import main.utils.esl.ESL_py3 as ESL
from main.apps.core.vars import FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD, RXFAX_DIR, TXFAX_DIR
import os
import uuid as uuid_lib
from .models import FaxTransaction, FaxQueue
from main.apps.service.views.utils.converter import FileConverter


class FaxHandler:
    def __init__(self):
        self.connection = None
        
    def connect(self):
        """Establish connection to FreeSWITCH"""
        self.connection = ESL.ESLconnection(
            FREESWITCH_IP_ADDRESS, 
            FREESWITCH_PORT, 
            FREESWITCH_PASSWORD
        )
        return self.connection.connected()
    
    def disconnect(self):
        """Disconnect from FreeSWITCH"""
        if self.connection:
            self.connection.disconnect()
    
    def send_fax(self, username, file_path, numbers, is_enhanced=False, user=None):
        """Send fax to multiple recipients"""
        results = {
            'success': False,
            'message': '',
            'transaction': None,
            'details': []
        }
        
        # Check if file exists
        full_path = os.path.join(TXFAX_DIR, file_path) if not file_path.startswith('/') else file_path
        if not os.path.isfile(full_path):
            results['message'] = f"File not found: {full_path}"
            return results
        
        # Convert file to TIFF format if needed
        converted_path = full_path
        if not full_path.lower().endswith(('.tif', '.tiff')):
            try:
                converter = FileConverter(filename=full_path, is_enhanced=is_enhanced, DEBUG=False)
                converted_path = converter.convert()
            except Exception as e:
                results['message'] = f"File conversion failed: {str(e)}"
                return results
        else:
            # File is already TIFF, use as-is
            print(f"Using TIFF file directly: {full_path}")
        
        # Create transaction record
        transaction = FaxTransaction.objects.create(
            direction='outbound',
            status='processing',
            sender_number=username,
            recipient_number=numbers,
            file_path=converted_path,
            original_filename=os.path.basename(file_path),
            converted_filename=os.path.basename(converted_path),
            user=user
        )
        
        # Parse recipient numbers
        numbers_list = [num.strip() for num in numbers.split(',')]
        
        # Connect to FreeSWITCH
        if not self.connect():
            transaction.status = 'failed'
            transaction.error_message = "Failed to connect to FreeSWITCH"
            transaction.save()
            results['message'] = "Failed to connect to FreeSWITCH"
            results['transaction'] = transaction
            return results
        
        try:
            # Send fax to each recipient
            for number in numbers_list:
                # Create queue item
                queue_item = FaxQueue.objects.create(
                    transaction=transaction,
                    recipient_number=number
                )
                
                # Generate UUID for this call
                core_uuid = self.connection.api("create_uuid").getBody()
                
                # Build originate command
                originate_cmd = self._build_originate_command(
                    core_uuid, username, number, converted_path
                )
                
                # Execute command
                res = self.connection.bgapi("originate", originate_cmd)
                
                # Update queue item
                queue_item.job_uuid = core_uuid
                queue_item.event_name = res.getHeader("Event-Name")
                queue_item.attempts += 1
                queue_item.save()
                
                # Add to results
                results['details'].append({
                    'recipient': number,
                    'job_uuid': core_uuid,
                    'status': 'initiated'
                })
            
            transaction.status = 'sent'
            transaction.save()
            results['success'] = True
            results['message'] = f"Fax sent to {len(numbers_list)} recipients"
            results['transaction'] = transaction
            
        except Exception as e:
            transaction.status = 'failed'
            transaction.error_message = str(e)
            transaction.save()
            results['message'] = f"Error sending fax: {str(e)}"
            results['transaction'] = transaction
            
        finally:
            self.disconnect()
        
        return results
    
    def _build_originate_command(self, uuid, sender, recipient, file_path):
        """Build FreeSWITCH originate command for fax"""
        params = {
            'origination_uuid': uuid,
            'ignore_early_media': 'true',
            'absolute_codec_string': 'PCMU,PCMA',
            'fax_enable_t38': 'true',
            'fax_verbose': 'true',
            'fax_use_ecm': 'false',
            'fax_enable_t38_request': 'false',
            'fax_ident': sender
        }
        
        param_string = ','.join([f"{k}={v}" for k, v in params.items()])
        command = f"{{{param_string}}}sofia/gateway/{sender}/{recipient} &txfax({file_path})"
        
        return command
    
    def receive_fax(self, caller_number, called_number, file_path):
        """Process received fax"""
        transaction = FaxTransaction.objects.create(
            direction='inbound',
            status='received',
            sender_number=caller_number,
            recipient_number=called_number,
            file_path=file_path,
            original_filename=os.path.basename(file_path)
        )
        
        return transaction
    
    def get_fax_status(self, transaction_uuid):
        """Get status of a fax transaction"""
        try:
            transaction = FaxTransaction.objects.get(uuid=transaction_uuid)
            queue_items = FaxQueue.objects.filter(transaction=transaction)
            
            return {
                'uuid': str(transaction.uuid),
                'status': transaction.status,
                'direction': transaction.direction,
                'sender': transaction.sender_number,
                'recipient': transaction.recipient_number,
                'created': transaction.created_at,
                'queue_items': [
                    {
                        'recipient': item.recipient_number,
                        'attempts': item.attempts,
                        'processed': item.is_processed,
                        'job_uuid': item.job_uuid
                    }
                    for item in queue_items
                ]
            }
        except FaxTransaction.DoesNotExist:
            return None