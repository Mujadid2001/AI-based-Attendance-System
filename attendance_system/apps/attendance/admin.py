"""
Admin configuration for attendance models.
"""
from django.contrib import admin
from apps.attendance.models import AttendanceSession, Attendance, AttendanceReport


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceSession."""
    
    list_display = ('get_course_info', 'date', 'time_range', 'attendance_stats',
                   'status_badge', 'get_creator')
    list_filter = ('is_active', 'date', 'course')
    search_fields = ('course__code', 'course__name', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at', 'get_attendance_summary')
    list_per_page = 25
    date_hierarchy = 'date'
    actions = ['activate_sessions', 'deactivate_sessions', 'close_sessions']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'date')
        }),
        ('Session Time', {
            'fields': ('start_time', 'end_time')
        }),
        ('Attendance Summary', {
            'fields': ('get_attendance_summary',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_course_info(self, obj):
        """Display course information."""
        return f'{obj.course.code} - {obj.course.name}'
    get_course_info.short_description = 'Course'
    get_course_info.admin_order_field = 'course__code'
    
    def time_range(self, obj):
        """Display session time range."""
        return f'{obj.start_time.strftime("%H:%M")} - {obj.end_time.strftime("%H:%M")}'
    time_range.short_description = 'Time'
    
    def attendance_stats(self, obj):
        """Display attendance statistics."""
        total = obj.attendances.count()
        present = obj.attendances.filter(status='present').count()
        if total > 0:
            percentage = (present / total * 100)
            return f'{present}/{total} ({percentage:.0f}%)'
        return '0/0 (0%)'
    attendance_stats.short_description = 'Attendance'
    
    def status_badge(self, obj):
        """Display session status."""
        if obj.is_active:
            return '🟢 Active'
        return '🔴 Closed'
    status_badge.short_description = 'Status'
    
    def get_creator(self, obj):
        """Display session creator."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return '-'
    get_creator.short_description = 'Created By'
    
    def get_attendance_summary(self, obj):
        """Display detailed attendance summary."""
        from django.utils.html import format_html
        attendances = obj.attendances.all()
        present = attendances.filter(status='present').count()
        late = attendances.filter(status='late').count()
        absent = attendances.filter(status='absent').count()
        excused = attendances.filter(status='excused').count()
        total = attendances.count()
        
        return format_html(
            '<strong>Total:</strong> {} | '
            '<span style="color:green;">Present: {}</span> | '
            '<span style="color:orange;">Late: {}</span> | '
            '<span style="color:red;">Absent: {}</span> | '
            '<span style="color:blue;">Excused: {}</span>',
            total, present, late, absent, excused
        )
    get_attendance_summary.short_description = 'Attendance Summary'
    
    def activate_sessions(self, request, queryset):
        """Bulk activate sessions."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} session(s) activated successfully.')
    activate_sessions.short_description = 'Activate selected sessions'
    
    def deactivate_sessions(self, request, queryset):
        """Bulk deactivate sessions."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} session(s) deactivated successfully.')
    deactivate_sessions.short_description = 'Deactivate selected sessions'
    
    def close_sessions(self, request, queryset):
        """Close sessions."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} session(s) closed successfully.')
    close_sessions.short_description = 'Close selected sessions'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for Attendance."""
    
    list_display = ('get_student_info', 'get_session_info', 'status_badge',
                   'check_in_time', 'method_badge', 'confidence_display', 'created_at')
    list_filter = ('status', 'check_in_method', 'session__date', 'session__course',
                  'liveness_verified')
    search_fields = ('student__roll_number', 'student__user__email',
                    'student__user__first_name', 'session__course__code')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 30
    date_hierarchy = 'created_at'
    actions = ['mark_as_present', 'mark_as_absent', 'mark_as_excused']
    
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
    
    def get_student_info(self, obj):
        """Display student information."""
        return f'{obj.student.roll_number} - {obj.student.user.get_full_name()}'
    get_student_info.short_description = 'Student'
    get_student_info.admin_order_field = 'student__roll_number'
    
    def get_session_info(self, obj):
        """Display session information."""
        return f'{obj.session.course.code} ({obj.session.date})'
    get_session_info.short_description = 'Session'
    get_session_info.admin_order_field = 'session__date'
    
    def status_badge(self, obj):
        """Display attendance status with color."""
        status_map = {
            'present': '🟢 Present',
            'late': '🟠 Late',
            'absent': '🔴 Absent',
            'excused': '🔵 Excused'
        }
        return status_map.get(obj.status, obj.status)
    status_badge.short_description = 'Status'
    
    def method_badge(self, obj):
        """Display check-in method."""
        method_map = {
            'face': '👤 Face Recognition',
            'manual': '✍️ Manual',
            'qr': '📱 QR Code'
        }
        return method_map.get(obj.check_in_method, obj.check_in_method)
    method_badge.short_description = 'Method'
    
    def confidence_display(self, obj):
        """Display confidence score."""
        if obj.confidence_score:
            score = obj.confidence_score * 100
            if score >= 90:
                return f'🟢 {score:.1f}%'
            elif score >= 70:
                return f'🟠 {score:.1f}%'
            else:
                return f'🔴 {score:.1f}%'
        return '-'
    confidence_display.short_description = 'Confidence'
    
    def mark_as_present(self, request, queryset):
        """Bulk mark as present."""
        updated = queryset.update(status='present')
        self.message_user(request, f'{updated} attendance(s) marked as present.')
    mark_as_present.short_description = 'Mark as Present'
    
    def mark_as_absent(self, request, queryset):
        """Bulk mark as absent."""
        updated = queryset.update(status='absent')
        self.message_user(request, f'{updated} attendance(s) marked as absent.')
    mark_as_absent.short_description = 'Mark as Absent'
    
    def mark_as_excused(self, request, queryset):
        """Bulk mark as excused."""
        updated = queryset.update(status='excused')
        self.message_user(request, f'{updated} attendance(s) marked as excused.')
    mark_as_excused.short_description = 'Mark as Excused'


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceReport."""
    
    list_display = ('get_student_info', 'get_course_info', 'date_range',
                   'attendance_summary', 'percentage_display', 'generated_at')
    list_filter = ('course', 'start_date', 'end_date')
    search_fields = ('student__roll_number', 'student__user__email',
                    'course__code', 'course__name')
    readonly_fields = ('generated_at', 'attendance_percentage', 'get_detailed_stats')
    list_per_page = 25
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Course & Student', {
            'fields': ('course', 'student')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Attendance Statistics', {
            'fields': ('get_detailed_stats', 'total_sessions', 'present_count', 
                      'late_count', 'absent_count', 'excused_count', 'attendance_percentage')
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_info(self, obj):
        """Display student information."""
        return f'{obj.student.roll_number} - {obj.student.user.get_full_name()}'
    get_student_info.short_description = 'Student'
    get_student_info.admin_order_field = 'student__roll_number'
    
    def get_course_info(self, obj):
        """Display course information."""
        return f'{obj.course.code} - {obj.course.name}'
    get_course_info.short_description = 'Course'
    get_course_info.admin_order_field = 'course__code'
    
    def date_range(self, obj):
        """Display date range."""
        return f'{obj.start_date} to {obj.end_date}'
    date_range.short_description = 'Period'
    
    def attendance_summary(self, obj):
        """Display attendance summary."""
        return f'P:{obj.present_count} L:{obj.late_count} A:{obj.absent_count} E:{obj.excused_count}'
    attendance_summary.short_description = 'Summary (P/L/A/E)'
    
    def percentage_display(self, obj):
        """Display attendance percentage with color."""
        percentage = obj.attendance_percentage
        if percentage >= 75:
            return f'🟢 {percentage:.1f}%'
        elif percentage >= 50:
            return f'🟠 {percentage:.1f}%'
        else:
            return f'🔴 {percentage:.1f}%'
    percentage_display.short_description = 'Attendance %'
    
    def get_detailed_stats(self, obj):
        """Display detailed statistics."""
        from django.utils.html import format_html
        return format_html(
            '<div style="padding:10px; background:#f0f0f0; border-radius:5px;">' 
            '<strong>Total Sessions:</strong> {} | '
            '<span style="color:green;">Present: {}</span> | '
            '<span style="color:orange;">Late: {}</span> | '
            '<span style="color:red;">Absent: {}</span> | '
            '<span style="color:blue;">Excused: {}</span> | '
            '<strong>Percentage: {:.1f}%</strong>'
            '</div>',
            obj.total_sessions, obj.present_count, obj.late_count,
            obj.absent_count, obj.excused_count, obj.attendance_percentage
        )
    get_detailed_stats.short_description = 'Detailed Statistics'
