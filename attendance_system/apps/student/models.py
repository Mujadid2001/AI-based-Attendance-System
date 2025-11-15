"""
Student management models.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
try:
    import numpy as np
except ImportError:
    np = None

User = get_user_model()


class Course(models.Model):
    """Course model."""
    
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text=_('Course code (e.g., CS101)')
    )
    name = models.CharField(
        max_length=200,
        help_text=_('Course name')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Course description')
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        related_name='courses_teaching',
        help_text=_('Course instructor')
    )
    max_students = models.PositiveIntegerField(
        default=50,
        help_text=_('Maximum number of students')
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Course active status')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def student_count(self):
        """Get number of enrolled students."""
        return self.enrollments.filter(is_active=True).count()
    
    def is_full(self):
        """Check if course is at capacity."""
        return self.student_count() >= self.max_students


class StudentProfile(models.Model):
    """Student profile with face embedding storage."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='student_profile',
        limit_choices_to={'role': 'student'}
    )
    roll_number = models.CharField(
        max_length=50,
        unique=True,
        help_text=_('Student roll number')
    )
    face_embedding = models.BinaryField(
        null=True,
        blank=True,
        help_text=_('Stored face embedding (numpy array as binary)')
    )
    face_encoding_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last time face encoding was updated')
    )
    is_face_registered = models.BooleanField(
        default=False,
        help_text=_('Whether student has registered face')
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Student department')
    )
    semester = models.PositiveIntegerField(
        default=1,
        help_text=_('Current semester')
    )
    registration_date = models.DateField(
        auto_now_add=True,
        help_text=_('Date of registration')
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Student active status')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Student Profile')
        verbose_name_plural = _('Student Profiles')
        ordering = ['roll_number']
        indexes = [
            models.Index(fields=['roll_number']),
            models.Index(fields=['is_face_registered']),
        ]
    
    def __str__(self):
        return f"{self.roll_number} - {self.user.get_full_name()}"
    
    def set_face_embedding(self, embedding):
        """Store face embedding safely."""
        if isinstance(embedding, np.ndarray):
            self.face_embedding = embedding.tobytes()
        else:
            self.face_embedding = embedding
    
    def get_face_embedding(self):
        """Retrieve face embedding."""
        if self.face_embedding:
            return np.frombuffer(self.face_embedding, dtype=np.float32)
        return None
    
    def has_face_registered(self):
        """Check if face is registered."""
        return self.is_face_registered and self.face_embedding is not None


class Enrollment(models.Model):
    """Student course enrollment."""
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text=_('Enrollment active status')
    )
    
    class Meta:
        verbose_name = _('Enrollment')
        verbose_name_plural = _('Enrollments')
        unique_together = ('student', 'course')
        indexes = [
            models.Index(fields=['student', 'course']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.course.code}"


class StudentFaceImage(models.Model):
    """Store face images for training dataset."""
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='face_images'
    )
    image = models.ImageField(
        upload_to='student_faces/%Y/%m/%d/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    is_verified = models.BooleanField(
        default=False,
        help_text=_('Whether image was verified as correct face')
    )
    is_training_data = models.BooleanField(
        default=True,
        help_text=_('Whether image is used in training dataset')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Student Face Image')
        verbose_name_plural = _('Student Face Images')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'is_training_data']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.created_at}"
