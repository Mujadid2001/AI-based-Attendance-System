"""
URLs for authentication endpoints.
"""
from django.urls import path, include
from django.middleware.csrf import get_token
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from apps.authentication.views import AuthenticationViewSet, UserManagementViewSet

router = DefaultRouter()
router.register(r'authentication', AuthenticationViewSet, basename='auth')
router.register(r'users', UserManagementViewSet, basename='user')

def get_csrf_token(request):
    """Get CSRF token for frontend."""
    return JsonResponse({'csrfToken': get_token(request)})

urlpatterns = [
    path('csrf-token/', get_csrf_token, name='csrf-token'),
    path('', include(router.urls)),
]
