from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Notification


@login_required
def notification_list(request):
    """View for listing user notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    # If notification has a link, redirect to it
    if notification.link:
        return redirect(notification.link)
    
    # Otherwise, redirect back to notifications list
    return redirect('notification_list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notification_list')


@login_required
def get_unread_count(request):
    """API endpoint to get unread notification count"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def get_recent_notifications(request):
    """API endpoint to get recent notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Serialize notifications to JSON
    data = []
    for notification in notifications:
        data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'is_read': notification.is_read,
            'link': notification.link,
            'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
        })
    
    return JsonResponse({'notifications': data})
