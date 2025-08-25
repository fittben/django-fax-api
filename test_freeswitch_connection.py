#!/usr/bin/env python
"""Test FreeSWITCH ESL connection"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

import main.utils.esl.ESL_py3 as ESL
from main.apps.core.vars import FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD

print("Testing FreeSWITCH Connection")
print("=" * 40)
print(f"Host: {FREESWITCH_IP_ADDRESS}")
print(f"Port: {FREESWITCH_PORT}")
print(f"Password: {'*' * len(FREESWITCH_PASSWORD)}")
print()

# Test connection
con = ESL.ESLconnection(FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, FREESWITCH_PASSWORD)

if con.connected():
    print("✓ Successfully connected to FreeSWITCH!")
    
    # Get FreeSWITCH status
    res = con.api("status")
    print("\nFreeSWITCH Status:")
    print("-" * 40)
    print(res.getBody())
    
    # Get registered gateways
    res = con.api("sofia status")
    print("\nSofia Status:")
    print("-" * 40)
    status_output = res.getBody()
    print(status_output[:500] + "..." if len(status_output) > 500 else status_output)
    
    # Check for gateways
    res = con.api("sofia status gateway")
    print("\nGateways:")
    print("-" * 40)
    gateway_output = res.getBody()
    print(gateway_output)
    
    con.disconnect()
    print("\n✓ Connection test completed successfully")
else:
    print("✗ Failed to connect to FreeSWITCH")
    print("\nPossible issues:")
    print("1. FreeSWITCH is not running")
    print("2. ESL is not enabled")
    print("3. Wrong IP/Port/Password")
    print("4. Firewall blocking connection")
    
    # Try to check if it's a password issue
    print("\nTrying with default password 'ClueCon'...")
    con2 = ESL.ESLconnection(FREESWITCH_IP_ADDRESS, FREESWITCH_PORT, "ClueCon")
    if con2.connected():
        print("✓ Connected with default password!")
        print("Update FREESWITCH_PASSWORD in /opt/fs-service/main/apps/core/vars.py")
        con2.disconnect()
    else:
        print("✗ Default password also failed")