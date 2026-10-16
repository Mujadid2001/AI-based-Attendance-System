"""
URLs for attendance management.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.attendance import views
from apps.attendance.views import (
    AttendanceSessionViewSet, AttendanceViewSet, AttendanceReportViewSet,
    mark_attendance_by_face, today_attendance, get_session_records
)

router = DefaultRouter()
router.register(r'sessions', AttendanceSessionViewSet, basename='session')
router.register(r'records', AttendanceViewSet, basename='attendance')
router.register(r'reports', AttendanceReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
    path('mark_by_face/', mark_attendance_by_face, name='mark_by_face'),
    path('today/', today_attendance, name='today_attendance'),
    path('session_records/<int:session_id>/', get_session_records, name='session_records'),
    path('active_session/', views.get_active_session, name='active_session'),
]
