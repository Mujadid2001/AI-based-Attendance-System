"""
URL configuration for attendance_system project.
Backend API only - Completely decoupled from frontend.
Any frontend can consume this API by configuring the base URL.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Customize Django Admin
admin.site.site_header = 'AI Attendance System Administration'
admin.site.site_title = 'AI Attendance Admin'
admin.site.index_title = 'Dashboard - Manage Your Attendance System'


def api_root(request):
    """API root endpoint providing information about available endpoints."""
    return JsonResponse({
        'message': 'AI-based Attendance System API',
        'version': '1.0.0',
        'endpoints': {
            'authentication': '/api/auth/',
            'students': '/api/students/',
            'attendance': '/api/attendance/',
            'ai': '/api/ai/',
            'token': '/api/token/',
            'admin': '/admin/',
        },
        'documentation': {
            'api_schema': '/api/schema/',
            'browsable_api': 'Available on all endpoints when authenticated',
        },
        'health': '/api/health/',
    })


def health_check(request):
    """Health check endpoint for monitoring."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'AI Attendance System API',
    })


urlpatterns = [
    # API Root
    path('api/', api_root, name='api_root'),
    path('api/health/', health_check, name='health_check'),
    
    # Admin Panel (internal use only)
    path('admin/', admin.site.urls),
    
    # JWT Token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API Endpoints (completely decoupled from frontend)
    path('api/auth/', include('apps.authentication.urls')),
    path('api/students/', include('apps.student.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/ai/', include('apps.ai_core.urls')),
]

# Serve media files in development (user uploads, face images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
