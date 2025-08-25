#!/bin/bash

# Load Testing Script for Fax API
# Creates multiple transactions to test performance

API="http://127.0.0.1:8585"
TOKEN="4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"

# Number of test iterations
NUM_TESTS=${1:-10}

echo "Fax API Load Test"
echo "================="
echo "Creating $NUM_TESTS test transactions..."
echo ""

# Create test files
echo "Creating test files..."
for i in $(seq 1 5); do
    cat > "test_file_$i.txt" << EOF
Test Document $i
================
Generated at: $(date)
Document ID: $i
Random data: $(openssl rand -hex 32)

This is test document number $i for load testing.
It contains multiple lines to simulate a real document.

Page 1 of 1
EOF
done

# Arrays to store results
declare -a UPLOADED_FILES
declare -a TRANSACTION_UUIDS

# Test file uploads
echo -e "\n1. Testing file uploads..."
START_TIME=$(date +%s)

for i in $(seq 1 $NUM_TESTS); do
    FILE_NUM=$((i % 5 + 1))
    echo -n "Upload $i/$NUM_TESTS... "
    
    response=$(curl -s -X POST \
        -H "Authorization: Token $TOKEN" \
        -F "file=@test_file_$FILE_NUM.txt" \
        "$API/api/fax/upload/")
    
    if echo "$response" | grep -q "filename"; then
        filename=$(echo "$response" | python -c "import sys, json; print(json.load(sys.stdin)['filename'])" 2>/dev/null)
        UPLOADED_FILES+=("$filename")
        echo "✓ ($filename)"
    else
        echo "✗"
    fi
done

UPLOAD_TIME=$(($(date +%s) - START_TIME))
echo "Upload completed in ${UPLOAD_TIME}s"

# Test transaction creation (mock, since FreeSWITCH isn't running)
echo -e "\n2. Creating mock transactions..."
START_TIME=$(date +%s)

for i in $(seq 1 $NUM_TESTS); do
    echo -n "Transaction $i/$NUM_TESTS... "
    
    # Generate random phone numbers
    SENDER="90850$(shuf -i 1000000-9999999 -n 1)"
    RECIPIENT="0531$(shuf -i 1000000-9999999 -n 1)"
    
    # Use Python to create mock transaction directly
    uuid=$(python3 << EOF
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()
from main.apps.fax.models import FaxTransaction
from django.contrib.auth.models import User

try:
    user = User.objects.get(username='testuser')
    trans = FaxTransaction.objects.create(
        direction='outbound',
        status='sent',
        sender_number='$SENDER',
        recipient_number='$RECIPIENT',
        file_path='/opt/fs-service/fax_files/tx/test.tiff',
        original_filename='test_$i.txt',
        pages=$((RANDOM % 10 + 1)),
        duration=$((RANDOM % 300 + 30))
    )
    print(trans.uuid)
except Exception as e:
    print("ERROR")
EOF
)
    
    if [ "$uuid" != "ERROR" ]; then
        TRANSACTION_UUIDS+=("$uuid")
        echo "✓ ($uuid)"
    else
        echo "✗"
    fi
done

TRANSACTION_TIME=$(($(date +%s) - START_TIME))
echo "Transactions created in ${TRANSACTION_TIME}s"

# Test API performance
echo -e "\n3. Testing API read performance..."
START_TIME=$(date +%s)

# List all transactions
echo -n "Fetching transaction list... "
response=$(curl -s -w "\n%{time_total}" -X GET \
    -H "Authorization: Token $TOKEN" \
    "$API/api/fax/list/")
    
response_time=$(echo "$response" | tail -n 1)
count=$(echo "$response" | head -n -1 | python -c "import sys, json; print(json.load(sys.stdin)['count'])" 2>/dev/null)
echo "✓ ($count transactions in ${response_time}s)"

# Get individual transaction status
echo "Testing individual status queries..."
for i in $(seq 0 4); do
    if [ ${#TRANSACTION_UUIDS[@]} -gt $i ]; then
        uuid=${TRANSACTION_UUIDS[$i]}
        echo -n "  Query $((i+1)): "
        
        response_time=$(curl -s -w "%{time_total}" -o /dev/null -X GET \
            -H "Authorization: Token $TOKEN" \
            "$API/api/fax/status/$uuid/")
        
        echo "${response_time}s"
    fi
done

READ_TIME=$(($(date +%s) - START_TIME))
echo "Read tests completed in ${READ_TIME}s"

# Statistics
echo -e "\n4. Performance Summary"
echo "======================"
echo "Files uploaded: ${#UPLOADED_FILES[@]}"
echo "Transactions created: ${#TRANSACTION_UUIDS[@]}"
echo "Upload time: ${UPLOAD_TIME}s"
echo "Transaction time: ${TRANSACTION_TIME}s"
echo "Read test time: ${READ_TIME}s"
echo "Total time: $((UPLOAD_TIME + TRANSACTION_TIME + READ_TIME))s"

# Database statistics
echo -e "\n5. Database Statistics"
python3 << EOF
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()
from main.apps.fax.models import FaxTransaction, FaxQueue

total_trans = FaxTransaction.objects.count()
total_queue = FaxQueue.objects.count()
sent = FaxTransaction.objects.filter(status='sent').count()
failed = FaxTransaction.objects.filter(status='failed').count()
processing = FaxTransaction.objects.filter(status='processing').count()

print(f"Total transactions: {total_trans}")
print(f"Total queue items: {total_queue}")
print(f"Sent: {sent}")
print(f"Failed: {failed}")
print(f"Processing: {processing}")
EOF

# Cleanup
echo -e "\n6. Cleanup"
echo "Removing test files..."
rm -f test_file_*.txt
echo "Done!"

echo -e "\nLoad test completed successfully!"