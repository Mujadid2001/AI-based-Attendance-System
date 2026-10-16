"""
URLs for student management.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.student.views import (
    CourseViewSet, StudentProfileViewSet, EnrollmentViewSet
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'profiles', StudentProfileViewSet, basename='student-profile')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')

urlpatterns = [
    path('', include(router.urls)),
]
