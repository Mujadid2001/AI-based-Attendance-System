"""
URLs for AI operations.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ai_core.views import (
    FaceRegistrationViewSet, FaceRecognitionViewSet,
    AIConfigurationViewSet
)

router = DefaultRouter()
router.register(r'face-registration', FaceRegistrationViewSet, basename='face-registration')
router.register(r'face-recognition', FaceRecognitionViewSet, basename='face-recognition')
router.register(r'configuration', AIConfigurationViewSet, basename='configuration')

urlpatterns = [
    path('', include(router.urls)),
]
