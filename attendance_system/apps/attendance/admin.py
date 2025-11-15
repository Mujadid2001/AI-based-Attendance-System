"""
Admin configuration for attendance models.
"""
from django.contrib import admin
from apps.attendance.models import AttendanceSession, Attendance, AttendanceReport


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceSession."""
    
    list_display = ('course', 'date', 'start_time', 'end_time', 'is_active',
                   'created_at')
    list_filter = ('is_active', 'date', 'course')
    search_fields = ('course__code', 'course__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'date')
        }),
        ('Session Time', {
            'fields': ('start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for Attendance."""
    
    list_display = ('student', 'session', 'status', 'check_in_time',
                   'check_in_method', 'created_at')
    list_filter = ('status', 'check_in_method', 'session__date',
                  'liveness_verified')
    search_fields = ('student__roll_number', 'student__user__email',
                    'session__course__code')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Session & Student', {
            'fields': ('session', 'student')
        }),
        ('Attendance Information', {
            'fields': ('status', 'check_in_time', 'check_in_method')
        }),
        ('Face Recognition Data', {
            'fields': ('confidence_score', 'liveness_verified'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('remarks', 'recorded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceReport."""
    
    list_display = ('student', 'course', 'start_date', 'end_date',
                   'total_sessions', 'present_count', 'attendance_percentage')
    list_filter = ('course', 'start_date', 'end_date')
    search_fields = ('student__roll_number', 'course__code')
    readonly_fields = ('generated_at', 'attendance_percentage')
    fieldsets = (
        ('Course & Student', {
            'fields': ('course', 'student')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Attendance Statistics', {
            'fields': ('total_sessions', 'present_count', 'late_count',
                      'absent_count', 'excused_count', 'attendance_percentage')
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
