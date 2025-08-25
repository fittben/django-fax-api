#!/bin/bash

# Test Fax API with Real Number and TIFF File

API="http://127.0.0.1:8585"
TOKEN="4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"
REAL_NUMBER="18884732963"
TIFF_FILE="/tmp/testfax.tif"

echo "Testing Real Fax Transmission"
echo "============================="
echo "Number: $REAL_NUMBER"
echo "File: $TIFF_FILE"
echo ""

# Check if TIFF file exists
if [ ! -f "$TIFF_FILE" ]; then
    echo "❌ Error: TIFF file not found at $TIFF_FILE"
    echo "Please ensure the file exists"
    exit 1
fi

echo "✅ TIFF file found ($(stat -c%s "$TIFF_FILE") bytes)"

# Upload the TIFF file
echo ""
echo "1. Uploading TIFF file..."
upload_response=$(curl -s -X POST \
    -H "Authorization: Token $TOKEN" \
    -F "file=@$TIFF_FILE" \
    "$API/api/fax/upload/")

echo "Upload response:"
echo "$upload_response" | python -m json.tool

# Extract filename
filename=$(echo "$upload_response" | python -c "import sys, json; print(json.load(sys.stdin)['filename'])" 2>/dev/null)

if [ -z "$filename" ]; then
    echo "❌ Error: Failed to upload file"
    exit 1
fi

echo "✅ Uploaded as: $filename"

# Send fax to real number
echo ""
echo "2. Sending fax to $REAL_NUMBER..."

fax_data='{
    "username": "telnyx",
    "filename": "'$filename'",
    "numbers": "'$REAL_NUMBER'",
    "is_enhanced": false
}'

echo "Request data:"
echo "$fax_data" | python -m json.tool

send_response=$(curl -s -X POST \
    -H "Authorization: Token $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$fax_data" \
    "$API/api/fax/send/")

echo ""
echo "Send response:"
echo "$send_response" | python -m json.tool 2>/dev/null || echo "$send_response"

# Extract UUID
uuid=$(echo "$send_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('uuid', ''))" 2>/dev/null)

if [ -n "$uuid" ]; then
    echo ""
    echo "✅ Fax initiated with UUID: $uuid"
    
    # Monitor status for 30 seconds
    echo ""
    echo "3. Monitoring status..."
    for i in {1..6}; do
        echo "   Check $i/6..."
        
        status_response=$(curl -s -X GET \
            -H "Authorization: Token $TOKEN" \
            "$API/api/fax/status/$uuid/")
        
        status=$(echo "$status_response" | python -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
        echo "   Status: $status"
        
        if [ "$status" == "sent" ] || [ "$status" == "failed" ]; then
            echo ""
            echo "Final status:"
            echo "$status_response" | python -m json.tool
            break
        fi
        
        sleep 5
    done
    
    # Check FreeSWITCH logs for this call
    echo ""
    echo "4. Checking FreeSWITCH activity..."
    
    job_uuid=$(echo "$send_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data['details'][0]['job_uuid'])" 2>/dev/null)
    
    if [ -n "$job_uuid" ]; then
        echo "   Job UUID: $job_uuid"
        
        # Check if call exists in FreeSWITCH
        python3 << EOF
import main.utils.esl.ESL_py3 as ESL

con = ESL.ESLconnection("127.0.0.1", "8021", "ClueCon")
if con.connected():
    res = con.api("uuid_exists", "$job_uuid")
    exists = res.getBody().strip()
    
    if exists == "true":
        print("   ✅ Call is active in FreeSWITCH")
        
        # Get call info
        res = con.api("uuid_getvar", "$job_uuid variable_current_application")
        app = res.getBody()
        print(f"   Current application: {app}")
        
    else:
        print("   ℹ️  Call completed or not found")
    
    con.disconnect()
else:
    print("   ❌ Could not connect to FreeSWITCH")
EOF
    fi
    
else
    echo "❌ Failed to get transaction UUID"
fi

echo ""
echo "📊 Final transaction list:"
curl -s -X GET \
    -H "Authorization: Token $TOKEN" \
    "$API/api/fax/list/" | python -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total transactions: {data[\"count\"]}')
for tx in data['results'][:3]:
    print(f'  {tx[\"uuid\"]} - {tx[\"status\"]} - {tx[\"recipient_number\"]}')
"

echo ""
echo "🎯 Real fax test completed!"
echo ""
echo "Check the receiving fax machine at $REAL_NUMBER"
echo "The fax should arrive within a few minutes if successful."