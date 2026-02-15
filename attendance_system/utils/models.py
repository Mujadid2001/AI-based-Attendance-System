"""
Base models and mixins to reduce redundancy across the application.
"""
import uuid
from django.db import models
from django.utils import timezone


class TimestampMixin(models.Model):
    """
    Abstract base model that provides timestamp fields for created and updated times.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True
        # Common ordering by latest first
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-updated_at']),
        ]


class UUIDBased(models.Model):
    """
    Abstract base model that uses UUID as primary key.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )
    
    class Meta:
        abstract = True


class BaseModel(TimestampMixin, UUIDBased):
    """
    Base model combining timestamp and UUID functionality.
    Use this for models that need both features.
    """
    class Meta(TimestampMixin.Meta):
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin to add soft delete functionality.
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete the instance."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def restore(self):
        """Restore soft deleted instance."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class AuditMixin(models.Model):
    """
    Mixin to add audit trail functionality.
    """
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        db_index=True
    )
    updated_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        db_index=True
    )
    
    class Meta:
        abstract = True


class VersionedModel(models.Model):
    """
    Model with versioning support.
    """
    version = models.PositiveIntegerField(default=1, db_index=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Increment version on each save."""
        if self.pk:
            self.version += 1
        super().save(*args, **kwargs)


class StatusMixin(models.Model):
    """
    Mixin for models that need status tracking.
    """
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        PENDING = 'pending', 'Pending'
        ARCHIVED = 'archived', 'Archived'
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True
    )
    
    class Meta:
        abstract = True
    
    def activate(self):
        """Set status to active."""
        self.status = self.Status.ACTIVE
        self.save(update_fields=['status'])
    
    def deactivate(self):
        """Set status to inactive."""
        self.status = self.Status.INACTIVE
        self.save(update_fields=['status'])
    
    def archive(self):
        """Set status to archived."""
        self.status = self.Status.ARCHIVED
        self.save(update_fields=['status'])


# Manager for handling soft-deleted records
class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted records by default."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def with_deleted(self):
        """Include soft-deleted records."""
        return super().get_queryset()
    
    def deleted_only(self):
        """Return only soft-deleted records."""
        return super().get_queryset().filter(is_deleted=True)


# Manager for status-based filtering
class ActiveManager(models.Manager):
    """Manager that returns only active records."""
    
    def get_queryset(self):
        return super().get_queryset().filter(status=StatusMixin.Status.ACTIVE)