from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_notifications_read'),
    path('api/unread-count/', views.get_unread_count, name='api_notification_unread_count'),
    path('api/recent/', views.get_recent_notifications, name='api_recent_notifications'),
] 