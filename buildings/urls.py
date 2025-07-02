from django.urls import path
from django.views.generic import TemplateView
from .views import BuildingCreateView, BuildingDetailView, get_apartments_by_building

urlpatterns = [
    # Geçici olarak basit bir view kullanıyoruz
    path('', TemplateView.as_view(template_name='buildings/building_list.html'), name='building_list'),
    path('apartments/', TemplateView.as_view(template_name='buildings/apartment_list.html'), name='apartment_list'),
    path('create/', BuildingCreateView.as_view(), name='building_create'),
    path('<int:pk>/', BuildingDetailView.as_view(), name='building_detail'),
    
    # API endpoints
    path('api/<int:building_id>/apartments/', get_apartments_by_building, name='api_building_apartments'),
]
