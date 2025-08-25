# Fax API Documentation

## Overview
This is a Django-based Fax API integrated with FreeSWITCH for sending and receiving faxes. The API has been refactored to work independently without CDR pusher dependencies.

## Features
- Send fax to single or multiple recipients
- Upload files for fax transmission
- Track fax transaction status
- List all fax transactions
- Receive inbound faxes via webhook
- File format conversion (PDF, DOC, etc. to TIFF)

## API Endpoints

### 1. Send Fax
**POST** `/api/fax/send/`

Send a fax to one or multiple recipients.

**Headers:**
- `Authorization: Token YOUR_TOKEN`
- `Content-Type: application/json`

**Request Body:**
```json
{
    "username": "908509999999",
    "filename": "document.pdf",
    "numbers": "05319999999,05329999999",
    "is_enhanced": false
}
```

**Response:**
```json
{
    "status": "OK",
    "code": 200,
    "uuid": "315ded86-99e9-11e6-88e6-c7aaf2c109a7",
    "message": "Fax sent to 2 recipients",
    "details": [
        {
            "recipient": "05319999999",
            "job_uuid": "315dfd94-99e9-11e6-88e7-c7aaf2c109a7",
            "status": "initiated"
        }
    ]
}
```

### 2. Upload File
**POST** `/api/fax/upload/`

Upload a file for fax transmission.

**Headers:**
- `Authorization: Token YOUR_TOKEN`

**Form Data:**
- `file`: File to upload

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/api/fax/upload/ \
     -H 'Authorization: Token YOUR_TOKEN' \
     -F 'file=@/path/to/document.pdf'
```

**Response:**
```json
{
    "status": "OK",
    "filename": "72df3bef-ec07-4968-9959-bd6a70a2e8c8.pdf",
    "original_name": "document.pdf",
    "size": 102400
}
```

### 3. Get Fax Status
**GET** `/api/fax/status/{uuid}/`

Get the status of a specific fax transaction.

**Headers:**
- `Authorization: Token YOUR_TOKEN`

**Response:**
```json
{
    "uuid": "315ded86-99e9-11e6-88e6-c7aaf2c109a7",
    "status": "sent",
    "direction": "outbound",
    "sender": "908509999999",
    "recipient": "05319999999,05329999999",
    "created": "2024-01-01T10:00:00Z",
    "queue_items": [
        {
            "recipient": "05319999999",
            "attempts": 1,
            "processed": true,
            "job_uuid": "315dfd94-99e9-11e6-88e7-c7aaf2c109a7"
        }
    ]
}
```

### 4. List Fax Transactions
**GET** `/api/fax/list/`

List all fax transactions for the authenticated user.

**Headers:**
- `Authorization: Token YOUR_TOKEN`

**Query Parameters:**
- `direction`: Filter by direction (inbound/outbound)
- `status`: Filter by status (pending/processing/sent/received/failed)

**Response:**
```json
{
    "count": 10,
    "results": [
        {
            "uuid": "315ded86-99e9-11e6-88e6-c7aaf2c109a7",
            "direction": "outbound",
            "status": "sent",
            "sender_number": "908509999999",
            "recipient_number": "05319999999",
            "file_path": "/path/to/fax.tiff",
            "pages": 3,
            "duration": 120,
            "created_at": "2024-01-01T10:00:00Z"
        }
    ]
}
```

### 5. Inbound Fax Webhook
**POST** `/api/fax/webhook/inbound/`

Webhook endpoint for receiving inbound fax notifications from FreeSWITCH.

**No authentication required**

**Request Body:**
```json
{
    "caller_id_number": "05319999999",
    "destination_number": "908509999999",
    "fax_file": "received_fax_20240101.tiff"
}
```

## Database Models

### FaxTransaction
Stores fax transaction information:
- `uuid`: Unique identifier
- `direction`: inbound/outbound
- `status`: pending/processing/sent/received/failed
- `sender_number`: Sender's phone number
- `recipient_number`: Recipient's phone number
- `file_path`: Path to fax file
- `original_filename`: Original uploaded filename
- `converted_filename`: Converted TIFF filename
- `pages`: Number of pages
- `duration`: Transmission duration
- `error_message`: Error details if failed
- `user`: Associated Django user

### FaxQueue
Manages fax queue for multiple recipients:
- `transaction`: Related FaxTransaction
- `recipient_number`: Individual recipient
- `attempts`: Number of send attempts
- `max_attempts`: Maximum retry attempts (default: 3)
- `is_processed`: Processing status
- `job_uuid`: FreeSWITCH job UUID
- `event_name`: FreeSWITCH event name

## Configuration

### Environment Variables
Create a `.env` file with:
```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost
DEFAULTDB_URL=sqlite:///db.sqlite3
```

### FreeSWITCH Configuration
Update `/opt/fs-service/main/apps/core/vars.py`:
```python
FREESWITCH_IP_ADDRESS = "127.0.0.1"
FREESWITCH_PORT = "8021"
FREESWITCH_PASSWORD = "ClueCon"
RXFAX_DIR = "/var/spool/freeswitch/fax/rx/"
TXFAX_DIR = "/var/spool/freeswitch/fax/tx/"
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create superuser:
```bash
python manage.py createsuperuser
```

4. Generate authentication token:
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from rest_framework.authtoken.models import Token
>>> user = User.objects.get(username='your_username')
>>> token = Token.objects.create(user=user)
>>> print(token.key)
```

5. Run server:
```bash
python manage.py runserver
```

## Testing

### Test sending a fax:
```bash
# First upload a file
curl -X POST http://127.0.0.1:8000/api/fax/upload/ \
     -H 'Authorization: Token YOUR_TOKEN' \
     -F 'file=@test.pdf'

# Then send the fax
curl -X POST http://127.0.0.1:8000/api/fax/send/ \
     -H 'Authorization: Token YOUR_TOKEN' \
     -H 'Content-Type: application/json' \
     -d '{
         "username": "908509999999",
         "filename": "uploaded_filename.pdf",
         "numbers": "05319999999",
         "is_enhanced": false
     }'
```

## Notes
- The API requires FreeSWITCH to be running and accessible
- Files are automatically converted to TIFF format for fax transmission
- The system supports multiple recipient numbers (comma-separated)
- CDR pusher dependencies have been removed for simplicity
- Authentication is handled via Django REST Framework Token Authentication