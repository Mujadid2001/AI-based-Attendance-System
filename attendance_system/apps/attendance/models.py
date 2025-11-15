"""
Attendance tracking and management models.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from apps.student.models import StudentProfile, Course

User = get_user_model()


class AttendanceSession(models.Model):
    """Attendance session for a course on a specific date."""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )
    date = models.DateField(
        help_text=_('Date of attendance session')
    )
    start_time = models.TimeField(
        help_text=_('Session start time')
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text=_('Session end time')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sessions'
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether session is active')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Attendance Session')
        verbose_name_plural = _('Attendance Sessions')
        unique_together = ('course', 'date')
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['course', 'date']),
            models.Index(fields=['is_active', '-date']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.date} ({self.start_time})"
    
    def get_duration_minutes(self):
        """Calculate session duration in minutes."""
        if self.end_time:
            from datetime import datetime
            start = datetime.combine(timezone.now().date(), self.start_time)
            end = datetime.combine(timezone.now().date(), self.end_time)
            return int((end - start).total_seconds() / 60)
        return None


class Attendance(models.Model):
    """Attendance record for a student."""
    
    class Status(models.TextChoices):
        """Attendance status choices."""
        PRESENT = 'present', _('Present')
        ABSENT = 'absent', _('Absent')
        LATE = 'late', _('Late')
        EXCUSED = 'excused', _('Excused Absence')
    
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ABSENT,
        help_text=_('Attendance status')
    )
    check_in_time = models.TimeField(
        null=True,
        blank=True,
        help_text=_('Time student checked in')
    )
    check_in_method = models.CharField(
        max_length=50,
        choices=[
            ('face_recognition', _('Face Recognition')),
            ('manual', _('Manual Entry')),
            ('api', _('API')),
        ],
        default='face_recognition',
        help_text=_('Method of attendance recording')
    )
    remarks = models.TextField(
        blank=True,
        help_text=_('Additional remarks')
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Face recognition confidence score (0-1)')
    )
    liveness_verified = models.BooleanField(
        default=False,
        help_text=_('Whether liveness check passed')
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_attendances',
        help_text=_('User who manually recorded attendance')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Attendance')
        verbose_name_plural = _('Attendances')
        unique_together = ('session', 'student')
        ordering = ['-created_at', 'student__roll_number']
        indexes = [
            models.Index(fields=['session', 'student']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['student', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.session.date} - {self.get_status_display()}"
    
    def is_late(self):
        """Check if attendance is marked as late."""
        return self.status == self.Status.LATE
    
    def is_present(self):
        """Check if student is marked present."""
        return self.status in [self.Status.PRESENT, self.Status.LATE]


class AttendanceReport(models.Model):
    """Generated attendance reports for analytics."""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='attendance_reports'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendance_reports'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    total_sessions = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    excused_count = models.PositiveIntegerField(default=0)
    attendance_percentage = models.FloatField(default=0.0)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports'
    )
    
    class Meta:
        verbose_name = _('Attendance Report')
        verbose_name_plural = _('Attendance Reports')
        unique_together = ('course', 'student', 'start_date', 'end_date')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.course.code} ({self.start_date} to {self.end_date})"
    
    def calculate_percentage(self):
        """Calculate attendance percentage."""
        if self.total_sessions == 0:
            return 0.0
        return round(
            ((self.present_count + self.late_count) / self.total_sessions) * 100,
            2
        )
