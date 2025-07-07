from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import BuildingViewSet, ApartmentViewSet

router = DefaultRouter()
router.register(r'buildings', BuildingViewSet)
router.register(r'apartments', ApartmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
