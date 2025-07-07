from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    AnnouncementViewSet, AnnouncementCategoryViewSet,
    AnnouncementTemplateViewSet, AnnouncementCommentViewSet,
    AnnouncementStatsAPIView
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet, basename='announcement')
router.register(r'categories', AnnouncementCategoryViewSet, basename='announcement-category')
router.register(r'templates', AnnouncementTemplateViewSet, basename='announcement-template')
router.register(r'comments', AnnouncementCommentViewSet, basename='announcement-comment')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Additional API endpoints
    path('stats/', AnnouncementStatsAPIView.as_view(), name='announcement-stats'),
]
