from django.urls import path, include
from .views import (
    AnnouncementListView, AnnouncementDetailView, AnnouncementCreateView, 
    AnnouncementUpdateView, ResidentAnnouncementListView, MarkAnnouncementReadView,
    AnnouncementLikeView, AnnouncementCommentView, AnnouncementShareView,
    AnnouncementFeedbackView, AnnouncementAnalyticsView, AnnouncementExportView,
    AnnouncementTemplateView, AnnouncementAPIView, announcement_quick_actions
)

urlpatterns = [
    # Admin routes
    path('', AnnouncementListView.as_view(), name='announcement_list'),
    path('<int:pk>/', AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('create/', AnnouncementCreateView.as_view(), name='announcement_create'),
    path('<int:pk>/update/', AnnouncementUpdateView.as_view(), name='announcement_update'),
    
    # Resident routes
    path('my-announcements/', ResidentAnnouncementListView.as_view(), name='resident_announcement_list'),
    path('<int:pk>/read/', MarkAnnouncementReadView.as_view(), name='mark_announcement_read'),
    
    # Interactive features
    path('<int:pk>/like/', AnnouncementLikeView.as_view(), name='announcement_like'),
    path('<int:pk>/comment/', AnnouncementCommentView.as_view(), name='announcement_comment'),
    path('<int:pk>/share/', AnnouncementShareView.as_view(), name='announcement_share'),
    path('<int:pk>/feedback/', AnnouncementFeedbackView.as_view(), name='announcement_feedback'),
    path('<int:pk>/quick-actions/', announcement_quick_actions, name='announcement_quick_actions'),
    
    # Analytics and reports
    path('analytics/', AnnouncementAnalyticsView.as_view(), name='announcement_analytics'),
    path('export/', AnnouncementExportView.as_view(), name='announcement_export'),
    
    # Templates
    path('template/<int:template_id>/', AnnouncementTemplateView.as_view(), name='announcement_template'),
    
    # API
    path('api/announcements/', AnnouncementAPIView.as_view(), name='api_announcements'),
]
