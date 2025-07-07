from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt

from buildings.models import Building, Apartment
from payments.models import Dues, ApartmentDues, Expense, Payment
from complaints.models import Complaint
from announcements.models import Announcement
from notifications.models import Notification


class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings_count'] = Building.objects.count()
        context['apartments_count'] = Apartment.objects.count()
        context['residents_count'] = Apartment.objects.aggregate(
            total=Sum('occupant_count')
        )['total'] or 0
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Common stats for all user types
        current_month = timezone.now().month
        current_year = timezone.now().year
        last_month = (timezone.now() - timedelta(days=30)).month
        
        # Admin dashboard
        if user.is_admin:
            admin_buildings = Building.objects.filter(admin=user)
            context['buildings'] = admin_buildings
            
            # Enhanced Financial Summary
            current_dues = Dues.objects.filter(
                building__in=admin_buildings,
                month=current_month,
                year=current_year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            current_expenses = Expense.objects.filter(
                building__in=admin_buildings,
                expense_date__month=current_month,
                expense_date__year=current_year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Payment collection rate
            paid_dues = ApartmentDues.objects.filter(
                apartment__building__in=admin_buildings,
                dues__month=current_month,
                dues__year=current_year,
                status='paid'
            ).aggregate(total=Sum('paid_amount'))['total'] or 0
            
            collection_rate = (paid_dues / current_dues * 100) if current_dues > 0 else 0
            
            context.update({
                'total_dues': current_dues,
                'total_expenses': current_expenses,
                'paid_dues': paid_dues,
                'collection_rate': round(collection_rate, 1),
                'net_income': paid_dues - current_expenses,
            })
            
            # Overdue payments
            context['overdue_payments'] = ApartmentDues.objects.filter(
                apartment__building__in=admin_buildings,
                status='overdue'
            ).count()
            
            # Complaints summary with priority breakdown
            complaints_summary = Complaint.objects.filter(
                building__in=admin_buildings
            ).values('status', 'priority').annotate(count=Count('id'))
            
            context['complaints_summary'] = complaints_summary
            context['pending_complaints'] = Complaint.objects.filter(
                building__in=admin_buildings,
                status__in=[Complaint.NEW, Complaint.IN_PROGRESS]
            ).count()
            
            # Monthly trends
            context['monthly_trends'] = self.get_monthly_trends(admin_buildings)
            
            # Recent activities
            context['recent_activities'] = self.get_recent_activities(admin_buildings)
            
        # Enhanced Resident dashboard
        elif user.is_resident:
            resident_apartments = Apartment.objects.filter(
                Q(resident=user) | Q(owner=user)
            ).select_related('building')
            context['apartments'] = resident_apartments
            
            # Dues summary with totals
            unpaid_dues = ApartmentDues.objects.filter(
                apartment__in=resident_apartments,
                status__in=[ApartmentDues.UNPAID, ApartmentDues.PARTIAL, ApartmentDues.OVERDUE]
            ).select_related('dues', 'apartment')
            
            context['unpaid_dues'] = unpaid_dues
            context['total_unpaid_amount'] = unpaid_dues.aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            # Payment history
            context['recent_payments'] = Payment.objects.filter(
                apartment_dues__apartment__in=resident_apartments
            ).order_by('-payment_date')[:5]
            
            # Complaints with status tracking
            context['complaints'] = Complaint.objects.filter(
                apartment__in=resident_apartments
            ).order_by('-created_at')[:5]
            
            # Unread notifications
            context['unread_notifications'] = Notification.objects.filter(
                user=user,
                is_read=False
            ).count()
            
        # Enhanced Caretaker dashboard
        elif user.is_caretaker:
            caretaker_buildings = Building.objects.filter(caretaker=user)
            context['buildings'] = caretaker_buildings
            
            # Tasks with priority
            try:
                from caretaker.models import Task
                pending_tasks = Task.objects.filter(
                    assigned_to=user,
                    status__in=['pending', 'in_progress']
                ).order_by('-priority', '-created_at')
                
                context['pending_tasks'] = pending_tasks[:10]
                context['high_priority_tasks'] = pending_tasks.filter(priority='high').count()
            except ImportError:
                context['pending_tasks'] = []
                context['high_priority_tasks'] = 0
            
            # Complaints assigned to caretaker
            context['assigned_complaints'] = Complaint.objects.filter(
                building__in=caretaker_buildings,
                assigned_to=user,
                status__in=[Complaint.NEW, Complaint.IN_PROGRESS]
            ).count()
        
        return context
    
    def get_monthly_trends(self, buildings):
        """Get monthly trends for the last 6 months"""
        trends = []
        for i in range(6):
            month_date = timezone.now() - timedelta(days=30 * i)
            month = month_date.month
            year = month_date.year
            
            dues = Dues.objects.filter(
                building__in=buildings,
                month=month,
                year=year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            expenses = Expense.objects.filter(
                building__in=buildings,
                expense_date__month=month,
                expense_date__year=year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            trends.append({
                'month': month_date.strftime('%B'),
                'dues': float(dues),
                'expenses': float(expenses),
                'profit': float(dues - expenses)
            })
        
        return list(reversed(trends))
    
    def get_recent_activities(self, buildings):
        """Get recent activities for admin dashboard"""
        activities = []
        
        # Recent payments
        recent_payments = Payment.objects.filter(
            apartment_dues__apartment__building__in=buildings
        ).order_by('-payment_date')[:5]
        
        for payment in recent_payments:
            activities.append({
                'type': 'payment',
                'description': f"{payment.apartment_dues.apartment} ödeme yaptı",
                'amount': payment.amount,
                'date': payment.payment_date,
                'icon': 'fas fa-money-bill-wave',
                'color': 'success'
            })
        
        # Recent complaints
        recent_complaints = Complaint.objects.filter(
            building__in=buildings
        ).order_by('-created_at')[:5]
        
        for complaint in recent_complaints:
            activities.append({
                'type': 'complaint',
                'description': f"Yeni şikayet: {complaint.title}",
                'date': complaint.created_at,
                'icon': 'fas fa-exclamation-triangle',
                'color': 'warning'
            })
        
        # Sort by date
        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[:10]


class AdminAnalyticsView(LoginRequiredMixin, TemplateView):
    """Advanced analytics for administrators"""
    template_name = 'core/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_admin:
            return context
            
        admin_buildings = Building.objects.filter(admin=user)
        
        # Financial analytics
        context['financial_summary'] = self.get_financial_summary(admin_buildings)
        context['payment_trends'] = self.get_payment_trends(admin_buildings)
        context['expense_breakdown'] = self.get_expense_breakdown(admin_buildings)
        
        # Occupancy analytics
        context['occupancy_stats'] = self.get_occupancy_stats(admin_buildings)
        
        # Complaint analytics
        context['complaint_analytics'] = self.get_complaint_analytics(admin_buildings)
        
        return context
    
    def get_financial_summary(self, buildings):
        """Get comprehensive financial summary"""
        current_year = timezone.now().year
        
        # Annual totals
        annual_dues = Dues.objects.filter(
            building__in=buildings,
            year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        annual_expenses = Expense.objects.filter(
            building__in=buildings,
            expense_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Monthly averages
        monthly_avg_dues = annual_dues / 12 if annual_dues > 0 else 0
        monthly_avg_expenses = annual_expenses / 12 if annual_expenses > 0 else 0
        
        return {
            'annual_dues': annual_dues,
            'annual_expenses': annual_expenses,
            'annual_profit': annual_dues - annual_expenses,
            'monthly_avg_dues': monthly_avg_dues,
            'monthly_avg_expenses': monthly_avg_expenses,
            'profit_margin': ((annual_dues - annual_expenses) / annual_dues * 100) if annual_dues > 0 else 0
        }
    
    def get_payment_trends(self, buildings):
        """Get payment collection trends"""
        trends = []
        for i in range(12):
            month_date = timezone.now() - timedelta(days=30 * i)
            month = month_date.month
            year = month_date.year
            
            total_due = Dues.objects.filter(
                building__in=buildings,
                month=month,
                year=year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            total_paid = ApartmentDues.objects.filter(
                apartment__building__in=buildings,
                dues__month=month,
                dues__year=year,
                status='paid'
            ).aggregate(total=Sum('paid_amount'))['total'] or 0
            
            collection_rate = (total_paid / total_due * 100) if total_due > 0 else 0
            
            trends.append({
                'month': month_date.strftime('%B %Y'),
                'total_due': float(total_due),
                'total_paid': float(total_paid),
                'collection_rate': round(collection_rate, 1)
            })
        
        return list(reversed(trends))
    
    def get_expense_breakdown(self, buildings):
        """Get expense breakdown by category"""
        current_year = timezone.now().year
        
        expense_categories = Expense.objects.filter(
            building__in=buildings,
            expense_date__year=current_year
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return expense_categories
    
    def get_occupancy_stats(self, buildings):
        """Get occupancy statistics"""
        total_apartments = Apartment.objects.filter(building__in=buildings).count()
        occupied_apartments = Apartment.objects.filter(
            building__in=buildings,
            resident__isnull=False
        ).count()
        
        occupancy_rate = (occupied_apartments / total_apartments * 100) if total_apartments > 0 else 0
        
        return {
            'total_apartments': total_apartments,
            'occupied_apartments': occupied_apartments,
            'vacant_apartments': total_apartments - occupied_apartments,
            'occupancy_rate': round(occupancy_rate, 1)
        }
    
    def get_complaint_analytics(self, buildings):
        """Get complaint analytics"""
        total_complaints = Complaint.objects.filter(building__in=buildings).count()
        resolved_complaints = Complaint.objects.filter(
            building__in=buildings,
            status='resolved'
        ).count()
        
        avg_resolution_time = Complaint.objects.filter(
            building__in=buildings,
            status='resolved',
            resolved_at__isnull=False
        ).aggregate(
            avg_time=Avg('resolved_at') - Avg('created_at')
        )['avg_time']
        
        return {
            'total_complaints': total_complaints,
            'resolved_complaints': resolved_complaints,
            'pending_complaints': total_complaints - resolved_complaints,
            'resolution_rate': (resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0,
            'avg_resolution_time': avg_resolution_time
        }


# API Views for AJAX requests
class DashboardStatsAPIView(LoginRequiredMixin, TemplateView):
    """API endpoint for dashboard statistics"""
    
    def get(self, request, *args, **kwargs):
        user = request.user
        stats = {}
        
        if user.is_admin:
            buildings = Building.objects.filter(admin=user)
            current_month = timezone.now().month
            current_year = timezone.now().year
            
            stats = {
                'total_dues': float(Dues.objects.filter(
                    building__in=buildings,
                    month=current_month,
                    year=current_year
                ).aggregate(total=Sum('amount'))['total'] or 0),
                'pending_complaints': Complaint.objects.filter(
                    building__in=buildings,
                    status__in=[Complaint.NEW, Complaint.IN_PROGRESS]
                ).count(),
                'overdue_payments': ApartmentDues.objects.filter(
                    apartment__building__in=buildings,
                    status='overdue'
                ).count(),
            }
        
        return JsonResponse(stats)


@login_required
def badges_api(request):
    """API endpoint for badges/counts used in sidebar"""
    user = request.user
    
    # Initialize counts
    data = {
        'pending_complaints': 0,
        'unread_notifications': 0,
        'pending_payments': 0,
        'new_announcements': 0,
        'pending_packages': 0,
        'active_tasks': 0,
    }
    
    try:
        # Get unread notifications count
        data['unread_notifications'] = Notification.objects.filter(
            user=user, 
            is_read=False
        ).count()
        
        # Get pending complaints count based on user role
        if user.is_admin or user.is_caretaker:
            data['pending_complaints'] = Complaint.objects.filter(
                status__in=['open', 'in_progress']
            ).count()
        else:
            data['pending_complaints'] = Complaint.objects.filter(
                user=user,
                status__in=['open', 'in_progress']
            ).count()
        
        # Get new announcements count (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        data['new_announcements'] = Announcement.objects.filter(
            created_at__gte=week_ago,
            status='published'
        ).count()
        
        # Get pending packages count (for caretakers)
        if user.is_caretaker:
            from packages.models import Package
            data['pending_packages'] = Package.objects.filter(
                status='pending',
                building__caretaker=user
            ).count()
        
        # Get active tasks count (for caretakers)
        if user.is_caretaker:
            from caretaker.models import Task
            data['active_tasks'] = Task.objects.filter(
                assigned_to=user,
                status__in=['pending', 'in_progress']
            ).count()
        
        # Get pending payments count
        if user.is_resident:
            from payments.models import ApartmentDues
            data['pending_payments'] = ApartmentDues.objects.filter(
                apartment__resident=user,
                is_paid=False
            ).count()
        
    except Exception as e:
        # Log error but don't fail
        print(f"Error in badges_api: {e}")
    
    return JsonResponse(data)


def handler404(request, exception):
    """Custom 404 page"""
    return render(request, 'core/404.html', {
        'title': 'Sayfa Bulunamadı',
        'message': 'Aradığınız sayfa bulunamadı.'
    }, status=404)


def handler500(request):
    """Custom 500 page"""
    return render(request, 'core/500.html', {
        'title': 'Sunucu Hatası',
        'message': 'Bir sunucu hatası oluştu. Lütfen daha sonra tekrar deneyiniz.'
    }, status=500)
