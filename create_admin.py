#!/usr/bin/env python
"""
Create or reset admin user for Django admin panel
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth.models import User

# Admin credentials
username = 'admin'
email = 'admin@example.com'
password = 'admin123'

try:
    # Try to get existing user
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ Password reset for existing user '{username}'")
except User.DoesNotExist:
    # Create new superuser
    user = User.objects.create_superuser(username, email, password)
    print(f"✅ Created new superuser '{username}'")

print(f"\n🔐 Django Admin Login:")
print(f"URL: http://127.0.0.1:8585/admin/")
print(f"Username: {username}")
print(f"Password: {password}")

# Also show existing superusers
print(f"\n📋 All superusers:")
for u in User.objects.filter(is_superuser=True):
    print(f"  - {u.username} ({u.email})")