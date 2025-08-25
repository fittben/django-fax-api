"""
Transmit (TX) Fax Post-Processing Handler
Processes outgoing faxes after FreeSWITCH transmission
"""

import os
import json
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings
from .models_extended import FaxAccount, FaxTransmission, FaxPage, FaxLog, FaxWebhook, FaxContact
import requests
import hashlib
import hmac
import main.utils.esl.ESL_py3 as ESL
from main.apps.core.vars import FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD


class TXFaxProcessor:
    """Process transmitted faxes and handle post-processing"""
    
    def __init__(self, transmission_uuid):
        """Initialize with transmission UUID"""
        self.transmission = FaxTransmission.objects.get(uuid=transmission_uuid)
        self.account = self.transmission.account
        
    def process_completion(self, freeswitch_data):
        """
        Process fax completion data from FreeSWITCH
        
        freeswitch_data should contain:
        - fax_result: SUCCESS or FAILURE
        - fax_error: Error message if failed
        - fax_pages: Number of pages transmitted
        - fax_duration: Transmission duration
        - fax_transfer_rate: Actual baud rate
        - fax_ecm: Whether ECM was used
        """
        try:
            # 1. Update transmission status
            self._update_transmission_status(freeswitch_data)
            
            # 2. Log transmission details
            self._log_transmission_details(freeswitch_data)
            
            # 3. Update contact if exists
            self._update_contact_usage()
            
            # 4. Calculate and apply costs
            self._calculate_costs()
            
            # 5. Send confirmation email
            if self.account.send_fax_to_email:
                self._send_confirmation_email()
            
            # 6. Trigger webhooks
            self._trigger_webhooks()
            
            # 7. Handle retries if failed
            if self.transmission.status == 'failed':
                self._handle_retry()
            
            # 8. Update account usage
            self._update_account_usage()
            
            # 9. Archive if successful
            if self.transmission.status == 'completed':
                self._archive_transmission()
            
            self._log_info("Post-processing completed")
            return True
            
        except Exception as e:
            self._log_error(f"Post-processing failed: {str(e)}")
            return False
    
    def _update_transmission_status(self, data):
        """Update transmission status based on FreeSWITCH result"""
        result = data.get('fax_result', 'FAILURE')
        
        if result == 'SUCCESS':
            self.transmission.status = 'completed'
            self.transmission.completed_at = datetime.now()
            self._log_info("Transmission completed successfully")
        else:
            error = data.get('fax_error', 'Unknown error')
            if 'BUSY' in error:
                self.transmission.status = 'busy'
            elif 'NO_ANSWER' in error:
                self.transmission.status = 'no_answer'
            else:
                self.transmission.status = 'failed'
            
            self.transmission.error_code = data.get('fax_error_code', '')
            self.transmission.error_message = error
            self._log_error(f"Transmission failed: {error}")
        
        # Update transmission details
        self.transmission.pages = data.get('fax_pages', self.transmission.pages)
        self.transmission.duration = data.get('fax_duration', 0)
        self.transmission.baud_rate = data.get('fax_transfer_rate', 14400)
        self.transmission.ecm_used = data.get('fax_ecm', 'false').lower() == 'true'
        
        self.transmission.save()
    
    def _log_transmission_details(self, data):
        """Log detailed transmission information"""
        details = {
            'result': data.get('fax_result'),
            'pages_sent': data.get('fax_pages'),
            'duration': data.get('fax_duration'),
            'transfer_rate': data.get('fax_transfer_rate'),
            'ecm_used': data.get('fax_ecm'),
            'remote_station_id': data.get('fax_remote_station_id'),
            'local_station_id': data.get('fax_local_station_id'),
        }
        
        FaxLog.objects.create(
            transmission=self.transmission,
            level='info',
            message='Transmission details',
            details=details
        )
    
    def _update_contact_usage(self):
        """Update contact usage statistics"""
        try:
            contact = FaxContact.objects.get(
                account=self.account,
                fax_number=self.transmission.recipient_number
            )
            contact.last_used = datetime.now()
            contact.usage_count += 1
            contact.save()
        except FaxContact.DoesNotExist:
            # Optionally create new contact
            if self.transmission.status == 'completed':
                FaxContact.objects.create(
                    account=self.account,
                    name=self.transmission.recipient_name or 'Auto-added',
                    fax_number=self.transmission.recipient_number,
                    last_used=datetime.now(),
                    usage_count=1
                )
    
    def _calculate_costs(self):
        """Calculate transmission costs"""
        if self.transmission.status == 'completed':
            self.transmission.cost = self.transmission.calculate_cost()
            self.transmission.save()
            self._log_info(f"Cost calculated: ${self.transmission.cost:.2f}")
    
    def _send_confirmation_email(self):
        """Send transmission confirmation email"""
        try:
            if self.transmission.status == 'completed':
                subject = f"Fax Sent Successfully to {self.transmission.recipient_number}"
                status_text = "successfully sent"
            else:
                subject = f"Fax Failed to {self.transmission.recipient_number}"
                status_text = f"failed ({self.transmission.error_message})"
            
            body = f"""
Your fax transmission has been {status_text}.

To: {self.transmission.recipient_number}
Pages: {self.transmission.pages}
Duration: {self.transmission.duration} seconds
Status: {self.transmission.status}
Cost: ${self.transmission.cost:.2f}

Fax ID: {self.transmission.uuid}
Sent: {self.transmission.started_at}
            """
            
            if self.transmission.status != 'completed':
                body += f"\nError: {self.transmission.error_message}"
                if self.transmission.retry_count < self.transmission.max_retries:
                    body += f"\nRetry {self.transmission.retry_count + 1}/{self.transmission.max_retries} will be attempted."
            
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.account.notification_email],
            )
            
            email.send()
            self._log_info(f"Confirmation email sent to {self.account.notification_email}")
            
        except Exception as e:
            self._log_error(f"Email notification failed: {str(e)}")
    
    def _trigger_webhooks(self):
        """Trigger appropriate webhooks"""
        if self.transmission.status == 'completed':
            event_type = 'on_sent'
            event_name = 'fax.sent'
        else:
            event_type = 'on_failed'
            event_name = 'fax.failed'
        
        webhooks = FaxWebhook.objects.filter(
            account=self.account,
            is_active=True
        ).filter(**{event_type: True})
        
        for webhook in webhooks:
            self._send_webhook(webhook, event_name)
    
    def _send_webhook(self, webhook, event_name):
        """Send webhook notification"""
        try:
            payload = {
                'event': event_name,
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'uuid': str(self.transmission.uuid),
                    'from': self.transmission.sender_number,
                    'to': self.transmission.recipient_number,
                    'pages': self.transmission.pages,
                    'duration': self.transmission.duration,
                    'status': self.transmission.status,
                    'cost': float(self.transmission.cost),
                }
            }
            
            if self.transmission.status != 'completed':
                payload['data']['error'] = self.transmission.error_message
            
            # Calculate signature
            signature = hmac.new(
                webhook.secret_key.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                'Content-Type': 'application/json',
                'X-Fax-Signature': signature
            }
            
            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                webhook.last_triggered = datetime.now()
                webhook.failure_count = 0
            else:
                webhook.failure_count += 1
            
            webhook.save()
            self._log_info(f"Webhook triggered: {webhook.url}")
            
        except Exception as e:
            webhook.failure_count += 1
            webhook.save()
            self._log_error(f"Webhook failed: {str(e)}")
    
    def _handle_retry(self):
        """Handle automatic retry for failed transmissions"""
        if self.transmission.retry_count < self.transmission.max_retries:
            self.transmission.retry_count += 1
            
            # Schedule retry (could use Celery for this)
            retry_delay = 60 * (2 ** self.transmission.retry_count)  # Exponential backoff
            
            self._log_info(f"Scheduling retry {self.transmission.retry_count}/{self.transmission.max_retries} in {retry_delay} seconds")
            
            # Reset status for retry
            self.transmission.status = 'queued'
            self.transmission.save()
            
            # In production, use Celery or similar for delayed execution
            # For now, just log the intention
            FaxLog.objects.create(
                transmission=self.transmission,
                level='info',
                message=f'Retry scheduled',
                details={'retry_count': self.transmission.retry_count, 'delay': retry_delay}
            )
    
    def _update_account_usage(self):
        """Update account usage statistics"""
        if self.transmission.status == 'completed':
            self.account.pages_sent_this_month += self.transmission.pages
            self.account.save()
    
    def _archive_transmission(self):
        """Archive successful transmission"""
        # Move files to archive directory
        archive_dir = os.path.join(
            settings.MEDIA_ROOT, 
            'fax', 
            'archive',
            datetime.now().strftime('%Y/%m/%d'),
            str(self.transmission.uuid)
        )
        os.makedirs(archive_dir, exist_ok=True)
        
        # Copy transmission file
        if os.path.exists(self.transmission.file_path):
            import shutil
            archive_path = os.path.join(archive_dir, os.path.basename(self.transmission.file_path))
            shutil.copy2(self.transmission.file_path, archive_path)
            self._log_info(f"Archived to {archive_path}")
    
    def check_transmission_status(self):
        """Check current transmission status in FreeSWITCH"""
        try:
            con = ESL.ESLconnection(FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD)
            
            if not con.connected():
                self._log_error("Failed to connect to FreeSWITCH")
                return None
            
            # Check if call exists
            res = con.api("uuid_exists", self.transmission.call_uuid)
            exists = res.getBody().strip()
            
            if exists == "true":
                # Get call details
                res = con.api("uuid_getvar", f"{self.transmission.call_uuid} fax_result")
                fax_result = res.getBody().strip()
                
                res = con.api("uuid_getvar", f"{self.transmission.call_uuid} fax_pages")
                fax_pages = res.getBody().strip()
                
                status = {
                    'call_active': True,
                    'fax_result': fax_result,
                    'fax_pages': fax_pages
                }
            else:
                status = {'call_active': False}
            
            con.disconnect()
            return status
            
        except Exception as e:
            self._log_error(f"Status check failed: {str(e)}")
            return None
    
    def cancel_transmission(self):
        """Cancel an active transmission"""
        try:
            con = ESL.ESLconnection(FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD)
            
            if not con.connected():
                self._log_error("Failed to connect to FreeSWITCH")
                return False
            
            # Kill the call
            res = con.api("uuid_kill", self.transmission.call_uuid)
            result = res.getBody()
            
            con.disconnect()
            
            # Update transmission status
            self.transmission.status = 'cancelled'
            self.transmission.completed_at = datetime.now()
            self.transmission.save()
            
            self._log_info(f"Transmission cancelled: {result}")
            return True
            
        except Exception as e:
            self._log_error(f"Cancellation failed: {str(e)}")
            return False
    
    def _log_info(self, message):
        """Log info message"""
        FaxLog.objects.create(
            transmission=self.transmission,
            level='info',
            message=message
        )
        print(f"[INFO] {message}")
    
    def _log_error(self, message):
        """Log error message"""
        FaxLog.objects.create(
            transmission=self.transmission,
            level='error',
            message=message
        )
        print(f"[ERROR] {message}")