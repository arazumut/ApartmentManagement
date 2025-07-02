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
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from users.views import register
from django.views.generic import RedirectView

# Geçici olarak temel URL'leri etkinleştiriyoruz
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='core/home.html'), name='home'),
    path('dashboard/', TemplateView.as_view(template_name='core/dashboard.html'), name='dashboard'),
    path('profile/', TemplateView.as_view(template_name='users/profile.html'), name='profile'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),  # Add register view at top level
    path('building_list/', RedirectView.as_view(url='/buildings/', permanent=False), name='building_list'),  # Redirect for compatibility
    path('apartment_list/', RedirectView.as_view(url='/buildings/apartments/', permanent=False), name='apartment_list'),  # Redirect for compatibility
    path('dues_list/', RedirectView.as_view(url='/payments/dues/', permanent=False), name='dues_list'),  # Redirect for compatibility
    path('expense_list/', RedirectView.as_view(url='/payments/expenses/', permanent=False), name='expense_list'),  # Redirect for compatibility
    path('announcement_list/', RedirectView.as_view(url='/announcements/', permanent=False), name='announcement_list'),  # Redirect for compatibility
    path('complaint_list/', RedirectView.as_view(url='/complaints/', permanent=False), name='complaint_list'),  # Redirect for compatibility
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls')),  # Include users app URLs
    path('buildings/', include('buildings.urls')),  # Include buildings app URLs
    path('payments/', include('payments.urls')),  # Include payments app URLs
    path('announcements/', include('announcements.urls')),  # Include announcements app URLs
    path('complaints/', include('complaints.urls')),  # Include complaints app URLs
    path('', include('caretaker.urls')),  # Include caretaker app URLs without prefix
    path('', include('packages.urls')),  # Include packages app URLs without prefix
    path('notifications/', include('notifications.urls')),  # Include notifications app URLs
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
