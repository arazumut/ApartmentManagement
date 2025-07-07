"""
URL configuration for apartment_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.views import LoginView, LogoutView

# Main URL patterns
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Home and dashboard
    path('', include('core.urls')),
    
    # Authentication
    path('accounts/', include('allauth.urls')),
    
    # App URLs
    path('users/', include('users.urls')),
    path('buildings/', include('buildings.urls')),
    path('payments/', include('payments.urls')),
    path('complaints/', include('complaints.urls')),
    path('announcements/', include('announcements.urls')),
    path('caretaker/', include('caretaker.urls')),
    path('packages/', include('packages.urls')),
    path('notifications/', include('notifications.urls')),
    
    # API URLs - All under /api/
    path('api/', include('apartment_project.api_urls')),
    
    # Legacy API endpoints (kept for backward compatibility)
    # These will be removed in future versions
    path('api/v1/users/', include('users.api_urls')),
    path('api/v1/buildings/', include('buildings.api_urls')),
    path('api/v1/payments/', include('payments.api_urls')),
    path('api/v1/complaints/', include('complaints.api_urls')),
    path('api/v1/announcements/', include('announcements.api_urls')),
    path('api/v1/notifications/', include('notifications.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
