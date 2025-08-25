#!/usr/bin/env python
"""Basic API test without FreeSWITCH dependency"""

import requests
import json

BASE_URL = "http://127.0.0.1:8585"
AUTH_TOKEN = "4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"

headers = {
    "Authorization": f"Token {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

print("Testing Fax API Basic Functionality")
print("====================================\n")

# Test 1: List faxes (should be empty initially)
print("1. Testing List Faxes endpoint...")
response = requests.get(f"{BASE_URL}/api/fax/list/", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ Success: Found {data['count']} fax transactions")
else:
    print(f"   ✗ Error: {response.status_code} - {response.text}")

# Test 2: Upload a file
print("\n2. Testing File Upload endpoint...")
with open('/opt/fs-service/test_document.txt', 'rb') as f:
    files = {'file': f}
    headers_upload = {"Authorization": f"Token {AUTH_TOKEN}"}
    response = requests.post(f"{BASE_URL}/api/fax/upload/", files=files, headers=headers_upload)
    
if response.status_code == 201:
    data = response.json()
    uploaded_filename = data['filename']
    print(f"   ✓ Success: File uploaded as {uploaded_filename}")
    print(f"     Original name: {data['original_name']}")
    print(f"     Size: {data['size']} bytes")
else:
    print(f"   ✗ Error: {response.status_code} - {response.text}")
    uploaded_filename = None

# Test 3: Check if we can access the legacy fax endpoint
print("\n3. Testing Legacy Fax endpoint...")
response = requests.get(f"{BASE_URL}/api/service/fax/", headers=headers)
if response.status_code == 200:
    print(f"   ✓ Legacy endpoint accessible")
else:
    print(f"   ✗ Legacy endpoint returned: {response.status_code}")

# Test 4: Check new fax endpoints
print("\n4. Testing New Fax API endpoints...")
endpoints = [
    ("/api/fax/list/", "GET"),
    ("/api/fax/send/", "GET"),  # Should return 405 Method Not Allowed for GET
]

for endpoint, method in endpoints:
    if method == "GET":
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    print(f"   {endpoint}: {response.status_code} {response.reason}")

print("\n" + "="*40)
print("Basic API tests completed!")
print(f"Uploaded file available at: /opt/fs-service/fax_files/tx/{uploaded_filename if uploaded_filename else 'N/A'}")