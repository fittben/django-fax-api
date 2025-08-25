from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import uuid
from datetime import datetime


class Tenant(models.Model):
    """Multi-tenant support for enterprise deployments"""
    name = models.CharField(max_length=255, unique=True)
    company_name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, unique=True, help_text="e.g., company.efax.local")
    
    # Contact Information
    admin_email = models.EmailField()
    admin_phone = models.CharField(max_length=20)
    billing_email = models.EmailField()
    
    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default='US')
    
    # Settings
    max_users = models.IntegerField(default=10)
    max_dids = models.IntegerField(default=5)
    max_pages_per_month = models.IntegerField(default=1000)
    
    # Branding
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    secondary_color = models.CharField(max_length=7, default='#6c757d', help_text='Hex color code')
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_tenant'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.company_name}"


class DID(models.Model):
    """Direct Inward Dialing numbers"""
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number format: '+999999999'")
    
    number = models.CharField(validators=[phone_regex], max_length=20, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='dids')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_dids')
    assigned_at = models.DateTimeField(null=True, blank=True)
    
    # Provider Information
    PROVIDER_CHOICES = [
        ('telnyx', 'Telnyx'),
        ('twilio', 'Twilio'),
        ('vitelity', 'Vitelity'),
        ('internal', 'Internal'),
    ]
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='telnyx')
    provider_sid = models.CharField(max_length=100, blank=True, help_text='Provider-specific ID')
    
    # Configuration
    description = models.CharField(max_length=255, blank=True)
    is_fax_enabled = models.BooleanField(default=True)
    is_voice_enabled = models.BooleanField(default=False)
    is_sms_enabled = models.BooleanField(default=False)
    
    # Routing
    route_to_email = models.EmailField(blank=True, help_text='Forward faxes to this email')
    route_to_extension = models.CharField(max_length=10, blank=True, help_text='Forward calls to extension')
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_did'
        verbose_name = 'DID Number'
        verbose_name_plural = 'DID Numbers'
        ordering = ['number']
    
    def __str__(self):
        return f"{self.number} ({self.get_provider_display()})"


class CoverPage(models.Model):
    """Fax cover page templates"""
    name = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='cover_pages')
    
    # Template Design
    TEMPLATE_CHOICES = [
        ('professional', 'Professional'),
        ('simple', 'Simple'),
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('custom', 'Custom HTML'),
    ]
    template_type = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='professional')
    
    # Header
    header_text = models.CharField(max_length=255, default='FAX TRANSMISSION')
    show_logo = models.BooleanField(default=True)
    logo_position = models.CharField(max_length=10, choices=[('left', 'Left'), ('center', 'Center'), ('right', 'Right')], default='left')
    
    # Content Fields
    show_date = models.BooleanField(default=True)
    show_time = models.BooleanField(default=True)
    show_from = models.BooleanField(default=True)
    show_to = models.BooleanField(default=True)
    show_pages = models.BooleanField(default=True)
    show_subject = models.BooleanField(default=True)
    show_message = models.BooleanField(default=True)
    
    # Custom Fields
    custom_field_1_label = models.CharField(max_length=50, blank=True)
    custom_field_2_label = models.CharField(max_length=50, blank=True)
    custom_field_3_label = models.CharField(max_length=50, blank=True)
    
    # Footer
    footer_text = models.TextField(blank=True, default='This transmission is confidential and intended solely for the addressee.')
    
    # Styling
    font_family = models.CharField(max_length=50, default='Arial, sans-serif')
    primary_color = models.CharField(max_length=7, default='#000000')
    secondary_color = models.CharField(max_length=7, default='#666666')
    
    # Custom HTML Template
    custom_html = models.TextField(blank=True, help_text='Custom HTML template (for advanced users)')
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_cover_page'
        verbose_name = 'Cover Page Template'
        verbose_name_plural = 'Cover Page Templates'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({'Default' if self.is_default else self.get_template_type_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default per tenant
        if self.is_default:
            CoverPage.objects.filter(tenant=self.tenant, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class InboundFaxSettings(models.Model):
    """Inbound fax configuration per user/DID"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='inbound_fax_settings')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Reception Settings
    auto_print = models.BooleanField(default=False, help_text='Automatically print received faxes')
    printer_name = models.CharField(max_length=100, blank=True, help_text='Network printer name')
    
    # Email Delivery
    email_enabled = models.BooleanField(default=True)
    email_address = models.EmailField(help_text='Primary email for fax delivery')
    cc_addresses = models.TextField(blank=True, help_text='CC email addresses (one per line)')
    
    EMAIL_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('both', 'Both PDF and TIFF'),
    ]
    email_format = models.CharField(max_length=10, choices=EMAIL_FORMAT_CHOICES, default='pdf')
    
    # Email Template
    email_subject_template = models.CharField(
        max_length=255, 
        default='Fax received from {sender} - {pages} pages',
        help_text='Variables: {sender}, {recipient}, {pages}, {date}, {time}'
    )
    include_cover_sheet = models.BooleanField(default=False, help_text='Include summary cover sheet in email')
    
    # OCR Settings
    ocr_enabled = models.BooleanField(default=False, help_text='Perform OCR on received faxes')
    ocr_language = models.CharField(max_length=10, default='eng', help_text='OCR language code')
    searchable_pdf = models.BooleanField(default=True, help_text='Create searchable PDFs when OCR is enabled')
    
    # Storage Settings
    archive_enabled = models.BooleanField(default=True)
    archive_days = models.IntegerField(default=90, help_text='Days to keep faxes in archive')
    
    STORAGE_CHOICES = [
        ('local', 'Local Storage'),
        ('s3', 'Amazon S3'),
        ('azure', 'Azure Blob'),
        ('gcs', 'Google Cloud Storage'),
    ]
    storage_backend = models.CharField(max_length=20, choices=STORAGE_CHOICES, default='local')
    storage_path = models.CharField(max_length=255, blank=True, help_text='Custom storage path/bucket')
    
    # Routing Rules
    routing_enabled = models.BooleanField(default=False, help_text='Enable advanced routing rules')
    routing_rules = models.JSONField(
        default=dict, 
        blank=True,
        help_text='JSON routing rules based on sender, time, etc.'
    )
    
    # Notifications
    sms_notification = models.BooleanField(default=False)
    sms_number = models.CharField(max_length=20, blank=True)
    
    webhook_enabled = models.BooleanField(default=False)
    webhook_url = models.URLField(blank=True)
    webhook_secret = models.CharField(max_length=64, blank=True)
    
    # Security
    require_encryption = models.BooleanField(default=False, help_text='Encrypt stored faxes')
    allowed_senders = models.TextField(blank=True, help_text='Whitelist of allowed sender numbers (one per line)')
    blocked_senders = models.TextField(blank=True, help_text='Blacklist of blocked sender numbers (one per line)')
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_inbound_settings'
        verbose_name = 'Inbound Fax Settings'
        verbose_name_plural = 'Inbound Fax Settings'
    
    def __str__(self):
        return f"Inbound settings for {self.user.username}"


class OutboundFaxSettings(models.Model):
    """Outbound fax configuration per user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='outbound_fax_settings')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Default Settings
    default_did = models.ForeignKey(DID, on_delete=models.SET_NULL, null=True, blank=True, help_text='Default outbound DID')
    default_cover_page = models.ForeignKey(CoverPage, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Transmission Settings
    use_ecm = models.BooleanField(default=True, help_text='Use Error Correction Mode')
    fine_resolution = models.BooleanField(default=False, help_text='Use fine resolution (204x196 dpi)')
    max_retries = models.IntegerField(default=3, help_text='Maximum retry attempts')
    retry_interval = models.IntegerField(default=300, help_text='Seconds between retries')
    
    # Confirmation
    confirmation_enabled = models.BooleanField(default=True)
    confirmation_email = models.EmailField(blank=True)
    include_first_page = models.BooleanField(default=True, help_text='Include first page in confirmation')
    
    # Header Customization
    header_format = models.CharField(
        max_length=255,
        default='{date} {time} | From: {sender} | To: {recipient} | Page {page}/{total}',
        help_text='Header format for transmitted pages'
    )
    
    # Scheduling
    allow_scheduling = models.BooleanField(default=True, help_text='Allow scheduled transmissions')
    business_hours_only = models.BooleanField(default=False, help_text='Send only during business hours')
    business_hours_start = models.TimeField(default='08:00')
    business_hours_end = models.TimeField(default='18:00')
    business_days = models.CharField(max_length=20, default='1,2,3,4,5', help_text='Comma-separated day numbers (1=Monday)')
    
    # Cost Controls
    max_pages_per_fax = models.IntegerField(default=100)
    max_cost_per_fax = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    require_approval_above = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_outbound_settings'
        verbose_name = 'Outbound Fax Settings'
        verbose_name_plural = 'Outbound Fax Settings'
    
    def __str__(self):
        return f"Outbound settings for {self.user.username}"


class UserProfile(models.Model):
    """Extended user profile for fax system"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fax_profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    
    # Personal Information
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=100, blank=True)
    
    # Permissions
    can_send_fax = models.BooleanField(default=True)
    can_receive_fax = models.BooleanField(default=True)
    can_manage_contacts = models.BooleanField(default=True)
    can_view_reports = models.BooleanField(default=False)
    is_tenant_admin = models.BooleanField(default=False)
    
    # Preferences
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='%Y-%m-%d')
    time_format = models.CharField(max_length=20, default='%H:%M:%S')
    
    # Usage Limits
    max_pages_per_day = models.IntegerField(default=100)
    max_pages_per_month = models.IntegerField(default=1000)
    pages_sent_today = models.IntegerField(default=0)
    pages_sent_this_month = models.IntegerField(default=0)
    
    # Signature
    signature_image = models.ImageField(upload_to='signatures/', blank=True, null=True)
    signature_text = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.tenant.name})"