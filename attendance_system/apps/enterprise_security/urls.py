"""
URL configuration for enterprise security.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SecurityAuditViewSet, TwoFactorAuthView, SessionSecurityViewSet,
    ComplianceViewSet, SecurityIncidentViewSet, SystemHealthView
)

# API router for viewsets
router = DefaultRouter()
router.register('audit-logs', SecurityAuditViewSet, basename='security-audit')
router.register('sessions', SessionSecurityViewSet, basename='session-security')
router.register('compliance', ComplianceViewSet, basename='compliance')
router.register('incidents', SecurityIncidentViewSet, basename='security-incidents')

app_name = 'enterprise_security'

urlpatterns = [
    # API endpoints
    path('api/security/', include(router.urls)),
    path('api/security/2fa/', TwoFactorAuthView.as_view(), name='two-factor-auth'),
    path('api/security/health/', SystemHealthView.as_view(), name='system-health'),
]