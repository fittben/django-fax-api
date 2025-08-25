import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create superuser
username = 'testuser'
email = 'test@example.com'
password = 'testpass123'

try:
    user = User.objects.get(username=username)
    print(f"User '{username}' already exists")
except User.DoesNotExist:
    user = User.objects.create_superuser(username, email, password)
    print(f"Created superuser '{username}'")

# Create or get token
token, created = Token.objects.get_or_create(user=user)

print(f"\nAuthentication Token: {token.key}")
print(f"Username: {username}")
print(f"Password: {password}")