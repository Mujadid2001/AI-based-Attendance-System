"""
Commercial licensing and business logic implementation.
This module handles the commercial aspects of the government-level system.
"""
import uuid
import secrets
import hashlib
from datetime import timedelta, datetime
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

User = get_user_model()


class CommercialLicense(models.Model):
    """
    Commercial licensing system for government institutions.
    Handles different pricing tiers and feature access control.
    """
    
    class LicenseModel(models.TextChoices):
        PER_USER = 'per_user', _('Per User/Month')
        PER_INSTITUTION = 'per_institution', _('Per Institution/Year')
        ENTERPRISE = 'enterprise', _('Enterprise Contract')
        GOVERNMENT = 'government', _('Government Contract')
        
    class PricingTier(models.TextChoices):
        STARTUP = 'startup', _('Startup (1-50 users) - $5/user/month')
        BUSINESS = 'business', _('Business (51-200 users) - $4/user/month')
        CORPORATE = 'corporate', _('Corporate (201-1000 users) - $3/user/month')
        ENTERPRISE = 'enterprise', _('Enterprise (1000+ users) - $2/user/month')
        GOVERNMENT = 'government', _('Government (Custom pricing)')
        
    class Region(models.TextChoices):
        NORTH_AMERICA = 'na', _('North America')
        EUROPE = 'eu', _('Europe') 
        ASIA_PACIFIC = 'apac', _('Asia Pacific')
        MIDDLE_EAST = 'me', _('Middle East')
        AFRICA = 'africa', _('Africa')
        LATIN_AMERICA = 'latam', _('Latin America')
    
    # Basic license information
    license_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_name = models.CharField(max_length=255)
    license_key = models.CharField(max_length=100, unique=True)
    
    # Commercial details
    license_model = models.CharField(max_length=20, choices=LicenseModel.choices)
    pricing_tier = models.CharField(max_length=20, choices=PricingTier.choices)
    region = models.CharField(max_length=10, choices=Region.choices)
    
    # Pricing and billing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    billing_cycle = models.CharField(max_length=20, default='monthly')
    
    # Usage limits
    max_users = models.PositiveIntegerField()
    max_institutions = models.PositiveIntegerField(default=1)
    max_api_calls_per_month = models.PositiveIntegerField(default=100000)
    storage_limit_gb = models.PositiveIntegerField(default=100)
    
    # License validity
    issued_date = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    
    # Features and modules
    enabled_features = models.JSONField(default=dict)
    enabled_modules = models.JSONField(default=list)
    
    # Support and SLA
    support_level = models.CharField(max_length=20, default='standard')
    sla_uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=99.9)
    
    # Legal and compliance
    contract_number = models.CharField(max_length=100, blank=True)
    po_number = models.CharField(max_length=100, blank=True)
    terms_version = models.CharField(max_length=20, default='1.0')
    gdpr_compliant = models.BooleanField(default=True)
    
    # Contact information
    primary_contact_name = models.CharField(max_length=255)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=20)
    billing_contact_email = models.EmailField()
    
    # Technical details
    deployment_type = models.CharField(max_length=20, default='cloud')  # cloud, on_premise, hybrid
    custom_domain = models.CharField(max_length=255, blank=True)
    white_label_enabled = models.BooleanField(default=False)
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commercial_licenses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['license_key']),
            models.Index(fields=['organization_name', 'is_active']),
            models.Index(fields=['valid_until', 'auto_renew']),
        ]
    
    def __str__(self):
        return f"{self.organization_name} - {self.pricing_tier} ({self.license_key})"
    
    @property
    def is_expired(self):
        """Check if license has expired."""
        return timezone.now() > self.valid_until
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry."""
        delta = self.valid_until - timezone.now()
        return max(0, delta.days)
    
    @property
    def monthly_cost(self):
        """Calculate monthly cost based on pricing model."""
        if self.license_model == self.LicenseModel.PER_USER:
            # Assume current usage for calculation
            return self.base_price * self.max_users
        elif self.license_model == self.LicenseModel.PER_INSTITUTION:
            return self.base_price / 12  # Annual to monthly
        return self.base_price


class SalesLead(models.Model):
    """
    Sales lead management for potential government customers.
    """
    
    class LeadSource(models.TextChoices):
        WEBSITE = 'website', _('Website Inquiry')
        REFERRAL = 'referral', _('Referral')
        COLD_OUTREACH = 'cold_outreach', _('Cold Outreach')
        CONFERENCE = 'conference', _('Conference/Event')
        PARTNER = 'partner', _('Partner Referral')
        GOVERNMENT_PORTAL = 'gov_portal', _('Government Procurement Portal')
        
    class LeadStatus(models.TextChoices):
        NEW = 'new', _('New Lead')
        CONTACTED = 'contacted', _('Initial Contact Made')
        QUALIFIED = 'qualified', _('Qualified Lead')
        PROPOSAL = 'proposal', _('Proposal Sent')
        NEGOTIATION = 'negotiation', _('In Negotiation')
        WON = 'won', _('Won - Customer')
        LOST = 'lost', _('Lost')
        
    class InstitutionType(models.TextChoices):
        FEDERAL_GOVERNMENT = 'federal_gov', _('Federal Government')
        STATE_GOVERNMENT = 'state_gov', _('State Government')
        LOCAL_GOVERNMENT = 'local_gov', _('Local Government')
        PUBLIC_SCHOOL = 'public_school', _('Public School')
        PUBLIC_UNIVERSITY = 'public_university', _('Public University')
        MILITARY = 'military', _('Military')
        HEALTHCARE = 'healthcare', _('Healthcare Institution')
        
    # Lead identification
    lead_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Organization details
    organization_name = models.CharField(max_length=255)
    institution_type = models.CharField(max_length=20, choices=InstitutionType.choices)
    country = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    # Contact information
    contact_name = models.CharField(max_length=255)
    contact_title = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    
    # Lead details
    lead_source = models.CharField(max_length=20, choices=LeadSource.choices)
    status = models.CharField(max_length=20, choices=LeadStatus.choices, default=LeadStatus.NEW)
    estimated_users = models.PositiveIntegerField(null=True, blank=True)
    estimated_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_close_date = models.DateField(null=True, blank=True)
    
    # Requirements
    requirements = models.TextField(blank=True)
    budget_range = models.CharField(max_length=100, blank=True)
    timeline = models.CharField(max_length=100, blank=True)
    decision_makers = models.TextField(blank=True)
    
    # Sales process
    assigned_sales_rep = models.CharField(max_length=255, blank=True)
    last_contact_date = models.DateField(null=True, blank=True)
    next_followup_date = models.DateField(null=True, blank=True)
    
    # Documentation
    proposal_sent = models.BooleanField(default=False)
    proposal_date = models.DateField(null=True, blank=True)
    contract_sent = models.BooleanField(default=False)
    contract_date = models.DateField(null=True, blank=True)
    
    # Notes and history
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sales_leads'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.organization_name} - {self.contact_name} ({self.status})"


class BillingAccount(models.Model):
    """
    Billing and invoice management for commercial customers.
    """
    
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'credit_card', _('Credit Card')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        WIRE_TRANSFER = 'wire_transfer', _('Wire Transfer')
        CHECK = 'check', _('Check')
        PURCHASE_ORDER = 'purchase_order', _('Purchase Order')
        
    class AccountStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        OVERDUE = 'overdue', _('Overdue')
        CLOSED = 'closed', _('Closed')
    
    # Account identification
    account_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.OneToOneField(CommercialLicense, on_delete=models.CASCADE, related_name='billing_account')
    
    # Billing details
    billing_name = models.CharField(max_length=255)
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)
    
    # Tax information
    tax_id = models.CharField(max_length=50, blank=True)
    vat_number = models.CharField(max_length=50, blank=True)
    tax_exempt = models.BooleanField(default=False)
    tax_exempt_certificate = models.FileField(upload_to='tax_certificates/', blank=True)
    
    # Payment information
    preferred_payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_terms = models.CharField(max_length=20, default='net_30')  # net_15, net_30, net_60
    
    # Account status
    status = models.CharField(max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Billing cycle
    billing_cycle_start = models.DateField()
    next_billing_date = models.DateField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_accounts'
    
    def __str__(self):
        return f"{self.billing_name} - {self.status}"


class Invoice(models.Model):
    """
    Invoice management system.
    """
    
    class InvoiceStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SENT = 'sent', _('Sent')
        PAID = 'paid', _('Paid')
        OVERDUE = 'overdue', _('Overdue')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded')
    
    # Invoice identification
    invoice_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=20, unique=True)
    billing_account = models.ForeignKey(BillingAccount, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice details
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment tracking
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    # File attachments
    invoice_pdf = models.FileField(upload_to='invoices/', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.total_amount}"
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        return (
            self.status == self.InvoiceStatus.SENT and
            timezone.now().date() > self.due_date
        )
    
    @property
    def balance_due(self):
        """Calculate remaining balance."""
        return self.total_amount - self.paid_amount


class InvoiceLineItem(models.Model):
    """
    Individual line items on invoices.
    """
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    
    # Item details
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Billing period
    service_start_date = models.DateField()
    service_end_date = models.DateField()
    
    # Metadata
    item_type = models.CharField(max_length=50)  # 'user_license', 'setup_fee', 'support', etc.
    
    class Meta:
        db_table = 'invoice_line_items'
    
    def save(self, *args, **kwargs):
        """Calculate total price on save."""
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class UsageTracking(models.Model):
    """
    Track usage metrics for billing purposes.
    """
    
    license = models.ForeignKey(CommercialLicense, on_delete=models.CASCADE, related_name='usage_records')
    
    # Usage metrics
    active_users = models.PositiveIntegerField()
    api_calls = models.PositiveIntegerField(default=0)
    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    face_recognitions = models.PositiveIntegerField(default=0)
    
    # Time period
    date = models.DateField()
    month_year = models.CharField(max_length=7)  # Format: YYYY-MM
    
    # Additional metrics
    attendance_records_created = models.PositiveIntegerField(default=0)
    reports_generated = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'usage_tracking'
        unique_together = ['license', 'date']
        indexes = [
            models.Index(fields=['license', 'month_year']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.license.organization_name} - {self.date} ({self.active_users} users)"


class PartnerProgram(models.Model):
    """
    Partner and reseller program management.
    """
    
    class PartnerType(models.TextChoices):
        RESELLER = 'reseller', _('Reseller Partner')
        INTEGRATOR = 'integrator', _('System Integrator')
        CONSULTANT = 'consultant', _('Consultant Partner')
        TECHNOLOGY = 'technology', _('Technology Partner')
        
    class PartnerTier(models.TextChoices):
        BRONZE = 'bronze', _('Bronze (5% commission)')
        SILVER = 'silver', _('Silver (10% commission)')
        GOLD = 'gold', _('Gold (15% commission)')
        PLATINUM = 'platinum', _('Platinum (20% commission)')
    
    # Partner identification
    partner_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    partner_type = models.CharField(max_length=20, choices=PartnerType.choices)
    partner_tier = models.CharField(max_length=20, choices=PartnerTier.choices, default=PartnerTier.BRONZE)
    
    # Contact information
    primary_contact_name = models.CharField(max_length=255)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=20)
    
    # Business details
    business_address = models.TextField()
    business_registration = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=50)
    
    # Partnership terms
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage
    territory = models.CharField(max_length=255, blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    
    # Performance metrics
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    commission_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    customers_referred = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    certification_level = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    partnership_start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'partner_program'
        
    def __str__(self):
        return f"{self.company_name} - {self.partner_tier}"