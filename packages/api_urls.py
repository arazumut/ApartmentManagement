from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import PackageViewSet

router = DefaultRouter()
router.register(r'', PackageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
