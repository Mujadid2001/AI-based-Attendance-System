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
from django.shortcuts import render
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
        'endpoints': {
            'authentication': '/api/auth/',
            'students': '/api/students/',
            'attendance': '/api/attendance/',
            'ai': '/api/ai/',
            'camera': '/api/camera/',
            'security': '/api/security/',
            'token': '/api/token/',
            'admin': '/admin/',
        },
        'health': '/api/health/',
    })


def health_check(request):
    """Health check endpoint for monitoring.

    Tries the database too, so a load balancer or uptime check can tell the
    difference between "the process is up" and "the app actually works".
    """
    payload = {
        'status': 'healthy',
        'service': 'AI Attendance System API',
        'database': 'ok',
    }
    status_code = 200

    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception as exc:  # pragma: no cover - depends on live DB
        payload['status'] = 'degraded'
        payload['database'] = f'error: {exc.__class__.__name__}'
        status_code = 503

    return JsonResponse(payload, status=status_code)


def mobile_camera_view(request):
    """Serve the mobile camera HTML interface."""
    return render(request, 'camera.html')


urlpatterns = [
    # API Root
    path('api/', api_root, name='api_root'),
    path('api/health/', health_check, name='health_check'),
    
    # Mobile Camera Interface
    path('camera.html', mobile_camera_view, name='mobile_camera'),
    
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
    path('api/camera/', include('apps.camera_integration.urls')),
    
    # Enterprise Security APIs
    path('', include('apps.enterprise_security.urls')),
]

# Serve uploaded media and collected static files.
#
# In development this is always on. In production it is driven by
# SERVE_MEDIA_FILES / SERVE_STATIC_FILES in .env, because on PythonAnywhere
# the faster route is to map /media/ and /static/ in the Web tab instead.
# WhiteNoise still covers /static/ either way.
if settings.SERVE_MEDIA_FILES:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG and not settings.SERVE_STATIC_FILES:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

