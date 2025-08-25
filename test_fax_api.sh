#!/bin/bash

# Fax API Test Script
# This script tests all endpoints of the Fax API

# Configuration
API_BASE="http://127.0.0.1:8585"
TOKEN="4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"
TEST_FILE="/opt/fs-service/test_document.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -e "\n${YELLOW}Testing: $description${NC}"
    echo "Endpoint: $method $endpoint"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET \
            -H "Authorization: Token $TOKEN" \
            "$API_BASE$endpoint")
    elif [ "$method" == "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Authorization: Token $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_BASE$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Authorization: Token $TOKEN" \
            "$API_BASE$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        print_success "Status: $http_code"
        if [ -n "$body" ]; then
            echo "Response: $body" | python -m json.tool 2>/dev/null || echo "$body"
        fi
    else
        print_error "Status: $http_code"
        echo "Response: $body"
    fi
    
    return $http_code
}

# Main test sequence
print_header "FAX API TEST SUITE"
echo "API Base: $API_BASE"
echo "Token: ${TOKEN:0:20}..."

# Test 1: Check if server is running
print_header "1. SERVER STATUS CHECK"
if curl -s -f "$API_BASE" > /dev/null 2>&1; then
    print_success "Server is running"
else
    print_error "Server is not running on $API_BASE"
    echo "Please start the server with: python manage.py runserver 0.0.0.0:8585"
    exit 1
fi

# Test 2: List all fax transactions
print_header "2. LIST FAX TRANSACTIONS"
test_endpoint "GET" "/api/fax/list/" "List all fax transactions"

# Test 3: Filter by direction
print_info "Testing with direction filter..."
test_endpoint "GET" "/api/fax/list/?direction=outbound" "List outbound faxes"
test_endpoint "GET" "/api/fax/list/?direction=inbound" "List inbound faxes"

# Test 4: Filter by status
print_info "Testing with status filter..."
test_endpoint "GET" "/api/fax/list/?status=sent" "List sent faxes"
test_endpoint "GET" "/api/fax/list/?status=failed" "List failed faxes"

# Test 5: Upload a file
print_header "3. FILE UPLOAD TEST"

# Create a test file if it doesn't exist
if [ ! -f "$TEST_FILE" ]; then
    echo "Creating test file..."
    cat > "$TEST_FILE" << EOF
Test Fax Document
=================
Date: $(date)
This is a test document for the fax API.

Line 1: Testing fax transmission
Line 2: Multiple recipients support
Line 3: File upload and conversion

End of document.
EOF
    print_success "Test file created: $TEST_FILE"
fi

echo -e "\n${YELLOW}Uploading test file...${NC}"
upload_response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Authorization: Token $TOKEN" \
    -F "file=@$TEST_FILE" \
    "$API_BASE/api/fax/upload/")

upload_code=$(echo "$upload_response" | tail -n 1)
upload_body=$(echo "$upload_response" | head -n -1)

if [ "$upload_code" == "201" ]; then
    print_success "File uploaded successfully"
    echo "$upload_body" | python -m json.tool
    
    # Extract filename from response
    UPLOADED_FILE=$(echo "$upload_body" | python -c "import sys, json; print(json.load(sys.stdin)['filename'])" 2>/dev/null)
    print_info "Uploaded filename: $UPLOADED_FILE"
else
    print_error "Upload failed with status: $upload_code"
    echo "$upload_body"
fi

# Test 6: Send a fax (will fail without FreeSWITCH)
print_header "4. SEND FAX TEST"

if [ -n "$UPLOADED_FILE" ]; then
    fax_data='{
        "username": "908509999999",
        "filename": "'$UPLOADED_FILE'",
        "numbers": "05319999999,05329999999",
        "is_enhanced": false
    }'
    
    echo "Sending fax with data:"
    echo "$fax_data" | python -m json.tool
    
    test_endpoint "POST" "/api/fax/send/" "Send fax to multiple recipients" "$fax_data"
else
    print_error "No file to send (upload failed)"
fi

# Test 7: Get specific transaction status
print_header "5. TRANSACTION STATUS CHECK"

# Get a UUID from the list
echo "Getting transaction list to find a UUID..."
uuid_response=$(curl -s -X GET \
    -H "Authorization: Token $TOKEN" \
    "$API_BASE/api/fax/list/")

first_uuid=$(echo "$uuid_response" | python -c "
import sys, json
data = json.load(sys.stdin)
if data['results']:
    print(data['results'][0]['uuid'])
" 2>/dev/null)

if [ -n "$first_uuid" ]; then
    print_info "Testing with UUID: $first_uuid"
    test_endpoint "GET" "/api/fax/status/$first_uuid/" "Get transaction status"
else
    print_error "No transactions found to test status endpoint"
fi

# Test 8: Test invalid requests
print_header "6. ERROR HANDLING TESTS"

print_info "Testing without authentication..."
response=$(curl -s -w "\n%{http_code}" -X GET "$API_BASE/api/fax/list/")
http_code=$(echo "$response" | tail -n 1)
if [ "$http_code" == "401" ]; then
    print_success "Correctly rejected unauthenticated request"
else
    print_error "Expected 401, got $http_code"
fi

print_info "Testing with invalid token..."
response=$(curl -s -w "\n%{http_code}" -X GET \
    -H "Authorization: Token invalid_token_12345" \
    "$API_BASE/api/fax/list/")
http_code=$(echo "$response" | tail -n 1)
if [ "$http_code" == "401" ]; then
    print_success "Correctly rejected invalid token"
else
    print_error "Expected 401, got $http_code"
fi

print_info "Testing invalid UUID..."
test_endpoint "GET" "/api/fax/status/invalid-uuid/" "Get status with invalid UUID"

# Test 9: Legacy endpoints
print_header "7. LEGACY ENDPOINT COMPATIBILITY"

test_endpoint "GET" "/api/service/fax/" "Legacy fax root endpoint"

# Test 10: Webhook endpoint (no auth required)
print_header "8. WEBHOOK ENDPOINT TEST"

webhook_data='{
    "caller_id_number": "05319999999",
    "destination_number": "908509999999",
    "fax_file": "test_received.tiff"
}'

echo -e "\n${YELLOW}Testing inbound webhook (no auth)...${NC}"
webhook_response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$webhook_data" \
    "$API_BASE/api/fax/webhook/inbound/")

webhook_code=$(echo "$webhook_response" | tail -n 1)
webhook_body=$(echo "$webhook_response" | head -n -1)

if [ "$webhook_code" == "200" ]; then
    print_success "Webhook accepted"
    echo "$webhook_body" | python -m json.tool
else
    print_error "Webhook failed: $webhook_code"
fi

# Summary
print_header "TEST SUMMARY"

# Count transactions
total_count=$(curl -s -X GET \
    -H "Authorization: Token $TOKEN" \
    "$API_BASE/api/fax/list/" | python -c "
import sys, json
print(json.load(sys.stdin)['count'])
" 2>/dev/null)

echo "Total fax transactions in database: $total_count"
echo -e "\n${GREEN}Test suite completed!${NC}"
echo -e "${YELLOW}Note: Actual fax sending requires FreeSWITCH to be running.${NC}"