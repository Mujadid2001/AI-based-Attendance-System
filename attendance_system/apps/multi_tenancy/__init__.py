"""
Multi-tenancy models for enterprise government deployment.
Allows multiple institutions to use the same system instance.
"""
import uuid
from django.db import models  
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Organization(models.Model):
    """
    Multi-tenant organization model for institutions.
    Each organization represents a government institution, school, 
    university, or department that uses the attendance system.
    """
    
    class OrganizationType(models.TextChoices):
        GOVERNMENT_OFFICE = 'gov_office', _('Government Office')
        SCHOOL = 'school', _('School')
        UNIVERSITY = 'university', _('University') 
        COLLEGE = 'college', _('College')
        DEPARTMENT = 'department', _('Department')
        MINISTRY = 'ministry', _('Ministry')
        AGENCY = 'agency', _('Government Agency')
    
    class SubscriptionTier(models.TextChoices):
        BASIC = 'basic', _('Basic (Up to 100 users)')
        STANDARD = 'standard', _('Standard (Up to 500 users)')
        PREMIUM = 'premium', _('Premium (Up to 2000 users)')
        ENTERPRISE = 'enterprise', _('Enterprise (Unlimited)')
        GOVERNMENT = 'government', _('Government (Custom)')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, help_text="Public display name")
    slug = models.SlugField(unique=True, max_length=100, 
                           help_text="URL-friendly organization identifier")
    
    # Organization details
    organization_type = models.CharField(
        max_length=20, 
        choices=OrganizationType.choices,
        default=OrganizationType.SCHOOL
    )
    description = models.TextField(blank=True)
    
    # Contact information
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100) 
    state_province = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Government registration details
    registration_number = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Government registration/license number"
    )
    tax_id = models.CharField(max_length=50, blank=True)
    
    # Subscription and licensing
    subscription_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.BASIC
    )
    license_key = models.CharField(max_length=255, unique=True)
    max_users = models.PositiveIntegerField(default=100)
    max_sessions = models.PositiveIntegerField(default=50)
    
    # Status and configuration
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False) 
    custom_domain = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logos/', blank=True)
    
    # Compliance settings
    data_retention_days = models.PositiveIntegerField(default=2555)  # 7 years
    require_2fa = models.BooleanField(default=False)
    allowed_ip_ranges = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Billing information
    billing_contact_name = models.CharField(max_length=255)
    billing_contact_email = models.EmailField()
    billing_contact_phone = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'subscription_tier']),
            models.Index(fields=['registration_number']),
        ]
    
    def __str__(self):
        return self.display_name
    
    @property
    def current_user_count(self):
        """Get current number of active users in this organization."""
        return self.users.filter(is_active=True).count()
    
    @property
    def is_subscription_active(self):
        """Check if subscription is currently active."""
        if not self.subscription_expires_at:
            return True
        from django.utils import timezone
        return timezone.now() <= self.subscription_expires_at
    
    @property
    def users_remaining(self):
        """Calculate remaining user slots."""
        return max(0, self.max_users - self.current_user_count)


class OrganizationMembership(models.Model):
    """
    Membership relationship between users and organizations.
    Supports multi-organization access for administrators.
    """
    
    class Role(models.TextChoices):
        OWNER = 'owner', _('Owner')
        ADMIN = 'admin', _('Administrator') 
        MANAGER = 'manager', _('Manager')
        TEACHER = 'teacher', _('Teacher')
        STAFF = 'staff', _('Staff')
        MEMBER = 'member', _('Member')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    
    # Permissions
    can_manage_users = models.BooleanField(default=False)
    can_manage_attendance = models.BooleanField(default=False) 
    can_view_reports = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Department/division within organization
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'organization_memberships'
        unique_together = ['user', 'organization']
        indexes = [
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"


class LicenseManagement(models.Model):
    """
    Software licensing management for commercial deployment.
    """
    
    class LicenseType(models.TextChoices):
        TRIAL = 'trial', _('Free Trial (30 days)')
        BASIC = 'basic', _('Basic License')
        STANDARD = 'standard', _('Standard License')
        PREMIUM = 'premium', _('Premium License')
        ENTERPRISE = 'enterprise', _('Enterprise License')
        GOVERNMENT = 'government', _('Government License')
        CUSTOM = 'custom', _('Custom License')
    
    class LicenseStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        EXPIRED = 'expired', _('Expired')
        SUSPENDED = 'suspended', _('Suspended')
        REVOKED = 'revoked', _('Revoked')
        PENDING = 'pending', _('Pending Activation')
    
    organization = models.OneToOneField(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='license'
    )
    
    # License details
    license_key = models.CharField(max_length=255, unique=True)
    license_type = models.CharField(max_length=20, choices=LicenseType.choices)
    status = models.CharField(max_length=20, choices=LicenseStatus.choices, default=LicenseStatus.PENDING)
    
    # Validity
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_validation = models.DateTimeField(auto_now=True)
    
    # Limitations
    max_users = models.PositiveIntegerField(default=100)
    max_concurrent_sessions = models.PositiveIntegerField(default=50)
    max_api_calls_per_day = models.PositiveIntegerField(default=10000)
    
    # Features enabled
    features_enabled = models.JSONField(default=dict, blank=True)
    modules_enabled = models.JSONField(default=list, blank=True)
    
    # Validation settings
    require_online_validation = models.BooleanField(default=True)
    validation_server_url = models.URLField(blank=True)
    hardware_fingerprint = models.CharField(max_length=255, blank=True)
    
    # Commercial details
    purchase_order_number = models.CharField(max_length=100, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    class Meta:
        db_table = 'license_management' 
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"{self.organization.name} - {self.license_type} ({self.status})"
    
    @property
    def is_valid(self):
        """Check if license is currently valid."""
        if self.status != self.LicenseStatus.ACTIVE:
            return False
        
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() <= self.expires_at
        
        return True
    
    @property
    def days_until_expiry(self):
        """Calculate days until license expires."""
        if not self.expires_at:
            return None
        
        from django.utils import timezone
        delta = self.expires_at - timezone.now()
        return delta.days if delta.days > 0 else 0


class SystemConfiguration(models.Model):
    """
    System-wide configuration for government deployment.
    """
    
    class ConfigType(models.TextChoices):
        SECURITY = 'security', _('Security Configuration')
        COMPLIANCE = 'compliance', _('Compliance Settings')
        LOCALIZATION = 'localization', _('Localization')
        INTEGRATION = 'integration', _('Integration Settings')
        BRANDING = 'branding', _('Branding & UI')
        NOTIFICATION = 'notification', _('Notification Settings')
    
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='configurations'
    )
    
    config_type = models.CharField(max_length=20, choices=ConfigType.choices)
    config_key = models.CharField(max_length=100)
    config_value = models.JSONField()
    
    # Metadata
    description = models.TextField(blank=True)
    is_encrypted = models.BooleanField(default=False)
    requires_restart = models.BooleanField(default=False)
    
    # Versioning
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_configurations'
        unique_together = ['organization', 'config_type', 'config_key']
        indexes = [
            models.Index(fields=['organization', 'config_type']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.config_type}:{self.config_key}"


class DeploymentEnvironment(models.Model):
    """
    Deployment environment management for different government installations.
    """
    
    class EnvironmentType(models.TextChoices):
        DEVELOPMENT = 'development', _('Development')
        STAGING = 'staging', _('Staging')
        PRODUCTION = 'production', _('Production')
        DR = 'disaster_recovery', _('Disaster Recovery')
    
    class DeploymentStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        MAINTENANCE = 'maintenance', _('Under Maintenance')
        INACTIVE = 'inactive', _('Inactive')
        FAILED = 'failed', _('Failed')
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='environments'
    )
    
    name = models.CharField(max_length=100)
    environment_type = models.CharField(max_length=20, choices=EnvironmentType.choices)
    status = models.CharField(max_length=20, choices=DeploymentStatus.choices, default=DeploymentStatus.ACTIVE)
    
    # Infrastructure details
    server_url = models.URLField()
    database_host = models.CharField(max_length=255)
    redis_host = models.CharField(max_length=255)
    
    # Version information
    application_version = models.CharField(max_length=50)
    database_version = models.CharField(max_length=50)
    last_deployment = models.DateTimeField(null=True, blank=True)
    
    # Monitoring
    health_check_url = models.URLField(blank=True)
    monitoring_enabled = models.BooleanField(default=True)
    
    # Backup configuration
    backup_enabled = models.BooleanField(default=True)
    backup_schedule = models.CharField(max_length=100, default='0 2 * * *')  # Daily at 2 AM
    backup_retention_days = models.PositiveIntegerField(default=90)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'deployment_environments'
        unique_together = ['organization', 'name']
    
    def __str__(self):
        return f"{self.organization.name} - {self.name} ({self.environment_type})"