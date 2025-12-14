"""
Admin configuration for student models.
"""
from django.contrib import admin
from apps.student.models import (
    Course, StudentProfile, Enrollment, StudentFaceImage
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course model."""
    
    list_display = ('code', 'name', 'get_instructor_name', 'enrollment_stats',
                   'status_indicator', 'created_at')
    list_filter = ('is_active', 'created_at', 'instructor')
    search_fields = ('code', 'name', 'instructor__email', 'instructor__first_name',
                    'instructor__last_name')
    readonly_fields = ('created_at', 'updated_at', 'get_enrolled_students_list')
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['activate_courses', 'deactivate_courses']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Instructor', {
            'fields': ('instructor',)
        }),
        ('Enrollment', {
            'fields': ('max_students', 'get_enrolled_students_list')
        }),
        ('Configuration', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_instructor_name(self, obj):
        """Get instructor full name."""
        return obj.instructor.get_full_name() or obj.instructor.email
    get_instructor_name.short_description = 'Instructor'
    get_instructor_name.admin_order_field = 'instructor__first_name'
    
    def enrollment_stats(self, obj):
        """Display enrollment statistics."""
        enrolled = obj.student_count()
        max_students = obj.max_students
        percentage = (enrolled / max_students * 100) if max_students > 0 else 0
        return f'{enrolled}/{max_students} ({percentage:.0f}%)'
    enrollment_stats.short_description = 'Enrollment'
    
    def status_indicator(self, obj):
        """Display course status."""
        if obj.is_active:
            return '🟢 Active'
        return '🔴 Inactive'
    status_indicator.short_description = 'Status'
    
    def get_enrolled_students_list(self, obj):
        """Display list of enrolled students."""
        enrollments = obj.enrollments.filter(is_active=True).select_related('student')
        if enrollments:
            students = [f'{e.student.roll_number} - {e.student.user.get_full_name()}' 
                       for e in enrollments[:10]]
            result = '<br>'.join(students)
            if enrollments.count() > 10:
                result += f'<br>... and {enrollments.count() - 10} more'
            return result
        return 'No enrolled students'
    get_enrolled_students_list.short_description = 'Enrolled Students'
    get_enrolled_students_list.allow_tags = True
    
    def activate_courses(self, request, queryset):
        """Bulk activate courses."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} course(s) activated successfully.')
    activate_courses.short_description = 'Activate selected courses'
    
    def deactivate_courses(self, request, queryset):
        """Bulk deactivate courses."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} course(s) deactivated successfully.')
    deactivate_courses.short_description = 'Deactivate selected courses'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin interface for StudentProfile model."""
    
    list_display = ('roll_number', 'get_student_name', 'get_email', 'department', 
                   'semester', 'face_status', 'status_badge', 'registration_date')
    list_filter = ('is_active', 'is_face_registered', 'semester',
                  'department', 'registration_date')
    search_fields = ('roll_number', 'user__email', 'user__first_name',
                    'user__last_name', 'department')
    readonly_fields = ('created_at', 'updated_at', 'face_encoding_updated_at', 
                      'registration_date', 'get_enrolled_courses')
    list_per_page = 25
    date_hierarchy = 'registration_date'
    actions = ['activate_students', 'deactivate_students', 'reset_face_registration']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'get_enrolled_courses')
        }),
        ('Student Details', {
            'fields': ('roll_number', 'department', 'semester')
        }),
        ('Face Recognition', {
            'fields': ('is_face_registered', 'face_encoding_updated_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'registration_date'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_name(self, obj):
        """Get student full name."""
        return obj.user.get_full_name() or obj.user.email
    get_student_name.short_description = 'Student Name'
    get_student_name.admin_order_field = 'user__first_name'
    
    def get_email(self, obj):
        """Get student email."""
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def face_status(self, obj):
        """Display face registration status with icon."""
        if obj.is_face_registered:
            return '✅ Registered'
        return '❌ Not Registered'
    face_status.short_description = 'Face Status'
    
    def status_badge(self, obj):
        """Display active status with color."""
        if obj.is_active:
            return '🟢 Active'
        return '🔴 Inactive'
    status_badge.short_description = 'Status'
    
    def get_enrolled_courses(self, obj):
        """Display enrolled courses."""
        courses = obj.enrollments.filter(is_active=True)
        if courses:
            return ', '.join([e.course.code for e in courses])
        return 'No enrollments'
    get_enrolled_courses.short_description = 'Enrolled Courses'
    
    def activate_students(self, request, queryset):
        """Bulk activate students."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} student(s) activated successfully.')
    activate_students.short_description = 'Activate selected students'
    
    def deactivate_students(self, request, queryset):
        """Bulk deactivate students."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} student(s) deactivated successfully.')
    deactivate_students.short_description = 'Deactivate selected students'
    
    def reset_face_registration(self, request, queryset):
        """Reset face registration for students."""
        updated = queryset.update(is_face_registered=False)
        self.message_user(request, f'Face registration reset for {updated} student(s).')
    reset_face_registration.short_description = 'Reset face registration'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for Enrollment model."""
    
    list_display = ('get_student_info', 'get_course_info', 'status_badge', 'enrollment_date')
    list_filter = ('is_active', 'enrollment_date', 'course')
    search_fields = ('student__roll_number', 'course__code', 'course__name',
                    'student__user__email', 'student__user__first_name')
    readonly_fields = ('enrollment_date',)
    list_per_page = 30
    date_hierarchy = 'enrollment_date'
    actions = ['activate_enrollments', 'deactivate_enrollments']
    
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
    
    def status_badge(self, obj):
        """Display enrollment status."""
        if obj.is_active:
            return '🟢 Active'
        return '🔴 Inactive'
    status_badge.short_description = 'Status'
    
    def activate_enrollments(self, request, queryset):
        """Bulk activate enrollments."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} enrollment(s) activated successfully.')
    activate_enrollments.short_description = 'Activate selected enrollments'
    
    def deactivate_enrollments(self, request, queryset):
        """Bulk deactivate enrollments."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} enrollment(s) deactivated successfully.')
    deactivate_enrollments.short_description = 'Deactivate selected enrollments'


@admin.register(StudentFaceImage)
class StudentFaceImageAdmin(admin.ModelAdmin):
    """Admin interface for StudentFaceImage model."""
    
    list_display = ('student', 'is_verified', 'is_training_data',
                   'created_at')
    list_filter = ('is_verified', 'is_training_data', 'created_at')
    search_fields = ('student__roll_number', 'student__user__email')
    readonly_fields = ('created_at', 'image_preview')
    
    def image_preview(self, obj):
        """Display image preview in admin."""
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" height="100" />'
        return '-'
    image_preview.allow_tags = True
