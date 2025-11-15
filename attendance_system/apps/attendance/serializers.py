"""
Attendance-related serializers.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.attendance.models import (
    AttendanceSession, Attendance, AttendanceReport
)


class AttendanceSessionSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceSession."""
    
    course_code = serializers.CharField(
        source='course.code',
        read_only=True
    )
    course_name = serializers.CharField(
        source='course.name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    duration_minutes = serializers.SerializerMethodField()
    attendance_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course', 'course_code', 'course_name', 'date',
            'start_time', 'end_time', 'duration_minutes', 'created_by',
            'created_by_name', 'attendance_count', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_duration_minutes(self, obj):
        return obj.get_duration_minutes()
    
    def get_attendance_count(self, obj):
        return obj.attendances.count()


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance records."""
    
    student_roll = serializers.CharField(
        source='student.roll_number',
        read_only=True
    )
    student_name = serializers.CharField(
        source='student.user.get_full_name',
        read_only=True
    )
    session_date = serializers.CharField(
        source='session.date',
        read_only=True
    )
    session_time = serializers.CharField(
        source='session.start_time',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    check_in_method_display = serializers.CharField(
        source='get_check_in_method_display',
        read_only=True
    )
    recorded_by_name = serializers.CharField(
        source='recorded_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'session', 'student', 'student_roll', 'student_name',
            'status', 'status_display', 'check_in_time', 'check_in_method',
            'check_in_method_display', 'confidence_score',
            'liveness_verified', 'remarks', 'recorded_by', 'recorded_by_name',
            'session_date', 'session_time', 'created_at'
        ]
        read_only_fields = ['created_at']


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating attendance records."""
    
    class Meta:
        model = Attendance
        fields = [
            'session', 'student', 'status', 'check_in_time',
            'check_in_method', 'confidence_score', 'liveness_verified',
            'remarks'
        ]
    
    def validate_confidence_score(self, value):
        """Validate confidence score is between 0 and 1."""
        if value is not None and not (0 <= value <= 1):
            raise serializers.ValidationError(
                _('Confidence score must be between 0 and 1.')
            )
        return value


class AttendanceReportSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceReport."""
    
    course_code = serializers.CharField(
        source='course.code',
        read_only=True
    )
    student_roll = serializers.CharField(
        source='student.roll_number',
        read_only=True
    )
    student_name = serializers.CharField(
        source='student.user.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = AttendanceReport
        fields = [
            'id', 'course', 'course_code', 'student', 'student_roll',
            'student_name', 'start_date', 'end_date', 'total_sessions',
            'present_count', 'late_count', 'absent_count', 'excused_count',
            'attendance_percentage', 'generated_at'
        ]
        read_only_fields = ['generated_at', 'attendance_percentage']


class DailyAttendanceSerializer(serializers.Serializer):
    """Serializer for daily attendance summary."""
    
    date = serializers.DateField()
    total_students = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()


class StudentAttendanceStatsSerializer(serializers.Serializer):
    """Serializer for student attendance statistics."""
    
    student_roll = serializers.CharField()
    student_name = serializers.CharField()
    course_code = serializers.CharField()
    total_classes = serializers.IntegerField()
    present = serializers.IntegerField()
    late = serializers.IntegerField()
    absent = serializers.IntegerField()
    excused = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
