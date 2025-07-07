"""
API URL configuration for apartment_project.
All API endpoints are organized under /api/ prefix.
"""
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# API v1 URL patterns
api_v1_patterns = [
    # User management
    path('users/', include('users.api_urls')),
    
    # Building management
    path('', include('buildings.api_urls')),
    
    # Payment management
    path('payments/', include('payments.api_urls')),
    
    # Complaint management
    path('complaints/', include('complaints.api_urls')),
    
    # Announcement management
    path('announcements/', include('announcements.api_urls')),
    
    # Notification management
    path('notifications/', include('notifications.api_urls')),
    
    # Package management
    path('packages/', include('packages.api_urls')),
    
    # Caretaker management
    path('caretaker/', include('caretaker.api_urls')),
]

# Main API URL patterns
urlpatterns = [
    # API documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1 endpoints
    path('v1/', include(api_v1_patterns)),
    
    # REST Framework browsable API
    path('auth/', include('rest_framework.urls')),
]
