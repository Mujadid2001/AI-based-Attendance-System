"""URLs for Camera Integration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExternalCameraViewSet

router = DefaultRouter()
router.register(r'sources', ExternalCameraViewSet, basename='camera-source')

urlpatterns = [
    path('', include(router.urls)),
]
