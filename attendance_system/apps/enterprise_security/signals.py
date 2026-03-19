"""
Signal handlers for automated security monitoring.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from .models import SecurityAuditLog, SecurityIncident, SessionSecurity
from .services import SecurityService, IncidentResponseService

User = get_user_model()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login."""
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Assess login risk
    risk_score, risk_factors = SecurityService.assess_login_risk(
        user, ip_address, user_agent
    )
    
    # Determine risk level
    if risk_score >= 50:
        risk_level = SecurityAuditLog.RiskLevel.HIGH
    elif risk_score >= 30:
        risk_level = SecurityAuditLog.RiskLevel.MEDIUM
    else:
        risk_level = SecurityAuditLog.RiskLevel.LOW
    
    # Log the login
    SecurityAuditLog.objects.create(
        user=user,
        session_id=request.session.session_key,
        action_type=SecurityAuditLog.ActionType.LOGIN,
        risk_level=risk_level,
        description=f"User login successful. Risk factors: {', '.join(risk_factors) if risk_factors else 'None'}",
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={
            'risk_score': risk_score,
            'risk_factors': risk_factors
        }
    )
    
    # Create security incident for high-risk logins
    if risk_score >= 70:
        IncidentResponseService.create_incident(
            title=f"High-risk login detected for {user.email}",
            description=f"Login from {ip_address} has risk score {risk_score}. Risk factors: {', '.join(risk_factors)}",
            severity=SecurityIncident.Severity.MEDIUM,
            affected_user=user
        )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout."""
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', '')
    
    SecurityAuditLog.objects.create(
        user=user,
        session_id=request.session.session_key if hasattr(request, 'session') else None,
        action_type=SecurityAuditLog.ActionType.LOGOUT,
        risk_level=SecurityAuditLog.RiskLevel.LOW,
        description="User logout",
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Update session security
    if hasattr(request, 'session') and request.session.session_key:
        SessionSecurity.objects.filter(
            session_key=request.session.session_key
        ).update(is_active=False)


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts."""
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', '')
    email = credentials.get('email', 'unknown')
    
    # Check for brute force attempts
    cache_key = f"failed_login:{ip_address}"
    failed_count = cache.get(cache_key, 0) + 1
    cache.set(cache_key, failed_count, 3600)  # 1 hour
    
    risk_level = SecurityAuditLog.RiskLevel.MEDIUM
    if failed_count >= 5:
        risk_level = SecurityAuditLog.RiskLevel.HIGH
    
    SecurityAuditLog.objects.create(
        action_type=SecurityAuditLog.ActionType.LOGIN_FAILED,
        risk_level=risk_level,
        description=f"Failed login attempt for {email}. Attempt #{failed_count} from this IP",
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={
            'email': email,
            'failed_count': failed_count
        }
    )
    
    # Create incident for excessive failed attempts
    if failed_count >= 10:
        IncidentResponseService.create_incident(
            title=f"Brute force attack detected from {ip_address}",
            description=f"IP {ip_address} has made {failed_count} failed login attempts",
            severity=SecurityIncident.Severity.HIGH
        )


@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user creation and modification."""
    if created:
        SecurityAuditLog.objects.create(
            user=instance,
            action_type=SecurityAuditLog.ActionType.ADMIN_ACTION,
            risk_level=SecurityAuditLog.RiskLevel.LOW,
            description=f"New user account created: {instance.email}",
            ip_address='127.0.0.1',  # System action
            metadata={
                'role': instance.role,
                'is_active': instance.is_active
            }
        )
    else:
        # Log significant changes
        SecurityAuditLog.objects.create(
            user=instance,
            action_type=SecurityAuditLog.ActionType.DATA_MODIFY,
            risk_level=SecurityAuditLog.RiskLevel.LOW,
            description=f"User account modified: {instance.email}",
            ip_address='127.0.0.1',
            metadata={
                'role': instance.role,
                'is_active': instance.is_active
            }
        )


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """Log user deletion."""
    SecurityAuditLog.objects.create(
        action_type=SecurityAuditLog.ActionType.DATA_DELETE,
        risk_level=SecurityAuditLog.RiskLevel.HIGH,
        description=f"User account deleted: {instance.email}",
        ip_address='127.0.0.1',
        metadata={
            'deleted_user_id': str(instance.id),
            'deleted_user_email': instance.email,
            'deleted_user_role': instance.role
        }
    )


@receiver(pre_save, sender=User)
def detect_password_change(sender, instance, **kwargs):
    """Detect and log password changes."""
    if instance.pk:  # Only for existing users
        try:
            old_user = User.objects.get(pk=instance.pk)
            if old_user.password != instance.password:
                SecurityAuditLog.objects.create(
                    user=instance,
                    action_type=SecurityAuditLog.ActionType.PASSWORD_CHANGE,
                    risk_level=SecurityAuditLog.RiskLevel.MEDIUM,
                    description="Password changed",
                    ip_address='127.0.0.1',
                    metadata={
                        'change_type': 'password_update'
                    }
                )
        except User.DoesNotExist:
            pass


# Signal for attendance marking (connect to your attendance model)
def log_attendance_marking(sender, instance, created, **kwargs):
    """Log attendance marking events."""
    if created:
        SecurityAuditLog.objects.create(
            user=getattr(instance, 'student', None),
            action_type=SecurityAuditLog.ActionType.ATTENDANCE_MARK,
            risk_level=SecurityAuditLog.RiskLevel.LOW,
            description=f"Attendance marked for {getattr(instance, 'student', 'unknown')}",
            ip_address='127.0.0.1',
            metadata={
                'attendance_id': str(instance.id),
                'method': getattr(instance, 'marking_method', 'unknown'),
                'timestamp': str(getattr(instance, 'created_at', timezone.now()))
            }
        )


# Signal for face recognition events
def log_face_recognition_event(sender, **kwargs):
    """Log face recognition events."""
    user = kwargs.get('user')
    confidence = kwargs.get('confidence', 0)
    method = kwargs.get('method', 'unknown')
    
    risk_level = SecurityAuditLog.RiskLevel.LOW
    if confidence < 0.7:
        risk_level = SecurityAuditLog.RiskLevel.MEDIUM
    if confidence < 0.5:
        risk_level = SecurityAuditLog.RiskLevel.HIGH
    
    SecurityAuditLog.objects.create(
        user=user,
        action_type=SecurityAuditLog.ActionType.FACE_RECOGNITION,
        risk_level=risk_level,
        description=f"Face recognition event - confidence: {confidence}",
        ip_address='127.0.0.1',
        metadata={
            'confidence': confidence,
            'method': method,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    # Create incident for low confidence recognition
    if confidence < 0.4:
        IncidentResponseService.create_incident(
            title=f"Low confidence face recognition for {user.email if user else 'unknown'}",
            description=f"Face recognition confidence was {confidence}, which is below acceptable threshold",
            severity=SecurityIncident.Severity.LOW,
            affected_user=user
        )