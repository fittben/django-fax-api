#!/usr/bin/env python
"""Test real fax sending through FreeSWITCH"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

import main.utils.esl.ESL_py3 as ESL
from main.apps.core.vars import FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD, TXFAX_DIR

print("Testing Real Fax Transmission")
print("=" * 40)

# Check for test TIFF file
test_tiff = "/opt/fs-service/Samples/txfax-sample.tiff"
if not os.path.exists(test_tiff):
    print(f"Creating test TIFF file...")
    # Create a simple test TIFF using ImageMagick if available
    os.system(f'convert -size 1700x2200 xc:white -pointsize 72 -draw "text 100,200 \'TEST FAX\'" {test_tiff} 2>/dev/null')
    if not os.path.exists(test_tiff):
        print("Warning: Could not create TIFF file. Using text file instead.")
        test_tiff = "/opt/fs-service/test_document.txt"

print(f"Test file: {test_tiff}")
print(f"File exists: {os.path.exists(test_tiff)}")

# Gateway information from FreeSWITCH
gateway_name = "telnyx"  # From sofia status output
test_number = "19999999999"  # Replace with actual test number

print(f"\nGateway: {gateway_name}")
print(f"Test number: {test_number}")

# Connect to FreeSWITCH
con = ESL.ESLconnection(FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD)

if not con.connected():
    print("✗ Failed to connect to FreeSWITCH")
    sys.exit(1)

print("✓ Connected to FreeSWITCH")

# Generate UUID for tracking
res = con.api("create_uuid")
call_uuid = res.getBody().strip()
print(f"Call UUID: {call_uuid}")

# Build originate command for fax
# Note: Using the actual gateway name from sofia status
originate_cmd = (
    f"{{origination_uuid={call_uuid},"
    f"ignore_early_media=true,"
    f"absolute_codec_string='PCMU,PCMA',"
    f"fax_enable_t38=true,"
    f"fax_verbose=true,"
    f"fax_use_ecm=false,"
    f"fax_enable_t38_request=false,"
    f"fax_ident=TEST_FAX}}"
    f"sofia/gateway/{gateway_name}/{test_number} "
    f"&txfax({test_tiff})"
)

print(f"\nOriginate command:")
print(f"{originate_cmd}")

print("\n⚠️  WARNING: This will attempt to send a real fax!")
print("Only proceed if you have:")
print("1. A valid gateway configured in FreeSWITCH")
print("2. A test fax number to receive")
print("3. Sufficient credits/permissions")

response = input("\nProceed with test? (y/N): ")

if response.lower() == 'y':
    print("\nSending fax...")
    res = con.bgapi("originate", originate_cmd)
    
    job_uuid = res.getHeader("Job-UUID")
    body = res.getBody()
    
    print(f"Job UUID: {job_uuid}")
    print(f"Response: {body}")
    
    # Check channel status
    import time
    time.sleep(2)
    
    res = con.api("show", "channels")
    channels = res.getBody()
    
    print("\nActive channels:")
    print(channels[:500] if len(channels) > 500 else channels)
    
    # Check for errors
    res = con.api("uuid_exists", call_uuid)
    exists = res.getBody().strip()
    
    if exists == "true":
        print(f"\n✓ Call {call_uuid} is active")
        
        # Get call details
        res = con.api("uuid_getvar", f"{call_uuid} channel_name")
        channel = res.getBody()
        print(f"Channel: {channel}")
    else:
        print(f"\n✗ Call {call_uuid} not found (may have completed or failed)")
else:
    print("\nTest cancelled")

con.disconnect()
print("\n✓ Disconnected from FreeSWITCH")