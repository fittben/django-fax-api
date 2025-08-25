#!/usr/bin/env python3
"""
FreeSWITCH Fax Event Handler
This script is called by FreeSWITCH when fax events occur
"""

import os
import sys
import json
from datetime import datetime

# Add Django path
sys.path.append('/opt/fs-service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

import django
django.setup()

from main.apps.fax.rx_processor import RXFaxProcessor
from main.apps.fax.tx_processor import TXFaxProcessor
from main.apps.fax.models_extended import FaxTransmission


def process_receive_fax(env_vars):
    """Process received fax event from FreeSWITCH"""
    
    fax_data = {
        'caller_id_number': env_vars.get('fax_remote_station_id', env_vars.get('Caller-Caller-ID-Number', 'Unknown')),
        'destination_number': env_vars.get('fax_local_station_id', env_vars.get('Caller-Destination-Number', 'Unknown')),
        'fax_file': env_vars.get('fax_image', ''),
        'call_uuid': env_vars.get('Unique-ID', ''),
        'pages': int(env_vars.get('fax_pages', 0)),
        'duration': int(env_vars.get('fax_duration', 0)),
        'resolution': env_vars.get('fax_resolution', 'standard'),
        'transfer_rate': int(env_vars.get('fax_transfer_rate', 14400)),
    }
    
    print(f"Processing received fax from {fax_data['caller_id_number']}")
    
    processor = RXFaxProcessor(fax_data)
    success = processor.process()
    
    if success:
        print("Fax processing completed successfully")
        return 0
    else:
        print("Fax processing failed")
        return 1


def process_send_fax_result(env_vars):
    """Process sent fax result from FreeSWITCH"""
    
    # Find transmission by call UUID
    call_uuid = env_vars.get('Unique-ID', '')
    
    try:
        transmission = FaxTransmission.objects.get(call_uuid=call_uuid)
        
        freeswitch_data = {
            'fax_result': env_vars.get('fax_result', 'FAILURE'),
            'fax_error': env_vars.get('fax_error', ''),
            'fax_error_code': env_vars.get('fax_error_code', ''),
            'fax_pages': int(env_vars.get('fax_pages', 0)),
            'fax_duration': int(env_vars.get('fax_duration', 0)),
            'fax_transfer_rate': int(env_vars.get('fax_transfer_rate', 14400)),
            'fax_ecm': env_vars.get('fax_ecm', 'false'),
            'fax_remote_station_id': env_vars.get('fax_remote_station_id', ''),
            'fax_local_station_id': env_vars.get('fax_local_station_id', ''),
        }
        
        print(f"Processing sent fax result for {transmission.uuid}")
        
        processor = TXFaxProcessor(transmission.uuid)
        success = processor.process_completion(freeswitch_data)
        
        if success:
            print("TX fax post-processing completed")
            return 0
        else:
            print("TX fax post-processing failed")
            return 1
            
    except FaxTransmission.DoesNotExist:
        print(f"No transmission found for call UUID: {call_uuid}")
        return 1


def main():
    """Main entry point"""
    
    # Get environment variables from FreeSWITCH
    env_vars = dict(os.environ)
    
    # Log all variables for debugging
    log_file = '/tmp/fax_events.log'
    with open(log_file, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Event Variables:\n")
        for key, value in sorted(env_vars.items()):
            if 'fax' in key.lower() or 'Caller' in key:
                f.write(f"  {key}: {value}\n")
    
    # Determine event type
    event_name = env_vars.get('Event-Name', '')
    fax_success = env_vars.get('fax_success', '')
    
    if event_name == 'CHANNEL_HANGUP' or event_name == 'CHANNEL_HANGUP_COMPLETE':
        # Check if this was a fax call
        if 'rxfax' in env_vars.get('variable_current_application', ''):
            # Received fax
            if fax_success == 'true':
                return process_receive_fax(env_vars)
        elif 'txfax' in env_vars.get('variable_current_application', ''):
            # Sent fax
            return process_send_fax_result(env_vars)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())