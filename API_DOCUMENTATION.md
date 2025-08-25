# 📠 Fax API Documentation

## Overview

The Fax API provides a comprehensive RESTful interface for sending and receiving faxes, managing fax transactions, and integrating with FreeSWITCH and external providers like Telnyx. The API supports multi-tenant architecture, cover pages, webhooks, and various file formats.

## Base URL
```
http://127.0.0.1:8585/api/fax/
```

## Authentication

All API endpoints require authentication using Django REST Framework Token Authentication.

### Obtaining a Token

```bash
curl -X POST http://127.0.0.1:8585/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Using the Token

Include the token in the Authorization header for all API requests:

```bash
-H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

## API Endpoints

### 1. Send Fax

**Endpoint:** `POST /api/fax/send/`

Send a fax to one or multiple recipients.

**Request Body:**
```json
{
  "username": "908509999999",
  "filename": "document.pdf",
  "numbers": "05319999999,05329999999",
  "is_enhanced": false
}
```

**Parameters:**
- `username` (string, required): Sender's phone number (10 digits)
- `filename` (string, required): Name of the file to send (must be uploaded first)
- `numbers` (string, required): Comma-separated list of recipient numbers
- `is_enhanced` (boolean, optional): Use enhanced fax mode (default: false)

**Example Request:**
```bash
curl -X POST http://127.0.0.1:8585/api/fax/send/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "5551234567",
    "filename": "contract.pdf",
    "numbers": "5559876543,5555551234",
    "is_enhanced": false
  }'
```

**Success Response (200 OK):**
```json
{
  "status": "OK",
  "code": 200,
  "uuid": "3bca1e12-f50e-4bc2-a667-c67956c051b0",
  "message": "Fax queued successfully",
  "details": {
    "recipients": 2,
    "queued": ["5559876543", "5555551234"]
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "Error",
  "code": 400,
  "message": "File not found"
}
```

---

### 2. Upload File

**Endpoint:** `POST /api/fax/upload/`

Upload a document for fax transmission. Supports PDF, TIFF, and common image formats.

**Request:** Multipart form data with file

**Example Request:**
```bash
curl -X POST http://127.0.0.1:8585/api/fax/upload/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

**Success Response (201 Created):**
```json
{
  "status": "OK",
  "filename": "a4b5c6d7-e8f9-1234-5678-90abcdef1234.pdf",
  "original_name": "document.pdf",
  "size": 245678
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "No file provided"
}
```

**Supported File Types:**
- PDF (.pdf)
- TIFF (.tif, .tiff)
- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- BMP (.bmp)

---

### 3. Get Fax Status

**Endpoint:** `GET /api/fax/status/{uuid}/`

Retrieve the status of a specific fax transaction.

**URL Parameters:**
- `uuid` (required): Transaction UUID

**Example Request:**
```bash
curl -X GET http://127.0.0.1:8585/api/fax/status/3bca1e12-f50e-4bc2-a667-c67956c051b0/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "uuid": "3bca1e12-f50e-4bc2-a667-c67956c051b0",
  "direction": "outbound",
  "status": "sent",
  "sender_number": "5551234567",
  "recipient_number": "5559876543",
  "pages": 3,
  "duration": 45,
  "created_at": "2025-08-24T10:30:00Z",
  "updated_at": "2025-08-24T10:31:45Z",
  "queue_items": [
    {
      "recipient": "5559876543",
      "attempts": 1,
      "is_processed": true,
      "processed_at": "2025-08-24T10:31:45Z"
    }
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Transaction not found"
}
```

**Status Values:**
- `pending`: Fax is queued for transmission
- `processing`: Fax is being transmitted
- `sent`: Fax successfully sent
- `received`: Inbound fax received
- `failed`: Transmission failed

---

### 4. List Fax Transactions

**Endpoint:** `GET /api/fax/list/`

List all fax transactions for the authenticated user.

**Query Parameters:**
- `direction` (optional): Filter by direction (`inbound` or `outbound`)
- `status` (optional): Filter by status (`pending`, `processing`, `sent`, `received`, `failed`)

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8585/api/fax/list/?direction=outbound&status=sent" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "count": 25,
  "results": [
    {
      "uuid": "3bca1e12-f50e-4bc2-a667-c67956c051b0",
      "direction": "outbound",
      "status": "sent",
      "sender_number": "5551234567",
      "recipient_number": "5559876543",
      "pages": 3,
      "duration": 45,
      "created_at": "2025-08-24T10:30:00Z",
      "updated_at": "2025-08-24T10:31:45Z"
    },
    {
      "uuid": "7def8901-2345-6789-abcd-ef0123456789",
      "direction": "outbound",
      "status": "sent",
      "sender_number": "5551234567",
      "recipient_number": "5555551234",
      "pages": 1,
      "duration": 20,
      "created_at": "2025-08-24T09:15:00Z",
      "updated_at": "2025-08-24T09:15:20Z"
    }
  ]
}
```

---

## Webhook Integration

### Inbound Fax Webhook

**Endpoint:** `POST /api/fax/webhook/inbound/`

Receive notifications for incoming faxes from FreeSWITCH or external providers.

**Headers:**
- `X-Webhook-Signature`: HMAC signature for request validation (optional but recommended)

**Request Body (FreeSWITCH):**
```json
{
  "event": "fax.received",
  "uuid": "abc123-def456",
  "from": "+15551234567",
  "to": "+15559876543",
  "pages": 2,
  "duration": 30,
  "file_path": "/var/spool/fax/rxfax/abc123.tif",
  "timestamp": "2025-08-24T10:30:00Z"
}
```

**Request Body (Telnyx):**
```json
{
  "data": {
    "event_type": "fax.received",
    "id": "fax_123456",
    "connection_id": "conn_789",
    "from": "+15551234567",
    "to": "+15559876543",
    "status": "received",
    "page_count": 2,
    "media_url": "https://api.telnyx.com/v2/faxes/fax_123456/media",
    "created_at": "2025-08-24T10:30:00Z"
  }
}
```

**Success Response (200 OK):**
```json
{
  "status": "accepted",
  "message": "Fax received and queued for processing"
}
```

---

## FreeSWITCH Integration

### ESL (Event Socket Library) Connection

The API integrates with FreeSWITCH through the Event Socket Library for real-time fax transmission.

**Configuration:**
```python
# main/settings.py
FREESWITCH_HOST = '127.0.0.1'
FREESWITCH_PORT = 8021
FREESWITCH_PASSWORD = 'ClueCon'
```

### Fax Transmission Flow

1. **File Upload**: Document uploaded via `/api/fax/upload/`
2. **Conversion**: Convert to TIFF format if needed
3. **Queue**: Add to transmission queue
4. **ESL Command**: Send via FreeSWITCH originate command
5. **Status Updates**: Track progress through ESL events
6. **Completion**: Update database and notify via webhook

**FreeSWITCH Originate Command:**
```
originate {fax_enable_t38=true,fax_enable_t38_request=true}sofia/gateway/telnyx/+15559876543 &txfax(/var/spool/fax/txfax/document.tif)
```

---

## Telnyx Integration

### DID Management

Purchase and manage DIDs through Telnyx API.

**Search Available Numbers:**
```python
from main.apps.fax.telnyx_integration import TelnyxDIDManager

manager = TelnyxDIDManager(api_key='YOUR_KEY')
numbers = manager.search_available_numbers(
    area_code='212',
    features=['fax', 'voice']
)
```

**Purchase Number:**
```python
did = manager.purchase_number(
    phone_number='+12125551234',
    tenant=tenant_obj
)
```

### Send Fax via Telnyx

```python
fax_id = manager.send_fax(
    from_number='2125551234',
    to_number='2125559999',
    media_url='https://example.com/document.pdf'
)
```

---

## Error Handling

All API endpoints use standard HTTP status codes and return consistent error responses.

### Common Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 201 | Created (file uploaded) |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found (resource doesn't exist) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "error": "Human-readable error message",
  "details": {
    "field_name": ["Specific error for this field"]
  },
  "code": "ERROR_CODE"
}
```

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Send Fax**: 100 requests per hour per user
- **Upload File**: 50 files per hour per user
- **Status Check**: 1000 requests per hour per user
- **List Transactions**: 500 requests per hour per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1693824000
```

---

## File Management

### Storage Locations

- **Outbound Faxes**: `/var/spool/fax/txfax/`
- **Inbound Faxes**: `/var/spool/fax/rxfax/`
- **Converted Files**: `/var/spool/fax/converted/`
- **Cover Pages**: `/var/spool/fax/covers/`

### File Retention

- **Successful Faxes**: Retained for 30 days
- **Failed Faxes**: Retained for 7 days
- **Cover Pages**: Cached indefinitely

---

## Multi-Tenant Support

The API supports multi-tenant architecture with tenant isolation.

### Tenant Headers

Include tenant information in requests:
```bash
-H "X-Tenant-ID: tenant_123"
```

### Tenant-Specific Features

- Custom cover pages per tenant
- Separate DID pools
- Individual billing and usage tracking
- Customized routing rules
- Branded email notifications

---

## Testing

### Test Mode

Enable test mode to simulate fax transmission without actual sending:

```bash
curl -X POST http://127.0.0.1:8585/api/fax/send/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "X-Test-Mode: true" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "5551234567",
    "filename": "test.pdf",
    "numbers": "5559876543"
  }'
```

### Sample Test Numbers

- **Always Success**: 5550001111
- **Always Busy**: 5550002222
- **Always No Answer**: 5550003333
- **Always Failed**: 5550004444

---

## Code Examples

### Python

```python
import requests

class FaxAPIClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
    
    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f'{self.base_url}/upload/',
                headers={'Authorization': self.headers['Authorization']},
                files=files
            )
        return response.json()
    
    def send_fax(self, sender, filename, recipients):
        data = {
            'username': sender,
            'filename': filename,
            'numbers': ','.join(recipients)
        }
        response = requests.post(
            f'{self.base_url}/send/',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def get_status(self, uuid):
        response = requests.get(
            f'{self.base_url}/status/{uuid}/',
            headers=self.headers
        )
        return response.json()

# Usage
client = FaxAPIClient('http://127.0.0.1:8585/api/fax', 'YOUR_TOKEN')

# Upload file
upload_result = client.upload_file('/path/to/document.pdf')
filename = upload_result['filename']

# Send fax
send_result = client.send_fax('5551234567', filename, ['5559876543'])
uuid = send_result['uuid']

# Check status
status = client.get_status(uuid)
print(f"Fax status: {status['status']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

class FaxAPIClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async uploadFile(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));

    const response = await axios.post(
      `${this.baseUrl}/upload/`,
      form,
      {
        headers: {
          'Authorization': `Token ${this.token}`,
          ...form.getHeaders()
        }
      }
    );
    return response.data;
  }

  async sendFax(sender, filename, recipients) {
    const response = await axios.post(
      `${this.baseUrl}/send/`,
      {
        username: sender,
        filename: filename,
        numbers: recipients.join(',')
      },
      {
        headers: {
          'Authorization': `Token ${this.token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  }

  async getStatus(uuid) {
    const response = await axios.get(
      `${this.baseUrl}/status/${uuid}/`,
      {
        headers: {
          'Authorization': `Token ${this.token}`
        }
      }
    );
    return response.data;
  }
}

// Usage
async function main() {
  const client = new FaxAPIClient('http://127.0.0.1:8585/api/fax', 'YOUR_TOKEN');

  // Upload file
  const uploadResult = await client.uploadFile('/path/to/document.pdf');
  const filename = uploadResult.filename;

  // Send fax
  const sendResult = await client.sendFax('5551234567', filename, ['5559876543']);
  const uuid = sendResult.uuid;

  // Check status
  const status = await client.getStatus(uuid);
  console.log(`Fax status: ${status.status}`);
}

main().catch(console.error);
```

### cURL Examples

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST http://127.0.0.1:8585/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

# 2. Upload a file
FILENAME=$(curl -s -X POST http://127.0.0.1:8585/api/fax/upload/ \
  -H "Authorization: Token $TOKEN" \
  -F "file=@document.pdf" \
  | jq -r '.filename')

# 3. Send fax
UUID=$(curl -s -X POST http://127.0.0.1:8585/api/fax/send/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"5551234567\",
    \"filename\": \"$FILENAME\",
    \"numbers\": \"5559876543\"
  }" | jq -r '.uuid')

# 4. Check status
curl -X GET http://127.0.0.1:8585/api/fax/status/$UUID/ \
  -H "Authorization: Token $TOKEN" | jq

# 5. List all faxes
curl -X GET http://127.0.0.1:8585/api/fax/list/ \
  -H "Authorization: Token $TOKEN" | jq
```

---

## Support & Resources

- **Admin Interface**: http://127.0.0.1:8585/admin/
- **API Base URL**: http://127.0.0.1:8585/api/fax/
- **FreeSWITCH Console**: Port 8021
- **Logs**: `/opt/fs-service/logs/`

### Troubleshooting

**Common Issues:**

1. **File Upload Fails**
   - Check file size limits (default: 10MB)
   - Verify supported file format
   - Ensure proper permissions on upload directory

2. **Fax Transmission Fails**
   - Verify FreeSWITCH connection
   - Check gateway configuration
   - Review ESL logs for errors

3. **Authentication Errors**
   - Ensure token is valid and not expired
   - Check user permissions
   - Verify tenant assignment

### Contact

For technical support or API access, contact your system administrator.