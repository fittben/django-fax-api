#!/bin/bash

# Quick Fax API Test Script
# Simple one-liners for testing

API="http://127.0.0.1:8585"
TOKEN="4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"

echo "Quick Fax API Tests"
echo "==================="
echo ""
echo "1. List all faxes:"
echo "curl -X GET $API/api/fax/list/ -H 'Authorization: Token $TOKEN' | python -m json.tool"
curl -X GET $API/api/fax/list/ -H "Authorization: Token $TOKEN" | python -m json.tool

echo -e "\n2. Upload a file:"
echo "curl -X POST $API/api/fax/upload/ -H 'Authorization: Token $TOKEN' -F 'file=@test_document.txt'"
curl -X POST $API/api/fax/upload/ -H "Authorization: Token $TOKEN" -F "file=@test_document.txt"

echo -e "\n\n3. Send a fax (replace FILENAME with actual uploaded filename):"
echo 'curl -X POST $API/api/fax/send/ -H "Authorization: Token $TOKEN" -H "Content-Type: application/json" -d '"'"'{"username": "908509999999", "filename": "FILENAME", "numbers": "05319999999", "is_enhanced": false}'"'"

echo -e "\n4. Get transaction status (replace UUID):"
echo "curl -X GET $API/api/fax/status/UUID/ -H 'Authorization: Token $TOKEN' | python -m json.tool"

echo -e "\n5. Filter by status:"
echo "curl -X GET '$API/api/fax/list/?status=sent' -H 'Authorization: Token $TOKEN' | python -m json.tool"

echo -e "\n6. Test webhook (no auth needed):"
echo 'curl -X POST $API/api/fax/webhook/inbound/ -H "Content-Type: application/json" -d '"'"'{"caller_id_number": "1234567890", "destination_number": "0987654321", "fax_file": "received.tiff"}'"'"