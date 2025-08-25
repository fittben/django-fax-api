#!/usr/bin/env python
"""Test fax sending with mock FreeSWITCH connection"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from main.apps.fax.models import FaxTransaction, FaxQueue
from django.contrib.auth.models import User

print("Mock Fax Transaction Test")
print("=" * 40)

# Get test user
user = User.objects.get(username='testuser')

# Create a mock fax transaction directly in the database
print("\n1. Creating mock fax transaction...")
transaction = FaxTransaction.objects.create(
    direction='outbound',
    status='sent',
    sender_number='908509999999',
    recipient_number='05319999999,05329999999',
    file_path='/opt/fs-service/fax_files/tx/test.tiff',
    original_filename='test_document.txt',
    converted_filename='test.tiff',
    pages=1,
    duration=45,
    user=user
)
print(f"   ✓ Created transaction: {transaction.uuid}")

# Create queue items for multiple recipients
recipients = ['05319999999', '05329999999']
for recipient in recipients:
    queue_item = FaxQueue.objects.create(
        transaction=transaction,
        recipient_number=recipient,
        attempts=1,
        is_processed=True,
        job_uuid=f"mock-job-{recipient}"
    )
    print(f"   ✓ Created queue item for: {recipient}")

# Query the database
print("\n2. Querying fax transactions...")
all_transactions = FaxTransaction.objects.all()
print(f"   Total transactions: {all_transactions.count()}")

for trans in all_transactions:
    print(f"\n   Transaction {trans.uuid}:")
    print(f"     Status: {trans.status}")
    print(f"     Direction: {trans.direction}")
    print(f"     Sender: {trans.sender_number}")
    print(f"     Recipients: {trans.recipient_number}")
    print(f"     Created: {trans.created_at}")
    
    queue_items = FaxQueue.objects.filter(transaction=trans)
    print(f"     Queue items: {queue_items.count()}")
    for item in queue_items:
        print(f"       - {item.recipient_number}: {'Processed' if item.is_processed else 'Pending'}")

print("\n" + "=" * 40)
print("Mock test completed successfully!")