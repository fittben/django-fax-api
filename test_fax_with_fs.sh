#!/bin/bash

# Test Fax API with FreeSWITCH Integration

API="http://127.0.0.1:8585"
TOKEN="4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"

echo "Testing Fax API with FreeSWITCH"
echo "================================"
echo ""

# 1. Create a test file
echo "1. Creating test file..."
cat > test_fax.txt << EOF
FAX TEST DOCUMENT
=================
Date: $(date)
Test ID: $(uuidgen)

This is a test fax transmission
using FreeSWITCH and Django API.

Line 1: Testing
Line 2: More testing
Line 3: Final test

End of document.
EOF

# 2. Upload the file
echo "2. Uploading file..."
upload_response=$(curl -s -X POST \
    -H "Authorization: Token $TOKEN" \
    -F "file=@test_fax.txt" \
    "$API/api/fax/upload/")

echo "Upload response: $upload_response"

# Extract filename
filename=$(echo "$upload_response" | python -c "import sys, json; print(json.load(sys.stdin)['filename'])" 2>/dev/null)

if [ -z "$filename" ]; then
    echo "Error: Failed to upload file"
    exit 1
fi

echo "Uploaded as: $filename"

# 3. Send fax using the telnyx gateway
echo ""
echo "3. Attempting to send fax..."
echo "   Gateway: telnyx (from FreeSWITCH)"
echo "   Test number: You need to provide a real number"
echo ""

# Using a more realistic configuration
# The username should match the gateway configuration
fax_data='{
    "username": "telnyx",
    "filename": "'$filename'",
    "numbers": "19999999999",
    "is_enhanced": false
}'

echo "Sending with data:"
echo "$fax_data" | python -m json.tool

send_response=$(curl -s -X POST \
    -H "Authorization: Token $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$fax_data" \
    "$API/api/fax/send/")

echo ""
echo "Send response:"
echo "$send_response" | python -m json.tool 2>/dev/null || echo "$send_response"

# Extract UUID if successful
uuid=$(echo "$send_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('uuid', ''))" 2>/dev/null)

if [ -n "$uuid" ]; then
    echo ""
    echo "4. Checking status..."
    sleep 2
    
    status_response=$(curl -s -X GET \
        -H "Authorization: Token $TOKEN" \
        "$API/api/fax/status/$uuid/")
    
    echo "Status:"
    echo "$status_response" | python -m json.tool
fi

echo ""
echo "Test complete!"
echo ""
echo "Note: Actual fax transmission requires:"
echo "1. Valid gateway configuration in FreeSWITCH"
echo "2. Real phone number with fax capability"
echo "3. Proper TIFF file conversion (ImageMagick required)"