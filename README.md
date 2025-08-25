# 📠 Django Fax API System

A complete, production-ready fax API system built with Django, featuring FreeSWITCH integration, Telnyx support, and a beautiful admin interface.

## 🚀 Features

### Core Functionality
- **RESTful API** for sending and receiving faxes
- **FreeSWITCH Integration** via Event Socket Library (ESL)
- **Telnyx API Integration** for DID purchasing and management
- **Multi-tenant Architecture** with complete isolation
- **Beautiful Admin Interface** with custom CSS and animations
- **Phone Number Formatting** - (XXX) XXX-XXXX throughout
- **File Support** - PDF, TIFF, PNG, JPEG, GIF, BMP

### Admin Features
- 📊 **Tenant Management** - Multi-company support with branding
- 📞 **DID Management** - Purchase numbers directly from Telnyx
- 📄 **Cover Pages** - 5 professional templates with WYSIWYG preview
- 📥 **Inbound Settings** - OCR, email delivery, auto-printing
- 📤 **Outbound Settings** - Retry logic, ECM, scheduling
- 📈 **Transaction Viewer** - Complete fax history with retry actions

### API Endpoints
- `POST /api/fax/send/` - Send faxes to multiple recipients
- `POST /api/fax/upload/` - Upload documents for transmission
- `GET /api/fax/status/{uuid}/` - Check transmission status
- `GET /api/fax/list/` - List all transactions with filtering
- `POST /api/fax/webhook/inbound/` - Receive inbound fax webhooks

## 🛠️ Tech Stack

- **Django 4.2.16** with Python 3.13
- **Django REST Framework** for API
- **FreeSWITCH** for fax transmission
- **Telnyx API** for DID management
- **PostgreSQL/SQLite** database
- **Custom CSS** with gradients and animations

## 📦 Installation

### Prerequisites
- Python 3.8+
- FreeSWITCH installed and configured
- Telnyx API key (for DID purchasing)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/fittben/django-fax-api.git
cd django-fax-api
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure settings**
```bash
# Edit main/settings.py
TELNYX_API_KEY = 'YOUR_KEY_HERE'
FREESWITCH_HOST = '127.0.0.1'
FREESWITCH_PORT = 8021
FREESWITCH_PASSWORD = 'ClueCon'
```

4. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Collect static files**
```bash
python manage.py collectstatic
```

7. **Start the server**
```bash
python manage.py runserver 0.0.0.0:8585
```

8. **Access the admin**
Navigate to `http://127.0.0.1:8585/admin/`

## 📖 Documentation

- [API Documentation](API_DOCUMENTATION.md) - Complete API reference with examples
- [Admin System Guide](ADMIN_SYSTEM_COMPLETE.md) - Admin interface features
- [FreeSWITCH Integration](FREESWITCH_INTEGRATION_STATUS.md) - ESL setup guide

## 🔌 API Usage

### Authentication
```bash
# Get token
curl -X POST http://127.0.0.1:8585/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'
```

### Send a Fax
```bash
# Upload file
curl -X POST http://127.0.0.1:8585/api/fax/upload/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@document.pdf"

# Send fax
curl -X POST http://127.0.0.1:8585/api/fax/send/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "5551234567",
    "filename": "document.pdf",
    "numbers": "5559876543"
  }'
```

## 🎨 Admin Interface

The admin interface includes:
- **Custom CSS** with gradients, shadows, and animations
- **Status badges** with color coding
- **Phone formatting** throughout
- **Action buttons** for DID purchasing
- **Cover page preview** with templates
- **Transaction history** with retry options

![Admin Interface](https://via.placeholder.com/800x400?text=Beautiful+Admin+Interface)

## 🧪 Testing

### Run Tests
```bash
# Basic API test
python test_fax_api.py

# FreeSWITCH connection test
python test_freeswitch_connection.py

# Admin features test
python test_admin.py
```

### Test Scripts
- `quick_test.sh` - Quick API test
- `test_fax_with_fs.sh` - FreeSWITCH integration test
- `load_test.sh` - Load testing script

## 📊 Features Status

| Feature | Status | Description |
|---------|--------|-------------|
| API Endpoints | ✅ | Complete REST API |
| FreeSWITCH | ✅ | ESL integration working |
| Telnyx Integration | ✅ | DID purchasing ready |
| Admin Interface | ✅ | Beautiful custom styling |
| Multi-tenant | ✅ | Complete isolation |
| Webhooks | ✅ | Inbound/outbound hooks |
| OCR Support | ✅ | Searchable PDFs |
| Email Delivery | ✅ | Fax-to-email ready |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FreeSWITCH team for the excellent telephony platform
- Telnyx for reliable DID services
- Django community for the amazing framework

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the [documentation](API_DOCUMENTATION.md)
- Review test scripts in the repository

---

**Built with ❤️ using Django and FreeSWITCH**

🤖 Generated with [Claude Code](https://claude.ai/code)