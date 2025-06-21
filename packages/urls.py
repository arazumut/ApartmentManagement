from django.urls import path
from .views import (
    PackageListView, PackageDetailView, PackageCreateView, PackageUpdateView,
    ResidentPackageListView, VisitorListView, VisitorCreateView, VisitorUpdateView
)

urlpatterns = [
    # Admin/Caretaker routes
    path('', PackageListView.as_view(), name='package_list'),
    path('<int:pk>/', PackageDetailView.as_view(), name='package_detail'),
    path('create/', PackageCreateView.as_view(), name='package_create'),
    path('<int:pk>/update/', PackageUpdateView.as_view(), name='package_update'),
    
    path('visitors/', VisitorListView.as_view(), name='visitor_list'),
    path('visitors/create/', VisitorCreateView.as_view(), name='visitor_create'),
    path('visitors/<int:pk>/update/', VisitorUpdateView.as_view(), name='visitor_update'),
    
    # Resident routes
    path('my-packages/', ResidentPackageListView.as_view(), name='resident_package_list'),
]
