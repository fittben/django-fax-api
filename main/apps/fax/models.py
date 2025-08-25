from django.db import models

# Import complete models if needed
try:
    from .models_complete import *
except ImportError:
    pass
from django.contrib.auth.models import User
import uuid

class FaxTransaction(models.Model):
    DIRECTION_CHOICES = [
        ('outbound', 'Outbound'),
        ('inbound', 'Inbound'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('failed', 'Failed'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    sender_number = models.CharField(max_length=20)
    recipient_number = models.CharField(max_length=20)
    
    file_path = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    converted_filename = models.CharField(max_length=255, blank=True, null=True)
    
    pages = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)
    
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'fax_transaction'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.direction} Fax {self.uuid} - {self.status}"


class FaxQueue(models.Model):
    transaction = models.ForeignKey(FaxTransaction, on_delete=models.CASCADE, related_name='queue_items')
    recipient_number = models.CharField(max_length=20)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    job_uuid = models.CharField(max_length=80, blank=True, null=True)
    event_name = models.CharField(max_length=80, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fax_queue'
        ordering = ['created_at']
        
    def __str__(self):
        return f"Queue for {self.transaction.uuid} to {self.recipient_number}"