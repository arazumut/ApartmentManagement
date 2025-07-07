from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# API URLs
urlpatterns = [
    # Authentication
    path('auth/register/', api_views.UserRegistrationView.as_view(), name='api_register'),
    path('auth/login/', api_views.UserLoginView.as_view(), name='api_login'),
    path('auth/logout/', api_views.UserLogoutView.as_view(), name='api_logout'),
    path('auth/change-password/', api_views.PasswordChangeView.as_view(), name='api_change_password'),
    
    # User management
    path('users/', api_views.UserListCreateView.as_view(), name='api_user_list'),
    path('users/<int:pk>/', api_views.UserDetailView.as_view(), name='api_user_detail'),
    path('users/me/', api_views.UserDetailView.as_view(), name='api_user_profile'),
    path('users/search/', api_views.search_users, name='api_search_users'),
    
    # Profile management
    path('profile/', api_views.UserProfileView.as_view(), name='api_user_profile_detail'),
    path('profile/upload-picture/', api_views.upload_profile_picture, name='api_upload_profile_picture'),
    path('profile/delete-picture/', api_views.delete_profile_picture, name='api_delete_profile_picture'),
    
    # Verification
    path('verify/phone/', api_views.verify_phone, name='api_verify_phone'),
    path('verify/email/', api_views.verify_email, name='api_verify_email'),
    
    # Activities and stats
    path('activities/', api_views.UserActivityListView.as_view(), name='api_user_activities'),
    path('stats/', api_views.user_stats, name='api_user_stats'),
    path('dashboard/', api_views.user_dashboard_data, name='api_user_dashboard'),
    path('permissions/', api_views.get_user_permissions, name='api_user_permissions'),
]
