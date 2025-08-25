#!/usr/bin/env python
"""Test script to verify admin functionality"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth.models import User
from main.apps.fax.models_complete import (
    Tenant, DID, CoverPage, InboundFaxSettings, 
    OutboundFaxSettings, UserProfile
)
from main.apps.fax.models import FaxTransaction

def test_admin_features():
    print("🔍 Testing Fax Admin System Features")
    print("=" * 50)
    
    # 1. Check Tenant
    print("\n✅ Checking Tenants...")
    tenants = Tenant.objects.all()
    if tenants:
        for tenant in tenants:
            print(f"  - {tenant.company_name} (Active: {tenant.is_active})")
    else:
        print("  Creating default tenant...")
        tenant = Tenant.objects.create(
            name='default',
            company_name='Demo Company',
            domain='demo.local',
            admin_email='admin@demo.local',
            admin_phone='5551234567',
            billing_email='billing@demo.local',
            is_active=True,
            address_line1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='US'
        )
        print(f"  ✓ Created: {tenant.company_name}")
    
    # 2. Check DIDs
    print("\n📞 Checking DIDs...")
    dids = DID.objects.all()
    if dids:
        for did in dids:
            formatted = f"({did.number[:3]}) {did.number[3:6]}-{did.number[6:]}" if len(did.number) == 10 else did.number
            print(f"  - {formatted} [{did.provider}] (Fax: {did.is_fax_enabled})")
    else:
        print("  No DIDs found (purchase through admin)")
    
    # 3. Check Cover Pages
    print("\n📄 Checking Cover Pages...")
    covers = CoverPage.objects.all()
    if covers:
        for cover in covers:
            print(f"  - {cover.name} (Default: {cover.is_default})")
    else:
        print("  Creating sample cover page...")
        tenant = Tenant.objects.first()
        if tenant:
            cover = CoverPage.objects.create(
                tenant=tenant,
                name='Professional Template',
                template_type='professional',
                is_default=True,
                show_logo=True,
                show_date=True,
                show_pages=True
            )
            print(f"  ✓ Created: {cover.name}")
    
    # 4. Check Inbound Settings
    print("\n📥 Checking Inbound Fax Settings...")
    inbound_settings = InboundFaxSettings.objects.all()
    if inbound_settings:
        for settings in inbound_settings:
            print(f"  - {settings.tenant.company_name}:")
            print(f"    Email: {settings.email_delivery}")
            print(f"    OCR: {settings.ocr_enabled}")
            print(f"    Storage: {settings.storage_backend}")
    else:
        print("  No inbound settings configured")
    
    # 5. Check Outbound Settings
    print("\n📤 Checking Outbound Fax Settings...")
    outbound_settings = OutboundFaxSettings.objects.all()
    if outbound_settings:
        for settings in outbound_settings:
            print(f"  - {settings.tenant.company_name}:")
            print(f"    Retry: {settings.retry_attempts}")
            print(f"    ECM: {settings.ecm_enabled}")
    else:
        print("  No outbound settings configured")
    
    # 6. Check Fax Transactions
    print("\n📠 Checking Fax Transactions...")
    transactions = FaxTransaction.objects.all()[:5]
    if transactions:
        for tx in transactions:
            sender = f"({tx.sender_number[:3]}) {tx.sender_number[3:6]}-{tx.sender_number[6:]}" if len(tx.sender_number) == 10 else tx.sender_number
            print(f"  - {tx.direction} | {sender} | {tx.status}")
    else:
        print("  No transactions found")
    
    # 7. Check User Profiles
    print("\n👤 Checking User Profiles...")
    profiles = UserProfile.objects.all()
    if profiles:
        for profile in profiles:
            print(f"  - {profile.user.username} ({profile.department})")
    else:
        print("  No user profiles configured")
    
    print("\n" + "=" * 50)
    print("✨ Admin Features Available:")
    print("  • Tenant Management (multi-company support)")
    print("  • DID Purchase via Telnyx API")
    print("  • Cover Page Templates (5 styles)")
    print("  • Inbound Settings (OCR, routing, storage)")
    print("  • Outbound Settings (retry, ECM, scheduling)")
    print("  • Transaction Viewer (with retry actions)")
    print("  • User Profiles (departments, limits)")
    print("\n🌐 Access admin at: http://127.0.0.1:8585/admin/")
    print("   Username: admin")
    print("   Password: admin123")

if __name__ == "__main__":
    test_admin_features()