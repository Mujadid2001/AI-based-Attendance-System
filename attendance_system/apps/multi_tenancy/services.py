"""
Multi-tenancy and licensing services.
"""
import uuid
import secrets
import hashlib
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from .models import (
    Organization, OrganizationMembership, LicenseManagement,
    SystemConfiguration, DeploymentEnvironment
)

User = get_user_model()


class OrganizationService:
    """Service for managing organizations."""
    
    @staticmethod
    def create_organization(data, owner_user):
        """Create a new organization with initial setup."""
        with transaction.atomic():
            # Generate unique license key
            license_key = OrganizationService.generate_license_key()
            
            # Create organization
            organization = Organization.objects.create(
                name=data['name'],
                display_name=data.get('display_name', data['name']),
                slug=data['slug'],
                organization_type=data['organization_type'],
                email=data['email'],
                address=data['address'],
                city=data['city'],
                state_province=data['state_province'],
                country=data['country'],
                postal_code=data['postal_code'],
                registration_number=data['registration_number'],
                subscription_tier=data.get('subscription_tier', 'basic'),
                license_key=license_key,
                max_users=OrganizationService.get_max_users_for_tier(
                    data.get('subscription_tier', 'basic')
                ),
                billing_contact_name=data['billing_contact_name'],
                billing_contact_email=data['billing_contact_email'],
                billing_contact_phone=data['billing_contact_phone']
            )
            
            # Create owner membership
            OrganizationMembership.objects.create(
                user=owner_user,
                organization=organization,
                role=OrganizationMembership.Role.OWNER,
                can_manage_users=True,
                can_manage_attendance=True,
                can_view_reports=True,
                can_manage_settings=True
            )
            
            # Create license
            LicenseService.create_license(organization, data.get('license_type', 'trial'))
            
            # Create default configurations
            OrganizationService.create_default_configurations(organization, owner_user)
            
            return organization
    
    @staticmethod
    def generate_license_key():
        """Generate a unique license key."""
        return f"GAS-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def get_max_users_for_tier(tier):
        """Get maximum users allowed for subscription tier."""
        limits = {
            'basic': 100,
            'standard': 500,
            'premium': 2000,
            'enterprise': 10000,
            'government': 50000
        }
        return limits.get(tier, 100)
    
    @staticmethod
    def create_default_configurations(organization, user):
        """Create default system configurations for new organization."""
        default_configs = [
            {
                'config_type': 'security',
                'config_key': 'password_policy',
                'config_value': {
                    'min_length': 12,
                    'require_uppercase': True,
                    'require_lowercase': True,
                    'require_numbers': True,
                    'require_special_chars': True,
                    'max_age_days': 90
                }
            },
            {
                'config_type': 'security',
                'config_key': 'session_settings',
                'config_value': {
                    'timeout_minutes': 30,
                    'max_concurrent_sessions': 3,
                    'require_2fa': False
                }
            },
            {
                'config_type': 'compliance',
                'config_key': 'data_retention',
                'config_value': {
                    'retention_days': 2555,  # 7 years
                    'automatic_cleanup': True,
                    'backup_before_cleanup': True
                }
            },
            {
                'config_type': 'localization',
                'config_key': 'regional_settings',
                'config_value': {
                    'timezone': 'UTC',
                    'language': 'en',
                    'date_format': 'YYYY-MM-DD',
                    'currency': 'USD'
                }
            },
            {
                'config_type': 'branding',
                'config_key': 'appearance',
                'config_value': {
                    'primary_color': '#1976d2',
                    'secondary_color': '#424242',
                    'logo_url': '',
                    'favicon_url': ''
                }
            }
        ]
        
        for config in default_configs:
            SystemConfiguration.objects.create(
                organization=organization,
                created_by=user,
                **config
            )
    
    @staticmethod
    def check_user_limit(organization):
        """Check if organization has reached user limit."""
        current_users = organization.current_user_count
        return current_users < organization.max_users
    
    @staticmethod
    def get_organization_stats(organization):
        """Get statistics for an organization."""
        return {
            'total_users': organization.current_user_count,
            'max_users': organization.max_users,
            'users_remaining': organization.users_remaining,
            'active_sessions': OrganizationMembership.objects.filter(
                organization=organization,
                is_active=True
            ).count(),
            'subscription_status': 'active' if organization.is_subscription_active else 'expired',
            'license_valid': organization.license.is_valid if hasattr(organization, 'license') else False
        }


class LicenseService:
    """Service for managing software licenses."""
    
    @staticmethod
    def create_license(organization, license_type='trial'):
        """Create a license for an organization."""
        # Set expiry based on license type
        expires_at = None
        if license_type == 'trial':
            expires_at = timezone.now() + timedelta(days=30)
        elif license_type in ['basic', 'standard', 'premium']:
            expires_at = timezone.now() + timedelta(days=365)  # 1 year
        # Government and enterprise licenses might not have expiry
        
        # Set limitations based on license type
        max_users = OrganizationService.get_max_users_for_tier(
            organization.subscription_tier
        )
        
        license_features = LicenseService.get_features_for_type(license_type)
        
        # Generate hardware fingerprint
        hardware_fingerprint = LicenseService.generate_hardware_fingerprint()
        
        return LicenseManagement.objects.create(
            organization=organization,
            license_key=organization.license_key,
            license_type=license_type,
            status=LicenseManagement.LicenseStatus.ACTIVE,
            expires_at=expires_at,
            max_users=max_users,
            max_concurrent_sessions=max_users // 2,
            max_api_calls_per_day=max_users * 1000,
            features_enabled=license_features,
            modules_enabled=LicenseService.get_modules_for_type(license_type),
            hardware_fingerprint=hardware_fingerprint
        )
    
    @staticmethod
    def get_features_for_type(license_type):
        """Get enabled features for license type."""
        features = {
            'trial': {
                'facial_recognition': True,
                'basic_reporting': True,
                'email_notifications': False,
                'api_access': True,
                'multi_camera': False,
                'advanced_analytics': False,
                'white_label': False,
                'priority_support': False
            },
            'basic': {
                'facial_recognition': True,
                'basic_reporting': True,
                'email_notifications': True,
                'api_access': True,
                'multi_camera': True,
                'advanced_analytics': False,
                'white_label': False,  
                'priority_support': False
            },
            'standard': {
                'facial_recognition': True,
                'basic_reporting': True,
                'email_notifications': True,
                'api_access': True,
                'multi_camera': True,
                'advanced_analytics': True,
                'white_label': False,
                'priority_support': True
            },
            'premium': {
                'facial_recognition': True,
                'basic_reporting': True,
                'email_notifications': True,
                'api_access': True,
                'multi_camera': True,
                'advanced_analytics': True,
                'white_label': True,
                'priority_support': True
            },
            'enterprise': {
                'facial_recognition': True,
                'basic_reporting': True,
                'email_notifications': True,
                'api_access': True,
                'multi_camera': True,
                'advanced_analytics': True,
                'white_label': True,
                'priority_support': True,
                'custom_integrations': True,
                'on_premise_deployment': True
            },
            'government': {
                'facial_recognition': True,
                'basic_reporting': True,
                'email_notifications': True,
                'api_access': True,
                'multi_camera': True,
                'advanced_analytics': True,
                'white_label': True,
                'priority_support': True,
                'custom_integrations': True,
                'on_premise_deployment': True,
                'compliance_reporting': True,
                'audit_logging': True,
                'data_sovereignty': True
            }
        }
        return features.get(license_type, features['trial'])
    
    @staticmethod
    def get_modules_for_type(license_type):
        """Get enabled modules for license type."""
        all_modules = [
            'core_attendance',
            'facial_recognition', 
            'reporting',
            'user_management',
            'camera_integration'
        ]
        
        premium_modules = all_modules + [
            'advanced_analytics',
            'api_integration',
            'mobile_app'
        ]
        
        enterprise_modules = premium_modules + [
            'multi_tenancy',
            'custom_workflows',
            'third_party_integrations'
        ]
        
        government_modules = enterprise_modules + [
            'compliance_management',
            'audit_trails',
            'data_sovereignty',
            'security_enhanced'
        ]
        
        module_mapping = {
            'trial': all_modules,
            'basic': all_modules,
            'standard': all_modules + ['advanced_analytics'],
            'premium': premium_modules,
            'enterprise': enterprise_modules,
            'government': government_modules
        }
        
        return module_mapping.get(license_type, all_modules)
    
    @staticmethod
    def generate_hardware_fingerprint():
        """Generate hardware fingerprint for license validation."""
        import platform
        import socket
        
        # Gather system information
        system_info = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'hostname': socket.gethostname()
        }
        
        # Create fingerprint hash
        fingerprint_data = ''.join(str(v) for v in system_info.values())
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    @staticmethod
    def validate_license(organization):
        """Validate organization license."""
        try:
            license_obj = organization.license
            
            # Check if license exists and is active
            if not license_obj or license_obj.status != LicenseManagement.LicenseStatus.ACTIVE:
                return False, "License not active"
            
            # Check expiry
            if not license_obj.is_valid:
                return False, "License expired"
            
            # Check user limits
            if organization.current_user_count > license_obj.max_users:
                return False, "User limit exceeded"
            
            # Update last validation
            license_obj.last_validation = timezone.now()
            license_obj.save(update_fields=['last_validation'])
            
            return True, "License valid"
            
        except LicenseManagement.DoesNotExist:
            return False, "No license found"
    
    @staticmethod
    def check_feature_access(organization, feature_name):
        """Check if organization has access to a specific feature."""
        try:
            license_obj = organization.license
            if not license_obj or not license_obj.is_valid:
                return False
            
            return license_obj.features_enabled.get(feature_name, False)
        except LicenseManagement.DoesNotExist:
            return False


class TenantMiddleware:
    """Middleware to handle multi-tenant isolation."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract tenant from subdomain or header
        tenant = self.get_tenant(request)
        
        if tenant:
            request.tenant = tenant
            # Set cache prefix for tenant isolation
            cache_prefix = f"tenant_{tenant.slug}_"
            cache._cache.key_prefix = cache_prefix
        
        response = self.get_response(request)
        return response
    
    def get_tenant(self, request):
        """Extract tenant organization from request."""
        # Method 1: From subdomain
        host = request.get_host().split(':')[0]  # Remove port
        parts = host.split('.')
        
        if len(parts) > 2:  # Has subdomain
            subdomain = parts[0]
            try:
                return Organization.objects.get(
                    slug=subdomain,
                    is_active=True
                )
            except Organization.DoesNotExist:
                pass
        
        # Method 2: From custom header
        org_slug = request.META.get('HTTP_X_ORGANIZATION')
        if org_slug:
            try:
                return Organization.objects.get(
                    slug=org_slug,
                    is_active=True
                )
            except Organization.DoesNotExist:
                pass
        
        # Method 3: From user's primary organization (if authenticated)
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                membership = OrganizationMembership.objects.filter(
                    user=request.user,
                    is_active=True
                ).first()
                if membership:
                    return membership.organization
            except:
                pass
        
        return None


class ConfigurationService:
    """Service for managing system configurations."""
    
    @staticmethod
    def get_config(organization, config_type, config_key, default=None):
        """Get configuration value for organization."""
        try:
            config = SystemConfiguration.objects.get(
                organization=organization,
                config_type=config_type,
                config_key=config_key
            )
            return config.config_value
        except SystemConfiguration.DoesNotExist:
            return default
    
    @staticmethod
    def set_config(organization, config_type, config_key, config_value, user):
        """Set configuration value for organization."""
        config, created = SystemConfiguration.objects.update_or_create(
            organization=organization,
            config_type=config_type,
            config_key=config_key,
            defaults={
                'config_value': config_value,
                'created_by': user
            }
        )
        
        if not created:
            config.version += 1
            config.created_by = user
            config.save()
        
        return config
    
    @staticmethod
    def get_all_configs(organization, config_type=None):
        """Get all configurations for organization."""
        queryset = SystemConfiguration.objects.filter(
            organization=organization
        )
        
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        
        return {
            f"{config.config_type}:{config.config_key}": config.config_value
            for config in queryset
        }