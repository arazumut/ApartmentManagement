from django.urls import path
from .views import HomeView, DashboardView, badges_api

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
