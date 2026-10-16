"""
Enterprise security API views for government-level features.
"""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import json

from .models import (
    SecurityAuditLog, TwoFactorAuth, SessionSecurity, 
    ComplianceFramework, SecurityIncident
)
from .services import (
    SecurityService, TwoFactorService, ComplianceService, 
    IncidentResponseService
)
from .serializers import (
    SecurityAuditLogSerializer, TwoFactorAuthSerializer,
    SessionSecuritySerializer, ComplianceFrameworkSerializer,
    SecurityIncidentSerializer
)
from utils.viewsets import ReadOnlyViewSet, BaseModelViewSet

User = get_user_model()


class SecurityAuditViewSet(ReadOnlyViewSet):
    """Security audit log management for administrators."""
    
    queryset = SecurityAuditLog.objects.all()
    serializer_class = SecurityAuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filter by risk level
        risk_level = self.request.query_params.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def security_dashboard(self, request):
        """Get security dashboard statistics."""
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Basic statistics
        stats = {
            'total_events_today': SecurityAuditLog.objects.filter(
                timestamp__date=today
            ).count(),
            'total_events_week': SecurityAuditLog.objects.filter(
                timestamp__gte=week_ago
            ).count(),
            'total_events_month': SecurityAuditLog.objects.filter(
                timestamp__gte=month_ago
            ).count(),
        }
        
        # Risk level breakdown for the last week
        risk_breakdown = SecurityAuditLog.objects.filter(
            timestamp__gte=week_ago
        ).values('risk_level').annotate(count=Count('id'))
        
        stats['risk_level_breakdown'] = {
            item['risk_level']: item['count'] for item in risk_breakdown
        }
        
        # Top IP addresses
        top_ips = SecurityAuditLog.objects.filter(
            timestamp__gte=week_ago
        ).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        stats['top_ip_addresses'] = list(top_ips)
        
        # Recent high-risk events
        high_risk_events = SecurityAuditLog.objects.filter(
            risk_level__in=['high', 'critical'],
            timestamp__gte=week_ago
        ).count()
        
        stats['high_risk_events'] = high_risk_events
        
        return Response(stats)


class TwoFactorAuthView(APIView):
    """Two-factor authentication management."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get 2FA status for current user."""
        try:
            two_fa = TwoFactorAuth.objects.get(user=request.user)
            serializer = TwoFactorAuthSerializer(two_fa)
            return Response(serializer.data)
        except (TwoFactorAuth.DoesNotExist, ValueError, TypeError):
            return Response({
                'is_enabled': False,
                'method': None,
                'phone_number': None
            })
    
    def post(self, request):
        """Setup 2FA for current user."""
        method = request.data.get('method', 'totp')
        
        if method == 'totp':
            result = TwoFactorService.setup_totp(request.user)
            
            SecurityService.log_security_event(
                request.user,
                'SYSTEM_CONFIG',
                '2FA TOTP setup initiated',
                'medium',
                request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'secret': result['secret'],
                'qr_code': result['qr_code'],
                'backup_codes': result['backup_codes']
            })
        
        elif method == 'sms':
            phone_number = request.data.get('phone_number')
            if not phone_number:
                return Response(
                    {'error': 'Phone number is required for SMS 2FA'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Setup SMS 2FA
            two_fa, created = TwoFactorAuth.objects.get_or_create(
                user=request.user,
                defaults={
                    'method': TwoFactorAuth.AuthMethod.SMS,
                    'phone_number': phone_number,
                    'backup_codes': SecurityService.generate_backup_codes()
                }
            )
            
            if not created:
                two_fa.method = TwoFactorAuth.AuthMethod.SMS
                two_fa.phone_number = phone_number
                two_fa.save()
            
            SecurityService.log_security_event(
                request.user,
                'SYSTEM_CONFIG',
                '2FA SMS setup initiated',
                'medium',
                request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'backup_codes': two_fa.backup_codes,
                'phone_number': phone_number
            })
        
        return Response(
            {'error': 'Invalid method'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def patch(self, request):
        """Enable/disable 2FA."""
        try:
            two_fa = TwoFactorAuth.objects.get(user=request.user)
        except (TwoFactorAuth.DoesNotExist, ValueError, TypeError):
            return Response(
                {'error': '2FA not set up'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')
        if action == 'enable':
            code = request.data.get('code')
            if not code:
                return Response(
                    {'error': 'Verification code required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify the code before enabling
            if two_fa.method == TwoFactorAuth.AuthMethod.TOTP:
                if TwoFactorService.verify_totp(request.user, code):
                    two_fa.is_enabled = True
                    two_fa.save()
                    
                    SecurityService.log_security_event(
                        request.user,
                        'SYSTEM_CONFIG',
                        '2FA enabled',
                        'medium',
                        request.META.get('REMOTE_ADDR')
                    )
                    
                    return Response({'message': '2FA enabled successfully'})
                else:
                    return Response(
                        {'error': 'Invalid verification code'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        elif action == 'disable':
            two_fa.is_enabled = False
            two_fa.save()
            
            SecurityService.log_security_event(
                request.user,
                'SYSTEM_CONFIG',
                '2FA disabled',
                'high',
                request.META.get('REMOTE_ADDR')
            )
            
            return Response({'message': '2FA disabled successfully'})
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )


class SessionSecurityViewSet(ReadOnlyViewSet):
    """Active session management."""
    
    queryset = SessionSecurity.objects.all()
    serializer_class = SessionSecuritySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own sessions, admins can see all
        if self.request.user.is_staff:
            return super().get_queryset()
        return SessionSecurity.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def terminate_session(self, request, pk=None):
        """Terminate a specific session."""
        session = self.get_object()
        
        # Users can only terminate their own sessions
        if not request.user.is_staff and session.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session.is_active = False
        session.save()
        
        SecurityService.log_security_event(
            request.user,
            'ADMIN_ACTION',
            f'Session terminated for user {session.user.email}',
            'medium',
            request.META.get('REMOTE_ADDR')
        )
        
        return Response({'message': 'Session terminated successfully'})


class ComplianceViewSet(ReadOnlyViewSet):
    """Compliance framework management."""
    
    queryset = ComplianceFramework.objects.all()
    serializer_class = ComplianceFrameworkSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['get'])
    def generate_report(self, request, pk=None):
        """Generate compliance report for a specific framework."""
        framework = self.get_object()
        
        if not framework.is_enabled:
            return Response(
                {'error': 'Framework is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report = ComplianceService.generate_compliance_report(
            framework.framework_type
        )
        
        if report:
            SecurityService.log_security_event(
                request.user,
                'REPORT_GENERATE',
                f'Compliance report generated for {framework.framework_type}',
                'low',
                request.META.get('REMOTE_ADDR')
            )
            
            return Response(report)
        
        return Response(
            {'error': 'Failed to generate report'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=False, methods=['get'])
    def active_frameworks(self, request):
        """Get all active compliance frameworks."""
        frameworks = ComplianceService.get_active_frameworks()
        serializer = ComplianceFrameworkSerializer(frameworks, many=True)
        return Response(serializer.data)


class SecurityIncidentViewSet(BaseModelViewSet):
    """Security incident management."""
    
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save(
            detected_by='manual',
            assigned_to=self.request.user
        )
        
        SecurityService.log_security_event(
            self.request.user,
            'ADMIN_ACTION',
            f'Security incident created: {serializer.validated_data["title"]}',
            'medium',
            self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign incident to a user."""
        incident = self.get_object()
        assignee_id = request.data.get('assignee_id')
        
        try:
            assignee = User.objects.get(id=assignee_id, is_staff=True)
            incident.assigned_to = assignee
            incident.status = SecurityIncident.Status.INVESTIGATING
            incident.save()
            
            SecurityService.log_security_event(
                request.user,
                'ADMIN_ACTION',
                f'Incident {incident.id} assigned to {assignee.email}',
                'low',
                request.META.get('REMOTE_ADDR')
            )
            
            return Response({'message': 'Incident assigned successfully'})
        
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {'error': 'Invalid assignee'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark incident as resolved."""
        incident = self.get_object()
        resolution_details = request.data.get('resolution_details', '')
        
        incident.status = SecurityIncident.Status.RESOLVED
        incident.resolution_details = resolution_details
        incident.resolved_at = timezone.now()
        incident.save()
        
        SecurityService.log_security_event(
            request.user,
            'ADMIN_ACTION',
            f'Incident {incident.id} resolved',
            'low',
            request.META.get('REMOTE_ADDR')
        )
        
        return Response({'message': 'Incident resolved successfully'})


class SystemHealthView(APIView):
    """System health and security status."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get system health status."""
        now = timezone.now()
        
        # Check for recent high-risk events
        high_risk_events = SecurityAuditLog.objects.filter(
            risk_level__in=['high', 'critical'],
            timestamp__gte=now - timedelta(hours=24)
        ).count()
        
        # Check for active incidents
        active_incidents = SecurityIncident.objects.filter(
            status__in=['open', 'investigating']
        ).count()
        
        # System resource metrics are a nice-to-have. psutil is not a hard
        # dependency, and a monitoring endpoint that throws a 500 because an
        # optional package is missing is worse than one that reports less.
        try:
            import psutil

            system_metrics = {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
            }
        except ImportError:
            system_metrics = {
                'available': False,
                'reason': 'psutil is not installed',
            }

        health_status = {
            'timestamp': now.isoformat(),
            'status': 'healthy',  # can be 'healthy', 'warning', 'critical'
            'security': {
                'high_risk_events_24h': high_risk_events,
                'active_incidents': active_incidents,
                'two_factor_enabled_users': TwoFactorAuth.objects.filter(
                    is_enabled=True
                ).count(),
            },
            'system': system_metrics,
            'compliance': {
                'active_frameworks': ComplianceFramework.objects.filter(
                    is_enabled=True
                ).count(),
            }
        }
        
        # Determine overall status
        if high_risk_events > 10 or active_incidents > 5:
            health_status['status'] = 'critical'
        elif high_risk_events > 5 or active_incidents > 2:
            health_status['status'] = 'warning'
        
        return Response(health_status)