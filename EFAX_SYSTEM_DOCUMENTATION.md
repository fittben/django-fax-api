# eFax-like System Implementation Documentation

## 🎯 System Overview

A complete eFax.com-like fax service has been implemented with:
- **TX (Transmit)** - Outbound fax processing with post-transmission handling
- **RX (Receive)** - Inbound fax processing with automatic routing
- **Database** - Comprehensive tracking of all fax transactions
- **Email Integration** - Automatic fax-to-email delivery
- **Webhook System** - Real-time notifications to external systems
- **Account Management** - User accounts with usage tracking and billing

---

## 📁 File Structure

```
/opt/fs-service/
├── main/apps/fax/
│   ├── models_extended.py      # Extended database models
│   ├── rx_processor.py         # Inbound fax processor
│   ├── tx_processor.py         # Outbound fax processor
│   └── [existing files]
├── Notes/freeswitch-receive-fax/
│   ├── process-fax-events.py   # FreeSWITCH event handler
│   └── dialplan-fax.xml        # FreeSWITCH dialplan config
└── fax_files/
    ├── rx/                      # Received faxes
    ├── tx/                      # Transmitted faxes
    └── archive/                 # Archived faxes
```

---

## 🗄️ Database Models

### 1. **FaxAccount**
User accounts with fax numbers and plans:
- Unique fax number per account
- Plan types: Basic, Plus, Pro, Enterprise
- Monthly page limits tracking
- Email notification settings

### 2. **FaxTransmission**
Complete fax transaction records:
- Direction (inbound/outbound)
- Status tracking (queued → transmitting → completed/failed)
- Phone numbers and names
- File information with SHA256 hashing
- Transmission details (duration, pages, baud rate)
- Cost calculation
- Error tracking with retry support

### 3. **FaxPage**
Individual page tracking:
- Page-by-page transmission status
- Quality metrics
- Transmission timing

### 4. **FaxContact**
Address book functionality:
- Frequently used numbers
- Usage statistics
- Auto-learning from successful transmissions

### 5. **FaxWebhook**
External notification system:
- Configurable webhooks per account
- Event triggers (received/sent/failed)
- HMAC signature security
- Failure tracking and retry

### 6. **FaxLog**
Detailed logging:
- Debug/Info/Warning/Error levels
- JSON details storage
- Linked to transmissions

---

## 📥 RX (Receive) Fax Processing

### Workflow:
1. **FreeSWITCH receives call** → Detects fax tones
2. **Saves TIFF file** → `/opt/fs-service/fax_files/rx/`
3. **Triggers Python processor** on hangup
4. **RXFaxProcessor**:
   - Identifies receiving account by number
   - Creates transmission record
   - Extracts individual pages
   - Converts to PDF if configured
   - Sends email notification
   - Triggers webhooks
   - Updates usage statistics

### Features:
- ✅ Automatic fax detection
- ✅ Multi-page TIFF handling
- ✅ PDF conversion
- ✅ Email delivery
- ✅ Webhook notifications
- ✅ Usage tracking

---

## 📤 TX (Transmit) Fax Processing

### Workflow:
1. **API receives send request**
2. **File uploaded and queued**
3. **FreeSWITCH initiates call**
4. **On completion → TXFaxProcessor**:
   - Updates transmission status
   - Logs transmission details
   - Updates contact usage
   - Calculates costs
   - Sends confirmation email
   - Triggers webhooks
   - Handles automatic retry
   - Archives successful transmissions

### Features:
- ✅ Status tracking (queued/dialing/transmitting/completed)
- ✅ Automatic retry with exponential backoff
- ✅ Cost calculation by destination
- ✅ Contact auto-learning
- ✅ Email confirmations
- ✅ Webhook notifications
- ✅ File archiving

---

## 📧 Email Integration

### Inbound Faxes:
```python
Subject: Fax Received from {sender_number}
Attachment: fax_{uuid}.pdf
```

### Outbound Confirmations:
```python
Subject: Fax Sent Successfully to {recipient_number}
Body: Status, pages, duration, cost
```

### Configuration:
- Format choice: PDF or TIFF
- Per-account email settings
- Automatic delivery on receipt

---

## 🔗 Webhook System

### Events:
- `fax.received` - Inbound fax completed
- `fax.sent` - Outbound fax successful
- `fax.failed` - Transmission failed

### Security:
- HMAC-SHA256 signatures
- Secret key per webhook
- Header: `X-Fax-Signature`

### Payload Example:
```json
{
  "event": "fax.received",
  "timestamp": "2025-08-24T15:00:00Z",
  "data": {
    "uuid": "abc-123",
    "from": "18884732963",
    "to": "15551234567",
    "pages": 3,
    "duration": 45,
    "status": "completed"
  }
}
```

---

## 🔧 FreeSWITCH Configuration

### Dialplan Setup:
1. Copy `dialplan-fax.xml` to `/usr/local/freeswitch/conf/dialplan/public/`
2. Add dedicated fax numbers to the dialplan
3. Reload FreeSWITCH XML: `fs_cli -x "reloadxml"`

### Fax Detection:
- Automatic CNG tone detection
- T.38 support enabled
- ECM (Error Correction Mode) configurable

### Post-Processing:
- Python script triggered on hangup
- Environment variables passed from FreeSWITCH
- Automatic database updates

---

## 💰 Billing & Usage

### Plans:
- **Basic**: 150 pages/month
- **Plus**: 300 pages/month  
- **Pro**: 500 pages/month
- **Enterprise**: Unlimited

### Cost Calculation:
- US/Canada: $0.10/page
- UK: $0.15/page
- International: $0.20/page

### Usage Tracking:
- Monthly page counters
- Automatic reset on billing cycle
- Per-transmission cost tracking

---

## 🚀 API Endpoints

### Send Fax:
```bash
POST /api/fax/send/
{
  "username": "fax_number",
  "filename": "document.pdf",
  "numbers": "18884732963",
  "is_enhanced": false
}
```

### Check Status:
```bash
GET /api/fax/status/{uuid}/
```

### List Transmissions:
```bash
GET /api/fax/list/?direction=inbound&status=completed
```

### Webhook Management:
```bash
POST /api/fax/webhooks/
{
  "url": "https://your-site.com/webhook",
  "on_received": true,
  "on_sent": true,
  "on_failed": true
}
```

---

## 📊 Testing

### Test Inbound Fax:
```bash
# Simulate inbound fax
python /opt/fs-service/Notes/freeswitch-receive-fax/process-fax-events.py
```

### Test Outbound Processing:
```python
from main.apps.fax.tx_processor import TXFaxProcessor
processor = TXFaxProcessor(transmission_uuid)
processor.process_completion(freeswitch_data)
```

---

## 🎯 Current Status

### ✅ Completed:
- RX fax processing with email delivery
- TX fax post-processing with confirmations
- Comprehensive database models
- Webhook notification system
- Email integration
- FreeSWITCH event handling
- Cost calculation
- Usage tracking
- Contact management
- File archiving

### 🔄 Ready for Production:
The system is fully functional and ready to:
1. Receive faxes on dedicated numbers
2. Process and deliver via email
3. Send faxes with tracking
4. Handle retries automatically
5. Calculate costs
6. Trigger webhooks
7. Maintain complete audit trail

---

## 📝 Notes

This implementation provides a complete eFax.com-like service with:
- **Enterprise features**: Webhooks, API access, usage tracking
- **Reliability**: Automatic retries, error handling, logging
- **Scalability**: Database indexes, file archiving, queue support
- **Security**: HMAC webhooks, file hashing, audit trails
- **Integration**: Email delivery, webhook notifications, REST API

The system is production-ready and can handle both sending and receiving faxes with comprehensive tracking and notification capabilities.