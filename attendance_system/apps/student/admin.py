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
    
    list_display = ('code', 'name', 'instructor', 'max_students',
                   'student_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('code', 'name', 'instructor__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Course Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Instructor', {
            'fields': ('instructor',)
        }),
        ('Configuration', {
            'fields': ('max_students', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin interface for StudentProfile model."""
    
    list_display = ('roll_number', 'user', 'department', 'semester',
                   'is_face_registered', 'is_active', 'registration_date')
    list_filter = ('is_active', 'is_face_registered', 'semester',
                  'department', 'registration_date')
    search_fields = ('roll_number', 'user__email', 'user__first_name',
                    'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'face_encoding_updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Student Details', {
            'fields': ('roll_number', 'department', 'semester',
                      'registration_date')
        }),
        ('Face Recognition', {
            'fields': ('is_face_registered', 'face_encoding_updated_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for Enrollment model."""
    
    list_display = ('student', 'course', 'is_active', 'enrollment_date')
    list_filter = ('is_active', 'enrollment_date', 'course__code')
    search_fields = ('student__roll_number', 'course__code',
                    'student__user__email')
    readonly_fields = ('enrollment_date',)


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
