from django.urls import path
from . import views

urlpatterns = [
    # Package management URLs
    path('packages/', views.package_list, name='package_list'),
    path('packages/resident/', views.resident_package_list, name='resident_package_list'),
    path('packages/create/', views.package_create, name='package_create'),
    path('packages/<int:pk>/', views.package_detail, name='package_detail'),
    path('packages/<int:pk>/update/', views.package_update, name='package_update'),
    path('packages/<int:pk>/deliver/', views.package_deliver, name='package_deliver'),
    
    # Visitor management URLs
    path('visitors/', views.visitor_list, name='visitor_list'),
    path('visitors/create/', views.visitor_create, name='visitor_create'),
    path('visitors/<int:pk>/update/', views.visitor_update, name='visitor_update'),
    path('visitors/<int:pk>/checkout/', views.visitor_checkout, name='visitor_checkout'),
]
