#!/bin/bash

# Cleanup Script - Remove test data from database

API="http://127.0.0.1:8585"
TOKEN="4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"

echo "Fax API Test Data Cleanup"
echo "========================="
echo ""
echo "WARNING: This will delete all test fax transactions from the database!"
echo -n "Are you sure? (y/N): "
read confirmation

if [ "$confirmation" != "y" ] && [ "$confirmation" != "Y" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Cleaning up test data..."

# Clean database using Django shell
python3 << EOF
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from main.apps.fax.models import FaxTransaction, FaxQueue

# Get counts before deletion
trans_count = FaxTransaction.objects.count()
queue_count = FaxQueue.objects.count()

print(f"Found {trans_count} transactions and {queue_count} queue items")

# Delete all test data
if trans_count > 0 or queue_count > 0:
    print("Deleting queue items...")
    FaxQueue.objects.all().delete()
    
    print("Deleting transactions...")
    FaxTransaction.objects.all().delete()
    
    print("Cleanup completed!")
else:
    print("No data to clean up.")

# Verify deletion
remaining = FaxTransaction.objects.count()
print(f"Remaining transactions: {remaining}")
EOF

# Clean up uploaded files
echo ""
echo "Cleaning uploaded files..."
if [ -d "/opt/fs-service/fax_files/tx" ]; then
    file_count=$(ls -1 /opt/fs-service/fax_files/tx/ 2>/dev/null | wc -l)
    if [ $file_count -gt 0 ]; then
        echo "Found $file_count files in tx directory"
        rm -f /opt/fs-service/fax_files/tx/*
        echo "Files deleted."
    else
        echo "No files to clean."
    fi
fi

if [ -d "/opt/fs-service/fax_files/rx" ]; then
    file_count=$(ls -1 /opt/fs-service/fax_files/rx/ 2>/dev/null | wc -l)
    if [ $file_count -gt 0 ]; then
        echo "Found $file_count files in rx directory"
        rm -f /opt/fs-service/fax_files/rx/*
        echo "Files deleted."
    else
        echo "No files to clean."
    fi
fi

echo ""
echo "Cleanup completed successfully!"