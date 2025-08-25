# Fax API Test Scripts Guide

## Available Test Scripts

### 1. **quick_test.sh** - Basic API Testing
Quick one-liner commands to test all endpoints.

```bash
./quick_test.sh
```

**Features:**
- Lists all fax transactions
- Uploads a test file
- Shows example commands for all endpoints
- No complex logic, just simple curl commands

### 2. **test_fax_api.sh** - Comprehensive Test Suite
Full test suite with colored output and error handling.

```bash
./test_fax_api.sh
```

**Features:**
- Server status check
- Tests all API endpoints
- Authentication testing
- Error handling validation
- Colored output for easy reading
- Automatic test file creation
- Response validation

### 3. **load_test.sh** - Performance Testing
Creates multiple transactions to test API performance.

```bash
./load_test.sh [number_of_tests]
# Example: ./load_test.sh 50
```

**Features:**
- Bulk file uploads
- Multiple transaction creation
- Performance metrics
- Database statistics
- Automatic cleanup of test files

### 4. **monitor_fax.sh** - Real-time Monitoring
Live dashboard showing fax transactions.

```bash
./monitor_fax.sh [refresh_interval_seconds]
# Example: ./monitor_fax.sh 3
```

**Features:**
- Real-time transaction updates
- Colored status indicators
- Status breakdown statistics
- Auto-refresh every N seconds
- Shows latest 10 transactions

### 5. **cleanup_test.sh** - Database Cleanup
Removes all test data from database and filesystem.

```bash
./cleanup_test.sh
```

**Features:**
- Confirmation prompt for safety
- Deletes all fax transactions
- Removes uploaded files
- Shows deletion statistics

## Quick Test Commands

### Basic Authentication Test
```bash
curl -X GET http://127.0.0.1:8585/api/fax/list/ \
  -H 'Authorization: Token 4165e5b65875b10f38eb015ae5b9e9a0512e3cd1'
```

### Upload a File
```bash
curl -X POST http://127.0.0.1:8585/api/fax/upload/ \
  -H 'Authorization: Token 4165e5b65875b10f38eb015ae5b9e9a0512e3cd1' \
  -F 'file=@/path/to/your/file.pdf'
```

### Send a Fax
```bash
curl -X POST http://127.0.0.1:8585/api/fax/send/ \
  -H 'Authorization: Token 4165e5b65875b10f38eb015ae5b9e9a0512e3cd1' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "908509999999",
    "filename": "uploaded_file.pdf",
    "numbers": "05319999999,05329999999",
    "is_enhanced": false
  }'
```

### Check Transaction Status
```bash
curl -X GET http://127.0.0.1:8585/api/fax/status/{UUID}/ \
  -H 'Authorization: Token 4165e5b65875b10f38eb015ae5b9e9a0512e3cd1'
```

### Filter Transactions
```bash
# By status
curl -X GET 'http://127.0.0.1:8585/api/fax/list/?status=sent' \
  -H 'Authorization: Token 4165e5b65875b10f38eb015ae5b9e9a0512e3cd1'

# By direction
curl -X GET 'http://127.0.0.1:8585/api/fax/list/?direction=outbound' \
  -H 'Authorization: Token 4165e5b65875b10f38eb015ae5b9e9a0512e3cd1'
```

### Test Webhook (No Auth)
```bash
curl -X POST http://127.0.0.1:8585/api/fax/webhook/inbound/ \
  -H 'Content-Type: application/json' \
  -d '{
    "caller_id_number": "1234567890",
    "destination_number": "0987654321",
    "fax_file": "received.tiff"
  }'
```

## Testing Workflow

### 1. Initial Setup
```bash
# Start the server (if not running)
python manage.py runserver 0.0.0.0:8585 &

# Run quick test to verify everything works
./quick_test.sh
```

### 2. Comprehensive Testing
```bash
# Run full test suite
./test_fax_api.sh

# Monitor in real-time (in another terminal)
./monitor_fax.sh 2
```

### 3. Load Testing
```bash
# Create 100 test transactions
./load_test.sh 100

# Monitor the results
./monitor_fax.sh 1
```

### 4. Cleanup
```bash
# Remove all test data
./cleanup_test.sh
```

## Environment Variables

All scripts use these default values:
- **API_BASE**: `http://127.0.0.1:8585`
- **TOKEN**: `4165e5b65875b10f38eb015ae5b9e9a0512e3cd1`
- **TEST_USER**: `testuser`
- **TEST_PASSWORD**: `testpass123`

## Expected Responses

### Successful File Upload
```json
{
  "status": "OK",
  "filename": "uuid-generated-name.pdf",
  "original_name": "your-file.pdf",
  "size": 12345
}
```

### Successful Fax Send (Mock)
```json
{
  "status": "OK",
  "code": 200,
  "uuid": "transaction-uuid",
  "message": "Fax sent to 2 recipients",
  "details": [...]
}
```

### Transaction Status
```json
{
  "uuid": "transaction-uuid",
  "status": "sent",
  "direction": "outbound",
  "sender": "908509999999",
  "recipient": "05319999999",
  "queue_items": [...]
}
```

## Troubleshooting

### Server Not Running
```bash
# Check if server is running
curl http://127.0.0.1:8585/

# Start server if needed
python manage.py runserver 0.0.0.0:8585 &
```

### Authentication Errors
```bash
# Verify token is correct
python manage.py shell
>>> from rest_framework.authtoken.models import Token
>>> Token.objects.get(user__username='testuser').key
```

### File Upload Issues
```bash
# Check directory permissions
ls -la /opt/fs-service/fax_files/

# Create directories if missing
mkdir -p /opt/fs-service/fax_files/{tx,rx}
```

## Notes

1. **FreeSWITCH Integration**: Actual fax sending will fail without FreeSWITCH running. The API will create transaction records but cannot transmit faxes.

2. **File Conversion**: The system expects ImageMagick and LibreOffice for file conversion to TIFF format.

3. **Database**: Using SQLite for testing. Production should use PostgreSQL or MySQL.

4. **Performance**: The load test script can help identify performance bottlenecks.

5. **Monitoring**: Use the monitor script to watch transactions in real-time during testing.