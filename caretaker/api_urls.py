from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import TaskViewSet, ReportViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'reports', ReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
