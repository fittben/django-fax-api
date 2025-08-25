from django.db import models
from django.contrib.auth.models import User
import uuid
import hashlib
from datetime import datetime

class FaxAccount(models.Model):
    """eFax-like account for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fax_number = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=255, blank=True)
    
    # Plan details
    PLAN_CHOICES = [
        ('basic', 'Basic - 150 pages/month'),
        ('plus', 'Plus - 300 pages/month'),
        ('pro', 'Pro - 500 pages/month'),
        ('enterprise', 'Enterprise - Unlimited'),
    ]
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    
    # Usage tracking
    pages_sent_this_month = models.IntegerField(default=0)
    pages_received_this_month = models.IntegerField(default=0)
    
    # Email settings
    notification_email = models.EmailField()
    send_fax_to_email = models.BooleanField(default=True)
    email_format = models.CharField(max_length=10, choices=[('pdf', 'PDF'), ('tiff', 'TIFF')], default='pdf')
    
    # Account status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_account'
        
    def __str__(self):
        return f"{self.user.username} - {self.fax_number}"


class FaxTransmission(models.Model):
    """Extended fax transmission record with complete tracking"""
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('dialing', 'Dialing'),
        ('negotiating', 'Negotiating'),
        ('transmitting', 'Transmitting'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('busy', 'Busy'),
        ('no_answer', 'No Answer'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Core fields
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    account = models.ForeignKey(FaxAccount, on_delete=models.CASCADE, related_name='transmissions')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # Phone numbers
    sender_number = models.CharField(max_length=20)
    sender_name = models.CharField(max_length=255, blank=True)
    recipient_number = models.CharField(max_length=20)
    recipient_name = models.CharField(max_length=255, blank=True)
    
    # File information
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(default=0)
    file_hash = models.CharField(max_length=64, blank=True)  # SHA256 hash
    pages = models.IntegerField(default=0)
    
    # Transmission details
    duration = models.IntegerField(default=0)  # seconds
    baud_rate = models.IntegerField(default=14400)
    resolution = models.CharField(max_length=20, default='standard')
    ecm_used = models.BooleanField(default=False)  # Error Correction Mode
    
    # FreeSWITCH details
    call_uuid = models.CharField(max_length=80, blank=True)
    sip_call_id = models.CharField(max_length=255, blank=True)
    
    # Timing
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_code = models.CharField(max_length=20, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Billing
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    class Meta:
        db_table = 'fax_transmission'
        ordering = ['-queued_at']
        indexes = [
            models.Index(fields=['account', 'direction', 'status']),
            models.Index(fields=['sender_number', 'recipient_number']),
            models.Index(fields=['queued_at']),
        ]
    
    def calculate_cost(self):
        """Calculate transmission cost based on pages and destination"""
        if self.direction == 'inbound':
            return 0
        
        # Basic pricing model
        base_rate = 0.10  # $0.10 per page
        if self.recipient_number.startswith('1'):  # US/Canada
            rate = base_rate
        elif self.recipient_number.startswith('44'):  # UK
            rate = base_rate * 1.5
        else:  # International
            rate = base_rate * 2
        
        return self.pages * rate
    
    def generate_file_hash(self):
        """Generate SHA256 hash of the fax file"""
        if not self.file_path:
            return None
        
        try:
            with open(self.file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
                self.file_hash = file_hash
                return file_hash
        except Exception:
            return None


class FaxPage(models.Model):
    """Individual page tracking for multi-page faxes"""
    transmission = models.ForeignKey(FaxTransmission, on_delete=models.CASCADE, related_name='fax_pages')
    page_number = models.IntegerField()
    file_path = models.CharField(max_length=500)
    
    # Transmission details
    transmitted_at = models.DateTimeField(null=True, blank=True)
    transmission_time = models.IntegerField(default=0)  # seconds
    
    # Quality metrics
    quality_score = models.IntegerField(default=100)  # 0-100
    error_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'fax_page'
        unique_together = ['transmission', 'page_number']
        ordering = ['page_number']


class FaxContact(models.Model):
    """Address book for frequently used fax numbers"""
    account = models.ForeignKey(FaxAccount, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    fax_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    company = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    # Usage tracking
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_contact'
        unique_together = ['account', 'fax_number']
        ordering = ['-last_used', 'name']


class FaxWebhook(models.Model):
    """Webhook configuration for notifications"""
    account = models.ForeignKey(FaxAccount, on_delete=models.CASCADE, related_name='webhooks')
    url = models.URLField()
    
    # Events to trigger on
    on_received = models.BooleanField(default=True)
    on_sent = models.BooleanField(default=True)
    on_failed = models.BooleanField(default=True)
    
    # Security
    secret_key = models.CharField(max_length=64, default=uuid.uuid4)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fax_webhook'


class FaxLog(models.Model):
    """Detailed logging for troubleshooting"""
    transmission = models.ForeignKey(FaxTransmission, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    LOG_LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES)
    
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'fax_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['transmission', 'timestamp']),
        ]