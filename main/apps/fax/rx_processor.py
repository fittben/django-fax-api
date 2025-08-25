"""
Receive (RX) Fax Processing Handler
Processes incoming faxes from FreeSWITCH
"""

import os
import shutil
import json
from datetime import datetime
from PIL import Image
import PyPDF2
from django.core.mail import EmailMessage
from django.conf import settings
from .models_extended import FaxAccount, FaxTransmission, FaxPage, FaxLog, FaxWebhook
import requests
import hashlib
import hmac


class RXFaxProcessor:
    """Process received faxes from FreeSWITCH"""
    
    def __init__(self, fax_data):
        """
        Initialize with fax data from FreeSWITCH
        
        fax_data should contain:
        - caller_id_number: Sender's phone number
        - destination_number: Recipient's phone number (our number)
        - fax_file: Path to received TIFF file
        - call_uuid: FreeSWITCH call UUID
        - pages: Number of pages
        - duration: Call duration
        - resolution: Fax resolution
        - transfer_rate: Baud rate
        """
        self.fax_data = fax_data
        self.account = None
        self.transmission = None
        
    def process(self):
        """Main processing pipeline"""
        try:
            # 1. Identify receiving account
            self.account = self._identify_account()
            if not self.account:
                self._log_error("No account found for number: " + self.fax_data.get('destination_number'))
                return False
            
            # 2. Create transmission record
            self.transmission = self._create_transmission_record()
            
            # 3. Process the fax file
            self._process_fax_file()
            
            # 4. Extract individual pages
            self._extract_pages()
            
            # 5. Convert to desired format
            output_file = self._convert_format()
            
            # 6. Send email notification
            if self.account.send_fax_to_email:
                self._send_email_notification(output_file)
            
            # 7. Trigger webhooks
            self._trigger_webhooks()
            
            # 8. Update transmission status
            self.transmission.status = 'completed'
            self.transmission.completed_at = datetime.now()
            self.transmission.save()
            
            # 9. Update account usage
            self._update_account_usage()
            
            self._log_info("Fax processing completed successfully")
            return True
            
        except Exception as e:
            self._log_error(f"Processing failed: {str(e)}")
            if self.transmission:
                self.transmission.status = 'failed'
                self.transmission.error_message = str(e)
                self.transmission.save()
            return False
    
    def _identify_account(self):
        """Identify the receiving account based on destination number"""
        try:
            return FaxAccount.objects.get(
                fax_number=self.fax_data.get('destination_number'),
                is_active=True
            )
        except FaxAccount.DoesNotExist:
            return None
    
    def _create_transmission_record(self):
        """Create database record for received fax"""
        transmission = FaxTransmission.objects.create(
            account=self.account,
            direction='inbound',
            status='transmitting',
            sender_number=self.fax_data.get('caller_id_number', 'Unknown'),
            recipient_number=self.fax_data.get('destination_number'),
            file_path=self.fax_data.get('fax_file'),
            pages=self.fax_data.get('pages', 0),
            duration=self.fax_data.get('duration', 0),
            resolution=self.fax_data.get('resolution', 'standard'),
            baud_rate=self.fax_data.get('transfer_rate', 14400),
            call_uuid=self.fax_data.get('call_uuid', ''),
            started_at=datetime.now()
        )
        
        self._log_info(f"Created transmission record: {transmission.uuid}")
        return transmission
    
    def _process_fax_file(self):
        """Process the received TIFF file"""
        source_file = self.fax_data.get('fax_file')
        if not source_file or not os.path.exists(source_file):
            raise ValueError(f"Fax file not found: {source_file}")
        
        # Create storage directory
        rx_dir = os.path.join(settings.MEDIA_ROOT, 'fax', 'rx', str(self.transmission.uuid))
        os.makedirs(rx_dir, exist_ok=True)
        
        # Copy file to permanent storage
        dest_file = os.path.join(rx_dir, 'original.tiff')
        shutil.copy2(source_file, dest_file)
        
        # Update transmission record
        self.transmission.file_path = dest_file
        self.transmission.file_size = os.path.getsize(dest_file)
        self.transmission.file_hash = self._calculate_file_hash(dest_file)
        self.transmission.save()
        
        self._log_info(f"Processed fax file: {dest_file}")
        return dest_file
    
    def _extract_pages(self):
        """Extract individual pages from multi-page TIFF"""
        try:
            from PIL import Image
            
            tiff_path = self.transmission.file_path
            img = Image.open(tiff_path)
            
            page_dir = os.path.dirname(tiff_path)
            page_count = 0
            
            # Extract each page
            for i in range(100):  # Max 100 pages
                try:
                    img.seek(i)
                    page_path = os.path.join(page_dir, f'page_{i+1:03d}.png')
                    img.save(page_path, 'PNG')
                    
                    # Create page record
                    FaxPage.objects.create(
                        transmission=self.transmission,
                        page_number=i+1,
                        file_path=page_path,
                        transmitted_at=datetime.now()
                    )
                    
                    page_count += 1
                except EOFError:
                    break
            
            # Update page count
            self.transmission.pages = page_count
            self.transmission.save()
            
            self._log_info(f"Extracted {page_count} pages")
            
        except Exception as e:
            self._log_warning(f"Page extraction failed: {str(e)}")
    
    def _convert_format(self):
        """Convert fax to user's preferred format"""
        format_type = self.account.email_format
        
        if format_type == 'pdf':
            return self._convert_to_pdf()
        else:
            return self.transmission.file_path  # Return original TIFF
    
    def _convert_to_pdf(self):
        """Convert TIFF to PDF"""
        try:
            from PIL import Image
            
            tiff_path = self.transmission.file_path
            pdf_path = tiff_path.replace('.tiff', '.pdf').replace('.tif', '.pdf')
            
            # Open TIFF
            img = Image.open(tiff_path)
            
            # Convert to PDF
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Handle multi-page TIFF
            images = []
            for i in range(100):
                try:
                    img.seek(i)
                    images.append(img.copy())
                except EOFError:
                    break
            
            if images:
                images[0].save(pdf_path, save_all=True, append_images=images[1:])
            else:
                img.save(pdf_path)
            
            self._log_info(f"Converted to PDF: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self._log_error(f"PDF conversion failed: {str(e)}")
            return self.transmission.file_path
    
    def _send_email_notification(self, attachment_path):
        """Send email notification with fax attachment"""
        try:
            subject = f"Fax Received from {self.transmission.sender_number}"
            
            body = f"""
You have received a new fax.

From: {self.transmission.sender_number}
To: {self.transmission.recipient_number}
Pages: {self.transmission.pages}
Received: {self.transmission.started_at}
Duration: {self.transmission.duration} seconds

Fax ID: {self.transmission.uuid}

This fax has been automatically processed and is attached to this email.
            """
            
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.account.notification_email],
            )
            
            # Attach the fax
            with open(attachment_path, 'rb') as f:
                filename = f"fax_{self.transmission.uuid}.{self.account.email_format}"
                email.attach(filename, f.read(), f'application/{self.account.email_format}')
            
            email.send()
            
            self._log_info(f"Email sent to {self.account.notification_email}")
            
        except Exception as e:
            self._log_error(f"Email notification failed: {str(e)}")
    
    def _trigger_webhooks(self):
        """Trigger configured webhooks"""
        webhooks = FaxWebhook.objects.filter(
            account=self.account,
            on_received=True,
            is_active=True
        )
        
        for webhook in webhooks:
            self._send_webhook(webhook)
    
    def _send_webhook(self, webhook):
        """Send webhook notification"""
        try:
            payload = {
                'event': 'fax.received',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'uuid': str(self.transmission.uuid),
                    'from': self.transmission.sender_number,
                    'to': self.transmission.recipient_number,
                    'pages': self.transmission.pages,
                    'duration': self.transmission.duration,
                    'status': self.transmission.status,
                }
            }
            
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
    
    def _update_account_usage(self):
        """Update account usage statistics"""
        self.account.pages_received_this_month += self.transmission.pages
        self.account.save()
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _log_info(self, message):
        """Log info message"""
        if self.transmission:
            FaxLog.objects.create(
                transmission=self.transmission,
                level='info',
                message=message
            )
        print(f"[INFO] {message}")
    
    def _log_warning(self, message):
        """Log warning message"""
        if self.transmission:
            FaxLog.objects.create(
                transmission=self.transmission,
                level='warning',
                message=message
            )
        print(f"[WARNING] {message}")
    
    def _log_error(self, message):
        """Log error message"""
        if self.transmission:
            FaxLog.objects.create(
                transmission=self.transmission,
                level='error',
                message=message
            )
        print(f"[ERROR] {message}")