#!/usr/bin/env python
"""
Test script for Fax API
"""
import requests
import json
import sys
import os

# Configuration
BASE_URL = "http://127.0.0.1:8585"
AUTH_TOKEN = "4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"  # Replace with actual token

# Headers
headers = {
    "Authorization": f"Token {AUTH_TOKEN}",
    "Content-Type": "application/json"
}


def test_upload_file(file_path):
    """Test file upload endpoint"""
    print("\n=== Testing File Upload ===")
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return None
    
    url = f"{BASE_URL}/api/fax/upload/"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        headers_upload = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(url, files=files, headers=headers_upload)
    
    if response.status_code == 201:
        result = response.json()
        print(f"Success: File uploaded as {result['filename']}")
        return result['filename']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def test_send_fax(username, filename, numbers, is_enhanced=False):
    """Test fax sending endpoint"""
    print("\n=== Testing Send Fax ===")
    
    url = f"{BASE_URL}/api/fax/send/"
    data = {
        "username": username,
        "filename": filename,
        "numbers": numbers,
        "is_enhanced": is_enhanced
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: Fax queued with UUID {result['uuid']}")
        return result['uuid']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def test_get_status(uuid):
    """Test fax status endpoint"""
    print("\n=== Testing Get Status ===")
    
    url = f"{BASE_URL}/api/fax/status/{uuid}/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Direction: {result['direction']}")
        print(f"Sender: {result['sender']}")
        print(f"Recipient: {result['recipient']}")
        return result
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def test_list_faxes(direction=None, status=None):
    """Test fax list endpoint"""
    print("\n=== Testing List Faxes ===")
    
    url = f"{BASE_URL}/api/fax/list/"
    params = {}
    
    if direction:
        params['direction'] = direction
    if status:
        params['status'] = status
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Found {result['count']} fax transactions")
        for fax in result['results'][:5]:  # Show first 5
            print(f"  - UUID: {fax['uuid']}, Status: {fax['status']}, Direction: {fax['direction']}")
        return result
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def main():
    """Main test function"""
    print("FAX API Test Suite")
    print("==================")
    
    # Check if token is set
    if AUTH_TOKEN == "YOUR_AUTH_TOKEN_HERE":
        print("\nError: Please set your AUTH_TOKEN in this script")
        print("You can get a token by running:")
        print("  python manage.py shell")
        print("  >>> from rest_framework.authtoken.models import Token")
        print("  >>> from django.contrib.auth.models import User")
        print("  >>> user = User.objects.get(username='your_username')")
        print("  >>> token, created = Token.objects.get_or_create(user=user)")
        print("  >>> print(token.key)")
        return
    
    # Test scenarios
    print("\nStarting tests...")
    
    # 1. List existing faxes
    test_list_faxes()
    
    # 2. Upload a test file (if provided)
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        uploaded_filename = test_upload_file(test_file)
        
        if uploaded_filename:
            # 3. Send a fax
            test_numbers = "05319999999"  # Replace with test number
            test_username = "908509999999"  # Replace with your gateway username
            
            fax_uuid = test_send_fax(test_username, uploaded_filename, test_numbers)
            
            if fax_uuid:
                # 4. Check status
                test_get_status(fax_uuid)
    else:
        print("\nTo test file upload and sending, run:")
        print(f"  python {sys.argv[0]} /path/to/test/file.pdf")
    
    print("\n=== Tests Complete ===")


if __name__ == "__main__":
    main()