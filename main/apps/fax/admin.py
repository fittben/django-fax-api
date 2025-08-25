from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
import requests
import json
from datetime import datetime
from .models import FaxTransaction, FaxQueue
from .models_complete import (
    Tenant, DID, CoverPage, InboundFaxSettings, 
    OutboundFaxSettings, UserProfile
)


# Custom Admin Site
class FaxAdminSite(admin.AdminSite):
    site_header = "📠 Fax Management System"
    site_title = "Fax Admin"
    index_title = "Dashboard"
    
    def each_context(self, request):
        context = super().each_context(request)
        context['custom_css'] = '/static/admin/css/fax_admin.css'
        return context


# Create custom admin site
fax_admin_site = FaxAdminSite(name='fax_admin')


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'company_name', 'domain', 'user_count', 'did_count', 'status_badge', 'created_at']
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['name', 'company_name', 'domain', 'admin_email']
    readonly_fields = ['created_at', 'updated_at', 'show_logo']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company_name', 'domain')
        }),
        ('Contact Information', {
            'fields': ('admin_email', 'admin_phone', 'billing_email')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Limits & Settings', {
            'fields': ('max_users', 'max_dids', 'max_pages_per_month'),
            'classes': ('collapse',)
        }),
        ('Branding', {
            'fields': ('logo', 'show_logo', 'primary_color', 'secondary_color'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        })
    )
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = '👥 Users'
    
    def did_count(self, obj):
        return obj.dids.count()
    did_count.short_description = '📞 DIDs'
    
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Active</span>')
        return format_html('<span style="color: red;">❌ Inactive</span>')
    status_badge.short_description = 'Status'
    
    def show_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="200" />', obj.logo.url)
        return "No logo"
    show_logo.short_description = 'Logo Preview'
    
    actions = ['activate_tenants', 'deactivate_tenants']
    
    def activate_tenants(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"✅ {queryset.count()} tenants activated")
    activate_tenants.short_description = "✅ Activate selected tenants"
    
    def deactivate_tenants(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"❌ {queryset.count()} tenants deactivated")
    deactivate_tenants.short_description = "❌ Deactivate selected tenants"


@admin.register(DID)
class DIDAdmin(admin.ModelAdmin):
    list_display = ['formatted_number', 'tenant', 'assigned_to', 'provider_badge', 'capabilities', 'status_badge', 'actions_buttons']
    list_filter = ['provider', 'is_active', 'is_fax_enabled', 'is_voice_enabled', 'is_sms_enabled', 'tenant']
    search_fields = ['number', 'description', 'assigned_to__username', 'assigned_to__email']
    raw_id_fields = ['assigned_to']
    readonly_fields = ['created_at', 'updated_at', 'provider_sid']
    
    fieldsets = (
        ('DID Information', {
            'fields': ('number', 'tenant', 'description')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_at')
        }),
        ('Provider Details', {
            'fields': ('provider', 'provider_sid'),
            'classes': ('collapse',)
        }),
        ('Capabilities', {
            'fields': ('is_fax_enabled', 'is_voice_enabled', 'is_sms_enabled')
        }),
        ('Routing', {
            'fields': ('route_to_email', 'route_to_extension'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        })
    )
    
    def formatted_number(self, obj):
        # Format as (XXX) XXX-XXXX for 10-digit numbers
        if len(obj.number) == 10:
            return f"({obj.number[:3]}) {obj.number[3:6]}-{obj.number[6:]}"
        elif len(obj.number) == 11 and obj.number.startswith('1'):
            return f"+1 ({obj.number[1:4]}) {obj.number[4:7]}-{obj.number[7:]}"
        return obj.number
    formatted_number.short_description = '📞 Number'
    formatted_number.admin_order_field = 'number'
    
    def provider_badge(self, obj):
        colors = {
            'telnyx': '#00C08B',
            'twilio': '#F22F46',
            'vitelity': '#0066CC',
            'internal': '#666666'
        }
        color = colors.get(obj.provider, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_provider_display()
        )
    provider_badge.short_description = 'Provider'
    
    def capabilities(self, obj):
        icons = []
        if obj.is_fax_enabled:
            icons.append('📠')
        if obj.is_voice_enabled:
            icons.append('📞')
        if obj.is_sms_enabled:
            icons.append('💬')
        return ' '.join(icons) or '❌'
    capabilities.short_description = 'Services'
    
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅</span>')
        return format_html('<span style="color: red;">❌</span>')
    status_badge.short_description = 'Active'
    
    def actions_buttons(self, obj):
        buttons = []
        if obj.assigned_to:
            buttons.append(format_html(
                '<a class="button" href="{}">👤 View User</a>',
                reverse('admin:auth_user_change', args=[obj.assigned_to.pk])
            ))
        buttons.append(format_html(
            '<a class="button" href="#" onclick="testDID({})">🧪 Test</a>',
            obj.pk
        ))
        return format_html(' '.join(buttons))
    actions_buttons.short_description = 'Actions'
    
    actions = ['purchase_dids_from_telnyx', 'assign_to_user', 'enable_fax', 'disable_fax']
    
    def purchase_dids_from_telnyx(self, request, queryset=None):
        """Purchase DIDs from Telnyx API"""
        # Redirect to DID purchase view
        return HttpResponseRedirect(reverse('admin:purchase_dids'))
    purchase_dids_from_telnyx.short_description = "🛒 Purchase DIDs from Telnyx"
    
    def assign_to_user(self, request, queryset):
        # This would show a form to select user
        selected = queryset.values_list('pk', flat=True)
        return HttpResponseRedirect(f'/admin/fax/did/assign/?ids={",".join(map(str, selected))}')
    assign_to_user.short_description = "👤 Assign to user"
    
    def enable_fax(self, request, queryset):
        queryset.update(is_fax_enabled=True)
        self.message_user(request, f"📠 Fax enabled for {queryset.count()} DIDs")
    enable_fax.short_description = "📠 Enable fax"
    
    def disable_fax(self, request, queryset):
        queryset.update(is_fax_enabled=False)
        self.message_user(request, f"❌ Fax disabled for {queryset.count()} DIDs")
    disable_fax.short_description = "❌ Disable fax"
    
    class Media:
        js = ('admin/js/did_admin.js',)
        css = {
            'all': ('admin/css/did_admin.css',)
        }


@admin.register(CoverPage)
class CoverPageAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'template_badge', 'preview_button', 'is_default', 'is_active', 'created_by']
    list_filter = ['template_type', 'is_default', 'is_active', 'tenant']
    search_fields = ['name', 'header_text', 'footer_text']
    readonly_fields = ['created_at', 'updated_at', 'preview_cover_page']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'tenant', 'template_type', 'is_default', 'is_active')
        }),
        ('Header Settings', {
            'fields': ('header_text', 'show_logo', 'logo_position')
        }),
        ('Content Fields', {
            'fields': ('show_date', 'show_time', 'show_from', 'show_to', 
                      'show_pages', 'show_subject', 'show_message'),
            'classes': ('collapse',)
        }),
        ('Custom Fields', {
            'fields': ('custom_field_1_label', 'custom_field_2_label', 'custom_field_3_label'),
            'classes': ('collapse',)
        }),
        ('Footer', {
            'fields': ('footer_text',)
        }),
        ('Styling', {
            'fields': ('font_family', 'primary_color', 'secondary_color'),
            'classes': ('collapse',)
        }),
        ('Custom HTML', {
            'fields': ('custom_html',),
            'classes': ('collapse',)
        }),
        ('Preview', {
            'fields': ('preview_cover_page',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def template_badge(self, obj):
        colors = {
            'professional': '#2C3E50',
            'simple': '#95A5A6',
            'modern': '#3498DB',
            'classic': '#8B4513',
            'custom': '#9B59B6'
        }
        color = colors.get(obj.template_type, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_template_type_display()
        )
    template_badge.short_description = 'Template'
    
    def preview_button(self, obj):
        return format_html(
            '<a class="button" href="/admin/fax/coverpage/{}/preview/" target="_blank">👁️ Preview</a>',
            obj.pk
        )
    preview_button.short_description = 'Preview'
    
    def preview_cover_page(self, obj):
        return format_html(
            '<iframe src="/admin/fax/coverpage/{}/preview/" width="100%" height="600" style="border: 1px solid #ddd;"></iframe>',
            obj.pk
        )
    preview_cover_page.short_description = 'Cover Page Preview'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['duplicate_cover_page', 'set_as_default']
    
    def duplicate_cover_page(self, request, queryset):
        for cover_page in queryset:
            cover_page.pk = None
            cover_page.name = f"{cover_page.name} (Copy)"
            cover_page.is_default = False
            cover_page.save()
        self.message_user(request, f"📄 {queryset.count()} cover pages duplicated")
    duplicate_cover_page.short_description = "📄 Duplicate selected"
    
    def set_as_default(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "⚠️ Please select only one cover page to set as default", level=messages.WARNING)
            return
        queryset.update(is_default=True)
        # Unset other defaults for the same tenant
        for obj in queryset:
            CoverPage.objects.filter(tenant=obj.tenant).exclude(pk=obj.pk).update(is_default=False)
        self.message_user(request, "✅ Default cover page set")
    set_as_default.short_description = "⭐ Set as default"


@admin.register(InboundFaxSettings)
class InboundFaxSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'email_badge', 'storage_badge', 'features', 'is_active']
    list_filter = ['email_format', 'storage_backend', 'ocr_enabled', 'is_active', 'tenant']
    search_fields = ['user__username', 'user__email', 'email_address']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User & Tenant', {
            'fields': ('user', 'tenant', 'is_active')
        }),
        ('📧 Email Delivery', {
            'fields': ('email_enabled', 'email_address', 'cc_addresses', 'email_format',
                      'email_subject_template', 'include_cover_sheet')
        }),
        ('🖨️ Printing', {
            'fields': ('auto_print', 'printer_name'),
            'classes': ('collapse',)
        }),
        ('🔍 OCR Settings', {
            'fields': ('ocr_enabled', 'ocr_language', 'searchable_pdf'),
            'classes': ('collapse',)
        }),
        ('💾 Storage', {
            'fields': ('archive_enabled', 'archive_days', 'storage_backend', 'storage_path'),
            'classes': ('collapse',)
        }),
        ('🔀 Routing', {
            'fields': ('routing_enabled', 'routing_rules'),
            'classes': ('collapse',)
        }),
        ('🔔 Notifications', {
            'fields': ('sms_notification', 'sms_number', 'webhook_enabled', 'webhook_url', 'webhook_secret'),
            'classes': ('collapse',)
        }),
        ('🔒 Security', {
            'fields': ('require_encryption', 'allowed_senders', 'blocked_senders'),
            'classes': ('collapse',)
        })
    )
    
    def email_badge(self, obj):
        if obj.email_enabled:
            return format_html(
                '<span style="color: green;">📧 {}</span>',
                obj.email_format.upper()
            )
        return format_html('<span style="color: gray;">📧 Disabled</span>')
    email_badge.short_description = 'Email'
    
    def storage_badge(self, obj):
        icons = {
            'local': '💾',
            's3': '☁️',
            'azure': '☁️',
            'gcs': '☁️'
        }
        return format_html(
            '{} {}',
            icons.get(obj.storage_backend, '💾'),
            obj.get_storage_backend_display()
        )
    storage_badge.short_description = 'Storage'
    
    def features(self, obj):
        features = []
        if obj.ocr_enabled:
            features.append('🔍 OCR')
        if obj.auto_print:
            features.append('🖨️ Print')
        if obj.routing_enabled:
            features.append('🔀 Routing')
        if obj.webhook_enabled:
            features.append('🔗 Webhook')
        return ' '.join(features) or '—'
    features.short_description = 'Features'


@admin.register(OutboundFaxSettings)
class OutboundFaxSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'default_did', 'settings_summary', 'is_active']
    list_filter = ['use_ecm', 'fine_resolution', 'allow_scheduling', 'is_active', 'tenant']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user', 'default_did', 'default_cover_page']
    
    fieldsets = (
        ('User & Tenant', {
            'fields': ('user', 'tenant', 'is_active')
        }),
        ('📞 Default Settings', {
            'fields': ('default_did', 'default_cover_page')
        }),
        ('📠 Transmission Settings', {
            'fields': ('use_ecm', 'fine_resolution', 'max_retries', 'retry_interval')
        }),
        ('✉️ Confirmation', {
            'fields': ('confirmation_enabled', 'confirmation_email', 'include_first_page'),
            'classes': ('collapse',)
        }),
        ('📝 Header', {
            'fields': ('header_format',),
            'classes': ('collapse',)
        }),
        ('⏰ Scheduling', {
            'fields': ('allow_scheduling', 'business_hours_only', 
                      'business_hours_start', 'business_hours_end', 'business_days'),
            'classes': ('collapse',)
        }),
        ('💰 Cost Controls', {
            'fields': ('max_pages_per_fax', 'max_cost_per_fax', 'require_approval_above'),
            'classes': ('collapse',)
        })
    )
    
    def settings_summary(self, obj):
        settings = []
        if obj.use_ecm:
            settings.append('ECM')
        if obj.fine_resolution:
            settings.append('Fine')
        if obj.allow_scheduling:
            settings.append('📅')
        if obj.business_hours_only:
            settings.append('🕐')
        return ' | '.join(settings) or '—'
    settings_summary.short_description = 'Settings'


@admin.register(FaxTransaction)
class FaxTransactionAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'direction_icon', 'formatted_sender', 'formatted_recipient', 
                   'pages', 'duration_display', 'status_badge', 'created_at']
    list_filter = ['direction', 'status', 'created_at']
    search_fields = ['uuid', 'sender_number', 'recipient_number']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def direction_icon(self, obj):
        if obj.direction == 'inbound':
            return format_html('<span style="color: green;">📥</span>')
        return format_html('<span style="color: blue;">📤</span>')
    direction_icon.short_description = 'Dir'
    
    def formatted_sender(self, obj):
        if len(obj.sender_number) == 10:
            return f"({obj.sender_number[:3]}) {obj.sender_number[3:6]}-{obj.sender_number[6:]}"
        return obj.sender_number
    formatted_sender.short_description = 'From'
    
    def formatted_recipient(self, obj):
        if len(obj.recipient_number) == 10:
            return f"({obj.recipient_number[:3]}) {obj.recipient_number[3:6]}-{obj.recipient_number[6:]}"
        return obj.recipient_number
    formatted_recipient.short_description = 'To'
    
    def duration_display(self, obj):
        if obj.duration:
            mins = obj.duration // 60
            secs = obj.duration % 60
            return f"{mins}:{secs:02d}"
        return "—"
    duration_display.short_description = 'Duration'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'processing': '#4169E1',
            'sent': '#32CD32',
            'received': '#32CD32',
            'failed': '#DC143C',
            'busy': '#FF6347',
            'no_answer': '#FFD700',
            'cancelled': '#808080'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    actions = ['retry_failed_faxes', 'export_to_csv']
    
    def retry_failed_faxes(self, request, queryset):
        failed = queryset.filter(status='failed')
        for fax in failed:
            # Queue for retry
            fax.status = 'pending'
            fax.save()
        self.message_user(request, f"🔄 {failed.count()} faxes queued for retry")
    retry_failed_faxes.short_description = "🔄 Retry failed faxes"


# Models are already registered with @admin.register decorator