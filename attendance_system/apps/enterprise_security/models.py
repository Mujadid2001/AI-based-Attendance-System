"""
Enterprise-level security models for government compliance.
"""
import uuid
import json
from datetime import timedelta
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from cryptography.fernet import Fernet
from django.conf import settings
import hashlib

User = get_user_model()


class SecurityAuditLog(models.Model):
    """Comprehensive audit logging for government compliance."""
    
    class ActionType(models.TextChoices):
        LOGIN = 'login', 'User Login'
        LOGOUT = 'logout', 'User Logout'
        LOGIN_FAILED = 'login_failed', 'Failed Login Attempt'
        PASSWORD_CHANGE = 'password_change', 'Password Changed'
        DATA_ACCESS = 'data_access', 'Data Access'
        DATA_MODIFY = 'data_modify', 'Data Modification'
        DATA_DELETE = 'data_delete', 'Data Deletion'
        SYSTEM_CONFIG = 'system_config', 'System Configuration Change'
        ATTENDANCE_MARK = 'attendance_mark', 'Attendance Marked'
        REPORT_GENERATE = 'report_generate', 'Report Generated'
        EXPORT_DATA = 'export_data', 'Data Exported'
        FACE_RECOGNITION = 'face_recognition', 'Face Recognition Event'
        SECURITY_VIOLATION = 'security_violation', 'Security Violation'
        ADMIN_ACTION = 'admin_action', 'Administrative Action'
    
    class RiskLevel(models.TextChoices):
        LOW = 'low', 'Low Risk'
        MEDIUM = 'medium', 'Medium Risk'
        HIGH = 'high', 'High Risk'
        CRITICAL = 'critical', 'Critical Risk'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Action details
    action_type = models.CharField(max_length=50, choices=ActionType.choices)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW)
    description = models.TextField()
    
    # Network information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    geolocation = models.JSONField(null=True, blank=True)
    
    # System information
    endpoint = models.CharField(max_length=255, blank=True)
    http_method = models.CharField(max_length=10, blank=True)
    response_code = models.IntegerField(null=True, blank=True)
    
    # Additional context
    metadata = models.JSONField(default=dict, blank=True)
    
    # Content type for tracking specific model changes
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        db_table = 'security_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action_type']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['risk_level', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action_type} by {self.user} at {self.timestamp}"


class DataEncryption(models.Model):
    """Model for managing encrypted sensitive data."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data_type = models.CharField(max_length=100)  # 'facial_data', 'personal_info', etc.
    encrypted_data = models.BinaryField()
    encryption_key_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Reference to the original object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        db_table = 'data_encryption'
        unique_together = ['content_type', 'object_id', 'data_type']


class TwoFactorAuth(models.Model):
    """Two-factor authentication for enhanced security."""
    
    class AuthMethod(models.TextChoices):
        SMS = 'sms', 'SMS Code'
        EMAIL = 'email', 'Email Code'
        TOTP = 'totp', 'Authenticator App'
        HARDWARE_TOKEN = 'hardware', 'Hardware Token'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    is_enabled = models.BooleanField(default=False)
    method = models.CharField(max_length=20, choices=AuthMethod.choices, default=AuthMethod.EMAIL)
    phone_number = models.CharField(max_length=20, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    secret_key = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'two_factor_auth'


class SessionSecurity(models.Model):
    """Enhanced session security tracking."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_fingerprint = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Risk assessment
    risk_score = models.IntegerField(default=0)  # 0-100
    is_suspicious = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'session_security'
        ordering = ['-created_at']


class ComplianceFramework(models.Model):
    """Government compliance framework configuration."""
    
    class Framework(models.TextChoices):
        GDPR = 'gdpr', 'General Data Protection Regulation'
        HIPAA = 'hipaa', 'Health Insurance Portability and Accountability Act'
        FERPA = 'ferpa', 'Family Educational Rights and Privacy Act'
        SOX = 'sox', 'Sarbanes-Oxley Act'
        ISO27001 = 'iso27001', 'ISO 27001'
        NIST = 'nist', 'NIST Cybersecurity Framework'
        LOCAL_GOV = 'local_gov', 'Local Government Requirements'
    
    framework_type = models.CharField(max_length=20, choices=Framework.choices, unique=True)
    is_enabled = models.BooleanField(default=False)
    configuration = models.JSONField(default=dict)
    requirements = models.JSONField(default=dict)
    last_audit = models.DateTimeField(null=True, blank=True)
    compliance_status = models.CharField(max_length=20, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_framework'


class SecurityIncident(models.Model):
    """Security incident tracking and response."""
    
    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'
    
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        INVESTIGATING = 'investigating', 'Under Investigation'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=Severity.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    
    # Affected user/system
    affected_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    affected_system = models.CharField(max_length=100, blank=True)
    
    # Detection and response
    detected_at = models.DateTimeField(auto_now_add=True)
    detected_by = models.CharField(max_length=100)  # 'system', 'user', 'admin'
    response_actions = models.JSONField(default=list, blank=True)
    
    # Investigation details
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_incidents'
    )
    investigation_notes = models.TextField(blank=True)
    resolution_details = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'security_incident'
        ordering = ['-detected_at']