"""Admin configuration for Camera Integration."""
from django.contrib import admin
from .models import ExternalCameraSource, CameraStreamSession


@admin.register(ExternalCameraSource)
class ExternalCameraSourceAdmin(admin.ModelAdmin):
    """Admin for External Camera Sources."""
    
    list_display = ['name', 'device_type', 'status', 'is_enabled', 'created_by', 'last_connected', 'created_at']
    list_filter = ['device_type', 'status', 'is_enabled', 'created_at']
    search_fields = ['name', 'device_id', 'created_by__username']
    readonly_fields = ['id', 'access_token', 'created_at', 'updated_at', 'last_connected']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'device_id', 'device_type')
        }),
        ('Security', {
            'fields': ('access_token', 'created_by')
        }),
        ('Status', {
            'fields': ('status', 'is_enabled', 'auto_mark_attendance', 'last_connected')
        }),
        ('Connection Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CameraStreamSession)
class CameraStreamSessionAdmin(admin.ModelAdmin):
    """Admin for Camera Stream Sessions."""
    
    list_display = ['id', 'camera_source', 'attendance_session', 'started_at', 'ended_at', 'frames_received', 'faces_recognized', 'attendance_marked']
    list_filter = ['started_at', 'ended_at']
    search_fields = ['camera_source__name', 'id']
    readonly_fields = ['id', 'started_at', 'ended_at']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('id', 'camera_source', 'attendance_session', 'started_at', 'ended_at')
        }),
        ('Statistics', {
            'fields': ('frames_received', 'faces_detected', 'faces_recognized', 'attendance_marked')
        }),
    )
