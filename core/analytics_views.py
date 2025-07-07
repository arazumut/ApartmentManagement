from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

from buildings.models import Building, Apartment
from payments.models import Dues, ApartmentDues, Payment, Expense
from complaints.models import Complaint, ComplaintSurvey
from users.models import User, UserActivity
from notifications.models import Notification


@login_required
def analytics_dashboard(request):
    """Advanced analytics dashboard"""
    if not request.user.is_admin:
        return render(request, 'core/403.html')
    
    context = {
        'user': request.user,
        'page_title': 'Analytics Dashboard'
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def financial_analytics_api(request):
    """API for financial analytics data"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    buildings = Building.objects.filter(admin=request.user)
    period = request.GET.get('period', '12')  # months
    
    # Date range
    end_date = timezone.now()
    start_date = end_date - relativedelta(months=int(period))
    
    # Monthly revenue and expenses
    monthly_data = []
    for i in range(int(period)):
        month_start = end_date - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)
        
        revenue = Payment.objects.filter(
            apartment_dues__apartment__building__in=buildings,
            payment_date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses = Expense.objects.filter(
            building__in=buildings,
            expense_date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': float(revenue),
            'expenses': float(expenses),
            'profit': float(revenue - expenses)
        })
    
    # Collection rates
    collection_rates = []
    for building in buildings:
        total_due = ApartmentDues.objects.filter(
            apartment__building=building,
            due_date__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_paid = ApartmentDues.objects.filter(
            apartment__building=building,
            due_date__gte=start_date,
            status='paid'
        ).aggregate(total=Sum('paid_amount'))['total'] or 0
        
        rate = (total_paid / total_due * 100) if total_due > 0 else 0
        
        collection_rates.append({
            'building': building.name,
            'rate': round(rate, 2),
            'total_due': float(total_due),
            'total_paid': float(total_paid)
        })
    
    # Expense categories
    expense_categories = Expense.objects.filter(
        building__in=buildings,
        expense_date__gte=start_date
    ).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    return JsonResponse({
        'monthly_data': list(reversed(monthly_data)),
        'collection_rates': collection_rates,
        'expense_categories': list(expense_categories),
        'period': period
    })


@login_required
def resident_analytics_api(request):
    """API for resident analytics"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    buildings = Building.objects.filter(admin=request.user)
    
    # Occupancy rates
    occupancy_data = []
    for building in buildings:
        total_apartments = building.apartments.count()
        occupied_apartments = building.apartments.filter(is_occupied=True).count()
        rate = (occupied_apartments / total_apartments * 100) if total_apartments > 0 else 0
        
        occupancy_data.append({
            'building': building.name,
            'total': total_apartments,
            'occupied': occupied_apartments,
            'rate': round(rate, 2)
        })
    
    # Age distribution
    residents = User.objects.filter(
        role=User.RESIDENT,
        apartments__building__in=buildings
    ).distinct()
    
    age_groups = {'18-30': 0, '31-45': 0, '46-60': 0, '60+': 0, 'unknown': 0}
    for resident in residents:
        age = resident.get_age()
        if age is None:
            age_groups['unknown'] += 1
        elif age <= 30:
            age_groups['18-30'] += 1
        elif age <= 45:
            age_groups['31-45'] += 1
        elif age <= 60:
            age_groups['46-60'] += 1
        else:
            age_groups['60+'] += 1
    
    # Registration trends
    registration_data = []
    for i in range(12):
        month_start = timezone.now() - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)
        
        count = User.objects.filter(
            role=User.RESIDENT,
            date_joined__range=[month_start, month_end]
        ).count()
        
        registration_data.append({
            'month': month_start.strftime('%Y-%m'),
            'count': count
        })
    
    return JsonResponse({
        'occupancy_data': occupancy_data,
        'age_groups': age_groups,
        'registration_trends': list(reversed(registration_data))
    })


@login_required
def complaint_analytics_api(request):
    """API for complaint analytics"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    buildings = Building.objects.filter(admin=request.user)
    
    # Complaint status distribution
    status_data = Complaint.objects.filter(
        building__in=buildings
    ).values('status').annotate(count=Count('id'))
    
    # Category breakdown
    category_data = Complaint.objects.filter(
        building__in=buildings
    ).values('category').annotate(count=Count('id'))
    
    # Priority distribution
    priority_data = Complaint.objects.filter(
        building__in=buildings
    ).values('priority').annotate(count=Count('id'))
    
    # Resolution time analysis
    resolved_complaints = Complaint.objects.filter(
        building__in=buildings,
        status='resolved',
        resolved_at__isnull=False
    )
    
    resolution_times = []
    for complaint in resolved_complaints:
        days = (complaint.resolved_at.date() - complaint.created_at.date()).days
        resolution_times.append(days)
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    # Satisfaction scores
    satisfaction_data = ComplaintSurvey.objects.filter(
        complaint__building__in=buildings
    ).aggregate(
        avg_overall=Avg('overall_satisfaction'),
        avg_response_time=Avg('response_time_rating'),
        avg_solution_quality=Avg('solution_quality_rating')
    )
    
    # Monthly trends
    monthly_trends = []
    for i in range(12):
        month_start = timezone.now() - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)
        
        created = Complaint.objects.filter(
            building__in=buildings,
            created_at__range=[month_start, month_end]
        ).count()
        
        resolved = Complaint.objects.filter(
            building__in=buildings,
            resolved_at__range=[month_start, month_end]
        ).count()
        
        monthly_trends.append({
            'month': month_start.strftime('%Y-%m'),
            'created': created,
            'resolved': resolved
        })
    
    return JsonResponse({
        'status_distribution': list(status_data),
        'category_breakdown': list(category_data),
        'priority_distribution': list(priority_data),
        'avg_resolution_time': round(avg_resolution_time, 1),
        'satisfaction_scores': satisfaction_data,
        'monthly_trends': list(reversed(monthly_trends))
    })


@login_required
def user_activity_analytics_api(request):
    """API for user activity analytics"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Login patterns
    login_data = UserActivity.objects.filter(
        activity_type='login',
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).extra(
        select={'hour': 'EXTRACT(hour FROM timestamp)'}
    ).values('hour').annotate(count=Count('id'))
    
    # Most active users
    active_users = UserActivity.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).values('user__email', 'user__first_name', 'user__last_name').annotate(
        activity_count=Count('id')
    ).order_by('-activity_count')[:10]
    
    # Activity types
    activity_types = UserActivity.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).values('activity_type').annotate(count=Count('id'))
    
    # Device/browser analytics (if user_agent is captured)
    device_data = UserActivity.objects.filter(
        activity_type='login',
        timestamp__gte=timezone.now() - timedelta(days=30),
        user_agent__isnull=False
    ).values('user_agent').annotate(count=Count('id'))
    
    return JsonResponse({
        'login_patterns': list(login_data),
        'active_users': list(active_users),
        'activity_types': list(activity_types),
        'device_data': list(device_data)
    })


@login_required
def notification_analytics_api(request):
    """API for notification analytics"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Notification engagement
    total_notifications = Notification.objects.count()
    read_notifications = Notification.objects.filter(is_read=True).count()
    engagement_rate = (read_notifications / total_notifications * 100) if total_notifications > 0 else 0
    
    # Channel performance
    email_sent = Notification.objects.filter(is_email_sent=True).count()
    sms_sent = Notification.objects.filter(is_sms_sent=True).count()
    
    # Type distribution
    type_distribution = Notification.objects.values('notification_type').annotate(
        count=Count('id')
    )
    
    # Response times (time to read)
    response_times = []
    read_notifications_with_time = Notification.objects.filter(
        is_read=True,
        read_at__isnull=False
    )
    
    for notification in read_notifications_with_time:
        time_diff = (notification.read_at - notification.created_at).total_seconds() / 3600  # hours
        response_times.append(time_diff)
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    return JsonResponse({
        'engagement_rate': round(engagement_rate, 2),
        'total_notifications': total_notifications,
        'read_notifications': read_notifications,
        'email_sent': email_sent,
        'sms_sent': sms_sent,
        'type_distribution': list(type_distribution),
        'avg_response_time': round(avg_response_time, 2)
    })


@login_required
def export_analytics_data(request):
    """Export analytics data to CSV"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.csv"'
    
    writer = csv.writer(response)
    
    # Get data type from request
    data_type = request.GET.get('type', 'financial')
    
    if data_type == 'financial':
        writer.writerow(['Month', 'Revenue', 'Expenses', 'Profit'])
        # Add financial data rows
        
    elif data_type == 'complaints':
        writer.writerow(['Date', 'Title', 'Category', 'Status', 'Priority', 'Resolution Days'])
        # Add complaint data rows
        
    elif data_type == 'residents':
        writer.writerow(['Name', 'Email', 'Apartment', 'Join Date', 'Last Login'])
        # Add resident data rows
    
    return response


@login_required
def generate_analytics_report(request):
    """Generate comprehensive analytics report"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Generate PDF report
    from django.template.loader import get_template
    from django.http import HttpResponse
    from weasyprint import HTML, CSS
    
    template = get_template('analytics/report_template.html')
    context = {
        'user': request.user,
        'buildings': Building.objects.filter(admin=request.user),
        'report_date': timezone.now(),
        # Add all analytics data
    }
    
    html_string = template.render(context)
    html = HTML(string=html_string)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.pdf"'
    
    html.write_pdf(response)
    return response
