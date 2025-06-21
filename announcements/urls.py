from django.urls import path
from .views import (
    AnnouncementListView, AnnouncementDetailView, AnnouncementCreateView, AnnouncementUpdateView,
    ResidentAnnouncementListView, ReadAnnouncementView
)

urlpatterns = [
    # Admin routes
    path('', AnnouncementListView.as_view(), name='announcement_list'),
    path('<int:pk>/', AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('create/', AnnouncementCreateView.as_view(), name='announcement_create'),
    path('<int:pk>/update/', AnnouncementUpdateView.as_view(), name='announcement_update'),
    
    # Resident routes
    path('my-announcements/', ResidentAnnouncementListView.as_view(), name='resident_announcement_list'),
    path('<int:pk>/read/', ReadAnnouncementView.as_view(), name='read_announcement'),
]
