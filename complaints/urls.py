from django.urls import path
from .views import (
    ComplaintListView, ComplaintDetailView, ComplaintCreateView, ComplaintUpdateView,
    ResidentComplaintListView, CaretakerComplaintListView, AddCommentView
)

urlpatterns = [
    # Admin routes
    path('', ComplaintListView.as_view(), name='complaint_list'),
    path('<int:pk>/', ComplaintDetailView.as_view(), name='complaint_detail'),
    path('create/', ComplaintCreateView.as_view(), name='complaint_create'),
    path('<int:pk>/update/', ComplaintUpdateView.as_view(), name='complaint_update'),
    path('<int:pk>/comment/', AddCommentView.as_view(), name='add_complaint_comment'),
    
    # Resident routes
    path('my-complaints/', ResidentComplaintListView.as_view(), name='resident_complaint_list'),
    
    # Caretaker routes
    path('assigned/', CaretakerComplaintListView.as_view(), name='caretaker_complaint_list'),
]
