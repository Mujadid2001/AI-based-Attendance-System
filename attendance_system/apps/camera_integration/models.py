"""Models for Camera Integration - External Camera Support."""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid


class ExternalCameraSource(models.Model):
    """Model to manage external camera sources (e.g., mobile cameras)."""
    
    class CameraStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        DISCONNECTED = 'disconnected', _('Disconnected')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text=_("Name for this camera source"))
    device_id = models.CharField(max_length=255, unique=True, help_text=_("Unique device identifier"))
    device_type = models.CharField(
        max_length=50, 
        choices=[
            ('mobile', _('Mobile Device')),
            ('tablet', _('Tablet')),
            ('webcam', _('External Webcam')),
            ('ip_camera', _('IP Camera / Wireless Camera')),
            ('rtsp', _('RTSP Stream')),
            ('http_stream', _('HTTP/MJPEG Stream')),
            ('other', _('Other'))
        ],
        default='mobile'
    )
    
    # Wireless/IP Camera specific fields
    stream_url = models.URLField(
        max_length=512,
        blank=True,
        null=True,
        help_text=_("Stream URL for IP cameras (rtsp://, http://, etc.)")
    )
    stream_username = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Username for authenticated streams")
    )
    stream_password = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Password for authenticated streams")
    )
    stream_protocol = models.CharField(
        max_length=20,
        choices=[
            ('rtsp', 'RTSP'),
            ('http', 'HTTP/MJPEG'),
            ('https', 'HTTPS'),
            ('upload', 'Manual Upload')
        ],
        default='upload',
        help_text=_("Protocol used for streaming")
    )
    stream_quality = models.CharField(
        max_length=20,
        choices=[
            ('high', _('High Quality')),
            ('medium', _('Medium Quality')),
            ('low', _('Low Quality'))
        ],
        default='medium',
        help_text=_("Stream quality/resolution preference")
    )
    fps_limit = models.IntegerField(
        default=5,
        help_text=_("Frames per second limit for processing (1-30)")
    )
    
    # Security and authentication
    access_token = models.CharField(max_length=64, unique=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='camera_sources'
    )
    
    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=CameraStatus.choices,
        default=CameraStatus.INACTIVE
    )
    last_connected = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Settings
    is_enabled = models.BooleanField(default=True)
    auto_mark_attendance = models.BooleanField(
        default=False,
        help_text=_("Automatically mark attendance when face is recognized")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("External Camera Source")
        verbose_name_plural = _("External Camera Sources")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.device_type})"
    
    @staticmethod
    def generate_token():
        """Generate a secure random access token."""
        import secrets
        return secrets.token_urlsafe(48)
    
    def save(self, *args, **kwargs):
        if not self.access_token:
            self.access_token = self.generate_token()
        super().save(*args, **kwargs)


class CameraStreamSession(models.Model):
    """Track camera streaming sessions for analytics and security."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    camera_source = models.ForeignKey(
        ExternalCameraSource,
        on_delete=models.CASCADE,
        related_name='stream_sessions'
    )
    attendance_session = models.ForeignKey(
        'attendance.AttendanceSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='camera_sessions'
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    frames_received = models.IntegerField(default=0)
    faces_detected = models.IntegerField(default=0)
    faces_recognized = models.IntegerField(default=0)
    attendance_marked = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _("Camera Stream Session")
        verbose_name_plural = _("Camera Stream Sessions")
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Session {self.id} - {self.camera_source.name}"
