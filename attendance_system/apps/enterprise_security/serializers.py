"""
Serializers for enterprise security models.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SecurityAuditLog, TwoFactorAuth, SessionSecurity,
    ComplianceFramework, SecurityIncident, DataEncryption
)

User = get_user_model()


class SecurityAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for security audit logs."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = SecurityAuditLog
        fields = [
            'id', 'timestamp', 'user', 'user_email', 'session_id',
            'action_type', 'risk_level', 'description', 'ip_address',
            'user_agent', 'geolocation', 'endpoint', 'http_method',
            'response_code', 'metadata'
        ]
        read_only_fields = fields


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    """Serializer for two-factor authentication."""
    
    class Meta:
        model = TwoFactorAuth
        fields = [
            'is_enabled', 'method', 'phone_number', 'created_at'
        ]
        read_only_fields = ['created_at']


class SessionSecuritySerializer(serializers.ModelSerializer):
    """Serializer for session security information."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = SessionSecurity
        fields = [
            'user', 'user_email', 'session_key', 'ip_address',
            'user_agent', 'device_fingerprint', 'is_active',
            'created_at', 'last_activity', 'expires_at',
            'risk_score', 'is_suspicious'
        ]
        read_only_fields = fields


class ComplianceFrameworkSerializer(serializers.ModelSerializer):
    """Serializer for compliance frameworks."""
    
    class Meta:
        model = ComplianceFramework
        fields = [
            'framework_type', 'is_enabled', 'configuration',
            'requirements', 'last_audit', 'compliance_status',
            'created_at', 'updated_at'
        ]


class SecurityIncidentSerializer(serializers.ModelSerializer):
    """Serializer for security incidents."""
    
    affected_user_email = serializers.CharField(
        source='affected_user.email', 
        read_only=True
    )
    assigned_to_email = serializers.CharField(
        source='assigned_to.email', 
        read_only=True
    )
    
    class Meta:
        model = SecurityIncident
        fields = [
            'id', 'title', 'description', 'severity', 'status',
            'affected_user', 'affected_user_email', 'affected_system',
            'detected_at', 'detected_by', 'response_actions',
            'assigned_to', 'assigned_to_email', 'investigation_notes',
            'resolution_details', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'detected_at', 'affected_user_email', 'assigned_to_email'
        ]


class DataEncryptionSerializer(serializers.ModelSerializer):
    """Serializer for encrypted data (limited exposure)."""
    
    class Meta:
        model = DataEncryption
        fields = [
            'id', 'data_type', 'encryption_key_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields