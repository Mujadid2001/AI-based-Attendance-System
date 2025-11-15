"""
URL configuration for attendance_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Home
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('admin-dashboard/', TemplateView.as_view(template_name='admin_dashboard.html'), name='admin_dashboard'),
    path('teacher-dashboard/', TemplateView.as_view(template_name='teacher_dashboard.html'), name='teacher_dashboard'),
    path('student-dashboard/', TemplateView.as_view(template_name='student_dashboard.html'), name='student_dashboard'),
    
    # Face Recognition & Attendance
    path('face-registration/', TemplateView.as_view(template_name='face_registration.html'), name='face_registration'),
    path('attendance-marking/', TemplateView.as_view(template_name='attendance_marking.html'), name='attendance_marking'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API
    path('api/auth/', include('apps.authentication.urls')),
    path('api/students/', include('apps.student.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/ai/', include('apps.ai_core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
