"""
Authentication models using industry-standard practices.
"""
import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with role-based access control."""
    
    class Role(models.TextChoices):
        """User role choices."""
        ADMIN = 'admin', _('Administrator')
        TEACHER = 'teacher', _('Teacher')
        STUDENT = 'student', _('Student')
    
    # Remove username field
    username = None
    
    # Custom fields
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text=_('Email address must be unique')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Contact phone number')
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('User role in the system')
    )
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        help_text=_('User profile picture')
    )
    is_verified = models.BooleanField(
        default=False,
        help_text=_('Email verification status')
    )
    is_approved = models.BooleanField(
        default=True,
        help_text=_('Account approved by admin (for teachers)')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    
    # Set USERNAME_FIELD
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def is_admin(self):
        """Check if user is admin."""
        return self.role == self.Role.ADMIN or self.is_superuser
    
    def is_teacher(self):
        """Check if user is teacher."""
        return self.role == self.Role.TEACHER
    
    def is_student(self):
        """Check if user is student."""
        return self.role == self.Role.STUDENT
    
    def get_role_display_verbose(self):
        """Get verbose role display."""
        return dict(self.Role.choices).get(self.role, 'Unknown')


class LoginLog(models.Model):
    """Track user login activities for security auditing."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_logs'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Reason for failed login attempt')
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Login Log')
        verbose_name_plural = _('Login Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.user.email} - {status} - {self.timestamp}"


class EmailVerificationToken(models.Model):
    """Email verification tokens for user registration."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_('Unique verification token')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text=_('Token expiration time')
    )
    is_used = models.BooleanField(
        default=False,
        help_text=_('Whether the token has been used')
    )
    
    class Meta:
        verbose_name = _('Email Verification Token')
        verbose_name_plural = _('Email Verification Tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.token}"
    
    def save(self, *args, **kwargs):
        """Set expiration time on creation."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=48)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()


class PasswordResetToken(models.Model):
    """Password reset tokens for password recovery."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_('Unique password reset token')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text=_('Token expiration time')
    )
    is_used = models.BooleanField(
        default=False,
        help_text=_('Whether the token has been used')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address from which reset was requested')
    )
    user_agent = models.TextField(
        blank=True,
        help_text=_('User agent string from reset request')
    )
    
    class Meta:
        verbose_name = _('Password Reset Token')
        verbose_name_plural = _('Password Reset Tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Password Reset - {self.created_at}"
    
    def save(self, *args, **kwargs):
        """Set expiration time on creation."""
        if not self.expires_at:
            # Password reset tokens expire in 1 hour for security
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()
