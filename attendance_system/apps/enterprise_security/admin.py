"""
Django admin configuration for enterprise security.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SecurityAuditLog, TwoFactorAuth, SessionSecurity,
    ComplianceFramework, SecurityIncident, DataEncryption
)


@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for security audit logs."""
    
    list_display = [
        'timestamp', 'user', 'action_type', 'risk_level',
        'ip_address', 'response_code', 'colored_risk_level'
    ]
    list_filter = [
        'action_type', 'risk_level', 'timestamp', 'response_code'
    ]
    search_fields = [
        'user__email', 'description', 'ip_address', 'endpoint'
    ]
    readonly_fields = [
        'id', 'timestamp', 'user', 'session_id', 'action_type',
        'risk_level', 'description', 'ip_address', 'user_agent',
        'geolocation', 'endpoint', 'http_method', 'response_code',
        'metadata', 'content_type', 'object_id'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def colored_risk_level(self, obj):
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'critical': 'darkred'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.risk_level, 'black'),
            obj.get_risk_level_display()
        )
    colored_risk_level.short_description = 'Risk Level'
    
    def has_add_permission(self, request):
        return False  # Read-only
    
    def has_change_permission(self, request, obj=None):
        return False  # Read-only
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superuser can delete


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    """Admin interface for two-factor authentication."""
    
    list_display = [
        'user', 'is_enabled', 'method', 'phone_number',
        'created_at', 'backup_codes_count'
    ]
    list_filter = ['is_enabled', 'method', 'created_at']
    search_fields = ['user__email', 'phone_number']
    readonly_fields = ['secret_key', 'backup_codes', 'created_at']
    
    def backup_codes_count(self, obj):
        return len(obj.backup_codes)
    backup_codes_count.short_description = 'Backup Codes'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing
            return self.readonly_fields + ['user']
        return self.readonly_fields


@admin.register(SessionSecurity)
class SessionSecurityAdmin(admin.ModelAdmin):
    """Admin interface for session security."""
    
    list_display = [
        'user', 'ip_address', 'is_active', 'is_suspicious',
        'risk_score', 'created_at', 'last_activity'
    ]
    list_filter = [
        'is_active', 'is_suspicious', 'created_at', 'last_activity'
    ]
    search_fields = ['user__email', 'ip_address', 'session_key']
    readonly_fields = [
        'session_key', 'device_fingerprint', 'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ComplianceFramework)
class ComplianceFrameworkAdmin(admin.ModelAdmin):
    """Admin interface for compliance frameworks."""
    
    list_display = [
        'framework_type', 'is_enabled', 'compliance_status',
        'last_audit', 'updated_at'
    ]
    list_filter = ['framework_type', 'is_enabled', 'compliance_status']
    search_fields = ['framework_type']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('framework_type', 'is_enabled', 'compliance_status')
        }),
        ('Configuration', {
            'fields': ('configuration', 'requirements'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('last_audit', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    """Admin interface for security incidents."""
    
    list_display = [
        'title', 'severity', 'status', 'affected_user',
        'assigned_to', 'detected_at', 'colored_severity'
    ]
    list_filter = [
        'severity', 'status', 'detected_by', 'detected_at'
    ]
    search_fields = [
        'title', 'description', 'affected_user__email',
        'assigned_to__email'
    ]
    readonly_fields = [
        'id', 'detected_at', 'detected_by'
    ]
    date_hierarchy = 'detected_at'
    ordering = ['-detected_at']
    
    fieldsets = (
        ('Incident Details', {
            'fields': (
                'title', 'description', 'severity', 'status',
                'affected_user', 'affected_system'
            )
        }),
        ('Detection Information', {
            'fields': ('detected_at', 'detected_by', 'response_actions'),
            'classes': ('collapse',)
        }),
        ('Investigation', {
            'fields': (
                'assigned_to', 'investigation_notes',
                'resolution_details', 'resolved_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def colored_severity(self, obj):
        colors = {
            'low': 'green',
            'medium': 'orange', 
            'high': 'red',
            'critical': 'darkred'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.severity, 'black'),
            obj.get_severity_display()
        )
    colored_severity.short_description = 'Severity'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'affected_user', 'assigned_to'
        )
    
    actions = ['assign_to_me', 'mark_as_investigating', 'mark_as_resolved']
    
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user)
        self.message_user(
            request,
            f'{updated} incident(s) assigned to you.'
        )
    assign_to_me.short_description = "Assign selected incidents to me"
    
    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status='investigating')
        self.message_user(
            request,
            f'{updated} incident(s) marked as investigating.'
        )
    mark_as_investigating.short_description = "Mark as investigating"
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status='resolved',
            resolved_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} incident(s) marked as resolved.'
        )
    mark_as_resolved.short_description = "Mark as resolved"


@admin.register(DataEncryption)
class DataEncryptionAdmin(admin.ModelAdmin):
    """Admin interface for encrypted data (minimal exposure)."""
    
    list_display = [
        'data_type', 'encryption_key_id', 'content_type',
        'object_id', 'created_at'
    ]
    list_filter = ['data_type', 'created_at']
    search_fields = ['data_type', 'encryption_key_id']
    readonly_fields = [
        'id', 'encrypted_data', 'created_at', 'updated_at'
    ]
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser