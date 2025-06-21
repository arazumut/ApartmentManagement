from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.utils import timezone

from buildings.models import Building, Apartment
from payments.models import Dues, ApartmentDues, Expense
from complaints.models import Complaint
from announcements.models import Announcement


class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings_count'] = Building.objects.count()
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Common stats for all user types
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        # Admin dashboard
        if user.is_admin:
            # Buildings managed by this admin
            admin_buildings = Building.objects.filter(admin=user)
            context['buildings'] = admin_buildings
            
            # Financial summary
            context['total_dues'] = Dues.objects.filter(
                building__in=admin_buildings,
                month=current_month,
                year=current_year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            context['total_expenses'] = Expense.objects.filter(
                building__in=admin_buildings,
                expense_date__month=current_month,
                expense_date__year=current_year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Complaints summary
            context['pending_complaints'] = Complaint.objects.filter(
                building__in=admin_buildings,
                status__in=[Complaint.NEW, Complaint.IN_PROGRESS]
            ).count()
            
            # Recent announcements
            context['recent_announcements'] = Announcement.objects.filter(
                building__in=admin_buildings
            ).order_by('-created_at')[:5]
            
        # Resident dashboard
        elif user.is_resident:
            # Apartments owned or rented by this resident
            resident_apartments = Apartment.objects.filter(
                Q(resident=user) | Q(owner=user)
            ).select_related('building')
            context['apartments'] = resident_apartments
            
            # Dues summary
            context['unpaid_dues'] = ApartmentDues.objects.filter(
                apartment__in=resident_apartments,
                status__in=[ApartmentDues.UNPAID, ApartmentDues.PARTIAL, ApartmentDues.OVERDUE]
            ).select_related('dues', 'apartment')
            
            # Complaints
            context['complaints'] = Complaint.objects.filter(
                apartment__in=resident_apartments
            ).order_by('-created_at')[:5]
            
            # Unread announcements
            context['unread_announcements'] = Announcement.objects.filter(
                building__in=[apt.building for apt in resident_apartments],
                is_active=True
            ).exclude(
                reads__user=user
            ).order_by('-created_at')[:5]
            
        # Caretaker dashboard
        elif user.is_caretaker:
            # Buildings where this person is the caretaker
            caretaker_buildings = Building.objects.filter(caretaker=user)
            context['buildings'] = caretaker_buildings
            
            # Tasks
            from caretaker.models import Task
            context['pending_tasks'] = Task.objects.filter(
                assigned_to=user,
                status__in=[Task.PENDING, Task.IN_PROGRESS]
            ).order_by('due_date')
            
            # Packages
            from packages.models import Package
            context['pending_packages'] = Package.objects.filter(
                building__in=caretaker_buildings,
                status=Package.PENDING
            ).count()
            
            # Complaints assigned to caretaker
            context['assigned_complaints'] = Complaint.objects.filter(
                assigned_to=user,
                status__in=[Complaint.NEW, Complaint.IN_PROGRESS]
            ).order_by('-created_at')[:5]
        
        return context


def handler404(request, exception):
    return render(request, 'core/404.html', status=404)


def handler500(request):
    return render(request, 'core/500.html', status=500)
