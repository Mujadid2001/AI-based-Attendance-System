"""
URLs for authentication endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.authentication.views import AuthenticationViewSet, UserManagementViewSet

router = DefaultRouter()
router.register(r'authentication', AuthenticationViewSet, basename='auth')
router.register(r'users', UserManagementViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
