from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import path
from .models import (
    CompanySettings, Notification, ActivityLog, TeamMember, ProjectShowcase,
    ContactMessage, Currency, AuditLog, NewsletterSubscriber,
    NewsletterCampaign, NewsletterSendLog, LegalDocument, CookieConsent,
    CookieCategory, CookieDetail, Testimonial, KenyanHoliday, HolidayOffer,
    ServiceArea, VideoTutorial
)
from .forms import (
    CompanySettingsForm, NewsletterCampaignForm, LegalDocumentForm,
    ServiceAreaForm, HolidayOfferForm, TeamMemberForm,
    ProjectShowcaseForm, TestimonialForm, CookieConsentForm
)

# Holiday Management Admin
@admin.register(KenyanHoliday)
class KenyanHolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'holiday_type', 'date_type', 'emoji', 'is_active', 'lead_time_days']
    list_filter = ['holiday_type', 'date_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'lead_time_days']
    readonly_fields = ['is_currently_active']

    fieldsets = (
        ('Holiday Information', {
            'fields': ('name', 'emoji', 'holiday_type', 'description')
        }),
        ('Date Configuration', {
            'fields': ('date_type', 'fixed_month', 'fixed_day', 'lead_time_days', 'duration_days')
        }),
        ('Status', {
            'fields': ('is_active', 'is_currently_active')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('fixed_month', 'fixed_day', 'name')


@admin.register(HolidayOffer)
class HolidayOfferAdmin(admin.ModelAdmin):
    form = HolidayOfferForm
    list_display = ['holiday', '__str__', 'discount_percentage', 'priority', 'is_active']
    list_filter = ['holiday', 'is_active', 'priority']
    search_fields = ['holiday__name', 'banner_text', 'discount_description']
    list_editable = ['is_active', 'priority']
    readonly_fields = ['is_currently_applicable']

    fieldsets = (
        ('Holiday Association', {
            'fields': ('holiday',)
        }),
        ('Offer Details', {
            'fields': ('banner_text', 'discount_percentage', 'discount_description', 'special_benefits')
        }),
        ('Timing (Optional)', {
            'fields': ('custom_lead_days', 'custom_duration_days'),
            'classes': ('collapse',)
        }),
        ('Priority & Status', {
            'fields': ('priority', 'order', 'is_active', 'is_currently_applicable')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('holiday').order_by('-priority', 'order', '-created_at')

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    form = CompanySettingsForm
    list_display = ('name', 'email', 'phone', 'primary_color', 'tagline')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'tagline', 'email', 'phone', 'website', 'address')
        }),
        ('Company Messaging', {
            'fields': ('about_description', 'mission_statement', 'vision_statement'),
            'classes': ('collapse',)
        }),
        ('SEO & Meta Information', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Branding & Media', {
            'fields': ('logo', 'favicon', 'hero_image', 'hero_title', 'hero_subtitle', 'hero_disclaimer', 'primary_color', 'secondary_color'),
            'classes': ('collapse',)
        }),
        ('Homepage Content', {
            'fields': ('urgency_banner_enabled', 'urgency_banner_text', 'urgency_banner_end_date', 'testimonial_section_title', 'testimonial_section_subtitle', 'hero_featured_customers_count'),
            'description': 'Content displayed on the homepage including urgency banners, testimonials, and customer statistics'
        }),
        ('Contact Information', {
            'fields': ('sales_email', 'sales_phone', 'support_email', 'support_phone', 'whatsapp_number'),
            'classes': ('collapse',)
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url', 'youtube_url'),
            'classes': ('collapse',)
        }),
        ('Location & Maps', {
            'fields': ('google_maps_url', 'latitude', 'longitude'),
            'description': 'Configure company location for Google Maps integration. Latitude and longitude enable the embedded map on the contact page.'
        }),
        ('Business Hours', {
            'fields': ('business_hours_weekday', 'business_hours_saturday', 'business_hours_sunday'),
            'classes': ('collapse',)
        }),
        ('Support Hours', {
            'fields': ('support_hours_weekday', 'support_hours_saturday', 'support_hours_sunday', 'emergency_support_available', 'emergency_support_description'),
            'description': 'Configure support hours that appear on the help page'
        }),
        ('Payment Integration - M-Pesa', {
            'fields': ('mpesa_business_name', 'mpesa_paybill_number', 'mpesa_account_number', 'mpesa_phone_number', 'mpesa_till_number'),
            'classes': ('collapse',)
        }),
        ('Business Details', {
            'fields': ('registration_number', 'tax_number', 'bank_name', 'bank_account_number', 'bank_branch'),
            'classes': ('collapse',)
        }),
        ('Statistics & Settings', {
            'fields': ('projects_completed', 'total_capacity', 'customer_satisfaction', 'cities_served', 'co2_saved_tons', 'founded_year', 'default_currency', 'vat_rate'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one company settings instance
        return not CompanySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of company settings
        return False

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'category', 'is_read', 'created_at')
    list_filter = ('notification_type', 'category', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'read_at', 'email_sent_at')
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'title', 'message', 'notification_type', 'category')
        }),
        ('Links', {
            'fields': ('link_url', 'link_text'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'email_sent', 'email_sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at',
        'log_type',
        'severity',
        'message',
        'user',
        'ip_address'
    ]
    
    list_filter = [
        'log_type',
        'severity',
        'created_at',
    ]
    
    readonly_fields = [
        'created_at',
        'log_type',
        'severity',
        'metric',
        'value',
        'message',
        'description',
        'action',
        'user',
        'ip_address',
        'user_agent'
    ]
    
    search_fields = [
        'message',
        'description',
        'user__username',
        'ip_address'
    ]
    
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Logs should only be created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be modified
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    form = TeamMemberForm
    list_display = ('name', 'position', 'order', 'is_active')
    list_filter = ('is_active', 'position')
    search_fields = ('name', 'position', 'bio')
    list_editable = ('order', 'is_active')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'bio', 'photo')
        }),
        ('Contact & Social', {
            'fields': ('email', 'linkedin_url', 'twitter_url'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
            'description': 'Control how this team member appears on the website'
        })
    )

@admin.register(ProjectShowcase)
class ProjectShowcaseAdmin(admin.ModelAdmin):
    form = ProjectShowcaseForm
    list_display = ('title', 'location', 'capacity', 'project_type', 'is_featured', 'order')
    list_filter = ('project_type', 'is_featured', 'completion_date')
    search_fields = ('title', 'location', 'description')
    list_editable = ('is_featured', 'order')

    fieldsets = (
        ('Project Information', {
            'fields': ('title', 'description', 'image', 'capacity', 'project_type')
        }),
        ('Location & Completion', {
            'fields': ('location', 'completion_date')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'order'),
            'description': 'Control how this project appears on the website'
        })
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    form = TestimonialForm
    list_display = ('author_name', 'location', 'rating', 'is_featured', 'order', 'created_at')
    list_filter = ('rating', 'is_featured', 'created_at')
    search_fields = ('author_name', 'location', 'quote')
    list_editable = ('is_featured', 'order')

    fieldsets = (
        ('Testimonial Information', {
            'fields': ('author_name', 'author_initials', 'location', 'quote', 'rating')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'order'),
            'description': 'Control how this testimonial appears on the homepage'
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('order', '-created_at')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'inquiry_type', 'property_type', 'is_read', 'is_responded', 'submitted_at')
    list_filter = ('inquiry_type', 'property_type', 'is_read', 'is_responded', 'submitted_at', 'subscribe_newsletter')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'message', 'location')
    readonly_fields = ('first_name', 'last_name', 'email', 'phone', 'location', 'property_type', 
                      'monthly_bill', 'inquiry_type', 'message', 'subscribe_newsletter', 
                      'agree_privacy', 'submitted_at', 'ip_address', 'full_name')
    list_editable = ('is_read',)
    
    fieldsets = (
        ('Contact Details', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'location')
        }),
        ('Inquiry Information', {
            'fields': ('inquiry_type', 'property_type', 'monthly_bill', 'message')
        }),
        ('Subscription & Privacy', {
            'fields': ('subscribe_newsletter', 'agree_privacy'),
            'classes': ('collapse',)
        }),
        ('Admin Management', {
            'fields': ('is_read', 'is_responded', 'admin_notes')
        }),
        ('System Information', {
            'fields': ('submitted_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_responded', 'mark_as_unread', 'respond_to_messages']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/respond/', self.admin_site.admin_view(self.respond_view), name='core_contactmessage_respond'),
        ]
        return custom_urls + urls
    
    def respond_view(self, request, object_id):
        """Handle email response to contact message"""
        contact_message = self.get_object(request, object_id)
        if contact_message is None:
            messages.error(request, 'Contact message not found.')
            return HttpResponseRedirect('../')
        
        if request.method == 'POST':
            response_message = request.POST.get('response_message', '').strip()
            if response_message:
                from .email_utils import EmailService
                success = EmailService.send_contact_response_email(
                    contact_message, 
                    response_message, 
                    request.user
                )
                
                if success:
                    # Add to admin notes
                    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                    admin_note = f"[{timestamp}] Response sent by {request.user.get_full_name() or request.user.username}:\n{response_message}\n\n"
                    contact_message.admin_notes = admin_note + contact_message.admin_notes
                    contact_message.save(update_fields=['admin_notes'])
                    
                    messages.success(request, f'Response sent successfully to {contact_message.email}')
                else:
                    messages.error(request, 'Failed to send response email. Please check email configuration.')
            else:
                messages.error(request, 'Please enter a response message.')
            
            return HttpResponseRedirect('../')
        
        context = {
            'title': f'Respond to {contact_message.full_name}',
            'contact_message': contact_message,
            'opts': self.model._meta,
            'original': contact_message,
            'has_view_permission': self.has_view_permission(request, contact_message),
        }
        
        return render(request, 'admin/core/contactmessage/respond.html', context)
    
    def response_actions(self, obj):
        """Display response action button"""
        if obj.pk:
            return format_html(
                '<a class="button" href="{}">Send Response</a>',
                reverse('admin:core_contactmessage_respond', args=[obj.pk])
            )
        return '-'
    response_actions.short_description = 'Actions'
    response_actions.allow_tags = True
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'
    
    def mark_as_responded(self, request, queryset):
        updated = queryset.update(is_responded=True)
        self.message_user(request, f'{updated} messages marked as responded.')
    mark_as_responded.short_description = 'Mark selected messages as responded'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} messages marked as unread.')
    mark_as_unread.short_description = 'Mark selected messages as unread'
    
    def respond_to_messages(self, request, queryset):
        """Redirect to respond page for single message"""
        if queryset.count() == 1:
            contact_message = queryset.first()
            return HttpResponseRedirect(reverse('admin:core_contactmessage_respond', args=[contact_message.pk]))
        else:
            self.message_user(request, 'Please select only one message to respond to.', level=messages.WARNING)
    respond_to_messages.short_description = 'Send email response'
    
    def changelist_view(self, request, extra_context=None):
        # Add response action button to the changelist
        extra_context = extra_context or {}
        return super().changelist_view(request, extra_context=extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                extra_context['show_response_button'] = True
                extra_context['response_url'] = reverse('admin:core_contactmessage_respond', args=[object_id])
        return super().change_view(request, object_id, form_url, extra_context)
    
    def has_add_permission(self, request):
        # Contact messages come from the website, not admin
        return False


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'exchange_rate', 'is_active', 'is_base')
    list_filter = ('is_active', 'is_base')
    search_fields = ('code', 'name')
    list_editable = ('exchange_rate', 'is_active')
    
    fieldsets = (
        ('Currency Information', {
            'fields': ('code', 'name', 'symbol')
        }),
        ('Exchange Rate', {
            'fields': ('exchange_rate',),
            'description': 'Exchange rate relative to KES (Kenyan Shillings)'
        }),
        ('Settings', {
            'fields': ('is_active', 'is_base')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_repr', 'ip_address', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'action', 'model_name', 'object_repr')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent', 'timestamp')
    
    fieldsets = (
        ('Action Details', {
            'fields': ('user', 'action', 'model_name', 'object_id', 'object_repr')
        }),
        ('Changes', {
            'fields': ('changes',),
            'classes': ('collapse',)
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Audit logs are created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Audit logs should not be modified
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit logs should not be deleted
        return False


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'get_full_name', 'subscription_source', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscription_source', 'subscribed_at')
    search_fields = ('email', 'first_name', 'last_name')
    list_editable = ('is_active',)
    readonly_fields = ('subscribed_at', 'unsubscribed_at')
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Subscription Details', {
            'fields': ('is_active', 'subscription_source', 'subscribed_at', 'unsubscribed_at')
        }),
    )
    
    actions = ['activate_subscribers', 'deactivate_subscribers', 'export_emails']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Name'
    
    def activate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True, unsubscribed_at=None)
        self.message_user(request, f'{updated} subscribers activated.')
    activate_subscribers.short_description = 'Activate selected subscribers'
    
    def deactivate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=False, unsubscribed_at=timezone.now())
        self.message_user(request, f'{updated} subscribers deactivated.')
    deactivate_subscribers.short_description = 'Deactivate selected subscribers'
    
    def export_emails(self, request, queryset):
        emails = [subscriber.email for subscriber in queryset]
        self.message_user(request, f'Emails: {", ".join(emails)}')
    export_emails.short_description = 'Export email addresses'


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    form = NewsletterCampaignForm
    list_display = ('title', 'subject', 'status', 'total_recipients', 'total_sent', 'delivery_rate_display', 'created_at', 'sent_at', 'send_now_button')
    list_filter = ('status', 'created_at', 'sent_at')
    search_fields = ('title', 'subject', 'content')
    readonly_fields = ('created_at', 'sent_at', 'total_recipients', 'total_sent', 'total_failed', 'delivery_rate')

    fieldsets = (
        ('Campaign Information', {
            'fields': ('title', 'subject', 'preview_text', 'content', 'template_type')
        }),
        ('Call to Action', {
            'fields': ('call_to_action_text', 'call_to_action_url'),
            'description': 'Text and URL for the main call-to-action button. Both fields must be filled to display the CTA button.'
        }),
        ('Scheduling & Status', {
            'fields': ('status', 'scheduled_for', 'created_by')
        }),
        ('Analytics (Read-only)', {
            'fields': ('total_recipients', 'total_sent', 'total_failed', 'delivery_rate', 'created_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['send_campaign', 'duplicate_campaign', 'reset_to_draft']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Creating new campaign
            # Restrict status choices for new campaigns
            form.base_fields['status'].choices = [
                ('draft', 'Draft'),
                ('scheduled', 'Scheduled'),
            ]
        return form

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new campaign
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def delivery_rate_display(self, obj):
        rate = obj.delivery_rate
        # Handle SafeString that may be cached from readonly_fields processing
        from django.utils.safestring import SafeString
        if isinstance(rate, SafeString):
            # Extract numeric value from SafeString
            rate_str = str(rate)
            import re
            match = re.search(r'(\d+(?:\.\d+)?)', rate_str)
            if match:
                try:
                    rate = float(match.group(1))
                except (ValueError, TypeError):
                    rate = 0.0
            else:
                rate = 0.0
        elif isinstance(rate, (int, float)):
            pass  # Already a number
        else:
            # Handle other string-like objects
            try:
                rate = float(rate)
            except (ValueError, TypeError):
                rate = 0.0

        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        # Format the rate as string first to avoid SafeString formatting issues
        rate_formatted = f"{rate:.1f}"
        return format_html(
            '<span style="color: {};">{}%</span>',
            color,
            rate_formatted
        )
    delivery_rate_display.short_description = 'Delivery Rate'

    def send_now_button(self, obj):
        """Display a send button for campaigns that can be sent"""
        if obj.can_send():
            return format_html(
                '<a class="button" href="{}" onclick="return confirm(\'Are you sure you want to send this campaign?\')">Send Now</a>',
                reverse('admin:send_campaign', args=[obj.pk])
            )
        return format_html('<span style="color: #999;">Cannot send</span>')
    send_now_button.short_description = 'Send'
    send_now_button.allow_tags = True
    
    def send_campaign(self, request, queryset):
        from .newsletter_service import NewsletterService
        service = NewsletterService()

        for campaign in queryset:
            if campaign.can_send():
                result = service.send_campaign(campaign, request.user)
                if result['success']:
                    self.message_user(request, result['message'])
                else:
                    self.message_user(request, f'Failed to send campaign "{campaign.title}": {result["error"]}', level='error')
            else:
                self.message_user(request, f'Campaign "{campaign.title}" cannot be sent (status: {campaign.get_status_display()})', level='warning')
    send_campaign.short_description = 'Send selected campaigns'
    
    def reset_to_draft(self, request, queryset):
        updated = queryset.update(status='draft', sent_at=None, total_sent=0, total_failed=0)
        self.message_user(request, f'{updated} campaigns reset to draft status.')
    reset_to_draft.short_description = 'Reset to draft (allows re-sending)'

    def duplicate_campaign(self, request, queryset):
        for campaign in queryset:
            campaign.pk = None
            campaign.title = f"{campaign.title} (Copy)"
            campaign.status = 'draft'
            campaign.created_by = request.user
            campaign.sent_at = None
            campaign.total_recipients = 0
            campaign.total_sent = 0
            campaign.total_failed = 0
            campaign.save()
            self.message_user(request, f'Campaign "{campaign.title}" duplicated.')
    duplicate_campaign.short_description = 'Duplicate selected campaigns'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:campaign_id>/send/', self.admin_site.admin_view(self.send_campaign_view), name='send_campaign'),
        ]
        return custom_urls + urls

    def send_campaign_view(self, request, campaign_id):
        """Handle individual campaign sending"""
        try:
            campaign = self.get_queryset(request).get(pk=campaign_id)
        except NewsletterCampaign.DoesNotExist:
            messages.error(request, 'Campaign not found.')
            return redirect('admin:core_newslettercampaign_changelist')

        if not campaign.can_send():
            messages.error(request, f'Campaign "{campaign.title}" cannot be sent (status: {campaign.get_status_display()})')
            return redirect('admin:core_newslettercampaign_changelist')

        # Get target subscribers
        subscribers = campaign.get_target_subscribers()
        if not subscribers.exists():
            messages.warning(request, f'No active subscribers found for campaign "{campaign.title}".')
            return redirect('admin:core_newslettercampaign_changelist')

        # Use the newsletter service to send
        from .newsletter_service import NewsletterService
        service = NewsletterService()
        result = service.send_campaign(campaign, request.user)

        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])

        return redirect('admin:core_newslettercampaign_changelist')


@admin.register(NewsletterSendLog)
class NewsletterSendLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'subscriber_email', 'delivery_status_display', 'sent_at', 'error_preview')
    list_filter = ('delivery_status', 'status', 'sent_at', 'campaign')
    search_fields = ('campaign__title', 'subscriber__email', 'error_message')
    readonly_fields = ('campaign', 'subscriber', 'delivery_status', 'status', 'sent_at', 'error_message', 'email_address')
    
    def subscriber_email(self, obj):
        return obj.subscriber.email
    subscriber_email.short_description = 'Subscriber Email'
    
    def delivery_status_display(self, obj):
        """Display delivery status with color coding"""
        status = getattr(obj, 'delivery_status', None)
        if status == 'sent':
            return format_html('<span style="color: #28a745;">✓ Sent</span>')
        elif status == 'failed':
            return format_html('<span style="color: #dc3545;">✗ Failed</span>')
        elif status == 'bounced':
            return format_html('<span style="color: #ffc107;">⚠ Bounced</span>')
        else:
            return format_html('<span style="color: #6c757d;">○ Pending</span>')
    delivery_status_display.short_description = 'Status'

    def error_preview(self, obj):
        if obj.error_message:
            return obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
        return '-'
    error_preview.short_description = 'Error Message'

    def has_add_permission(self, request):
        # Send logs are created automatically
        return False

    def has_change_permission(self, request, obj=None):
        # Send logs should not be modified
        return False


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    form = LegalDocumentForm
    list_display = ('document_type', 'title', 'version', 'effective_date', 'is_active', 'last_updated')
    list_filter = ('document_type', 'is_active', 'effective_date', 'last_updated')
    search_fields = ('title', 'content', 'short_description')
    readonly_fields = ('last_updated',)
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Document Information', {
            'fields': ('document_type', 'title', 'short_description')
        }),
        ('Content', {
            'fields': ('content',),
            'description': 'You can use HTML tags for formatting. Preview the document after saving.'
        }),
        ('Version Control', {
            'fields': ('version', 'effective_date', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['duplicate_document', 'activate_documents', 'deactivate_documents']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new document
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def duplicate_document(self, request, queryset):
        for doc in queryset:
            doc.pk = None
            doc.title = f"{doc.title} (Copy)"
            doc.version = "1.0"
            doc.is_active = False
            doc.created_by = request.user
            doc.save()
            self.message_user(request, f'Document "{doc.title}" duplicated.')
    duplicate_document.short_description = 'Duplicate selected documents'
    
    def activate_documents(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} documents activated.')
    activate_documents.short_description = 'Activate selected documents'
    
    def deactivate_documents(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} documents deactivated.')
    deactivate_documents.short_description = 'Deactivate selected documents'


# Cookie Management Admin

class CookieDetailInline(admin.TabularInline):
    model = CookieDetail
    extra = 1
    fields = ('name', 'purpose', 'duration', 'third_party', 'provider', 'is_active')


@admin.register(CookieCategory)
class CookieCategoryAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'is_essential', 'is_active', 'order', 'cookie_count')
    list_filter = ('is_essential', 'is_active')
    search_fields = ('name', 'display_name', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', 'name')
    inlines = [CookieDetailInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Settings', {
            'fields': ('is_essential', 'is_active', 'order')
        }),
    )
    
    def cookie_count(self, obj):
        return obj.cookies.count()
    cookie_count.short_description = 'Cookies'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('cookies')


@admin.register(CookieDetail)
class CookieDetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'provider', 'duration', 'third_party', 'is_active')
    list_filter = ('category', 'third_party', 'is_active', 'provider')
    search_fields = ('name', 'purpose', 'provider')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'purpose')
        }),
        ('Details', {
            'fields': ('duration', 'provider', 'third_party')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )


@admin.register(CookieConsent)
class CookieConsentAdmin(admin.ModelAdmin):
    form = CookieConsentForm
    list_display = ('consent_summary', 'user_display', 'consent_date', 'ip_address', 'consent_version', 'consent_status')
    list_filter = ('consent_date', 'consent_version', 'essential_consent', 'analytics_consent', 'marketing_consent')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'identifier', 'ip_address')
    readonly_fields = ('consent_date', 'updated_date', 'identifier', 'ip_address', 'user_agent')
    date_hierarchy = 'consent_date'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'identifier', 'ip_address', 'user_agent')
        }),
        ('Consent Preferences', {
            'fields': ('essential_consent', 'analytics_consent', 'marketing_consent', 'preferences_consent', 'social_consent')
        }),
        ('Metadata', {
            'fields': ('consent_date', 'updated_date', 'consent_version')
        }),
    )
    
    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.user.get_full_name() or obj.user.username,
                obj.user.email
            )
        else:
            return format_html(
                '<em>Anonymous</em><br><small>{}</small>',
                obj.identifier[:10] + '...' if obj.identifier else 'N/A'
            )
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user__email'
    
    def consent_summary(self, obj):
        consents = [
            ('Essential', obj.essential_consent, '#28a745'),
            ('Analytics', obj.analytics_consent, '#007bff'),
            ('Marketing', obj.marketing_consent, '#dc3545'),
            ('Preferences', obj.preferences_consent, '#ffc107'),
            ('Social', obj.social_consent, '#6f42c1')
        ]
        
        html = ''
        for name, status, color in consents:
            icon = '✓' if status == 'granted' else '✗' if status == 'denied' else '?'
            html += format_html(
                '<span style="color: {}; margin-right: 8px;" title="{}: {}">{} {}</span>',
                color, name, status.title(), icon, name[:1]
            )
        
        return format_html('<div style="font-size: 12px;">{}</div>', html)
    consent_summary.short_description = 'Consents'
    
    def consent_status(self, obj):
        granted_count = sum([
            obj.analytics_consent == 'granted',
            obj.marketing_consent == 'granted', 
            obj.preferences_consent == 'granted',
            obj.social_consent == 'granted'
        ])
        
        if granted_count == 4:
            return format_html('<span style="color: #28a745;">✓ All Granted</span>')
        elif granted_count == 0:
            return format_html('<span style="color: #dc3545;">✗ Essential Only</span>')
        else:
            return format_html('<span style="color: #ffc107;">◐ Partial ({}/4)</span>', granted_count)
    consent_status.short_description = 'Status'
    
    actions = ['export_consent_data', 'anonymize_consent_data']
    
    def export_consent_data(self, request, queryset):
        # Custom export action can be implemented here
        self.message_user(request, f"Export functionality not yet implemented for {queryset.count()} records.")
    export_consent_data.short_description = 'Export consent data'
    
    def anonymize_consent_data(self, request, queryset):
        # Anonymize user data while keeping consent preferences
        count = 0
        for consent in queryset:
            if consent.user:
                consent.user = None
                consent.save()
                count += 1
        
        self.message_user(request, f"Anonymized {count} consent records.")
    anonymize_consent_data.short_description = 'Anonymize selected consents'


@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    form = ServiceAreaForm
    list_display = [
        'name', 'area_type', 'county_display', 'coverage_type',
        'contact_info', 'coordinates', 'is_active', 'order'
    ]
    list_filter = [
        'area_type', 'coverage_type', 'is_active', 'county'
    ]
    search_fields = [
        'name', 'county', 'contact_person', 'contact_phone', 'description'
    ]
    list_editable = ['is_active', 'order', 'coverage_type']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'area_type', 'county', 'coverage_type', 'description')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_phone', 'estimated_response_time'),
            'description': 'Local contact details for this service area'
        }),
        ('Geographic Information', {
            'fields': ('latitude', 'longitude', 'center_point'),
            'description': 'Coordinates for mapping and location services'
        }),
        ('Advanced Settings', {
            'fields': ('boundary_geojson', 'radius_km'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order'),
            'description': 'Control visibility and ordering'
        }),
    )

    actions = [
        'activate_areas', 'deactivate_areas', 'update_coordinates',
        'clear_contact_info', 'export_service_areas',
        'set_primary_coverage', 'set_extended_coverage', 'set_planned_coverage'
    ]

    def county_display(self, obj):
        """Display county with hierarchical indication"""
        if obj.area_type == 'county':
            return format_html('<strong>{}</strong>', obj.county or obj.name)
        else:
            return format_html('↳ {}', obj.county or 'Unknown County')
    county_display.short_description = 'County/Area'
    county_display.admin_order_field = 'county'

    def contact_info(self, obj):
        """Display contact information summary"""
        if obj.contact_person and obj.contact_phone:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.contact_person,
                obj.contact_phone
            )
        elif obj.contact_person:
            return obj.contact_person
        elif obj.contact_phone:
            return obj.contact_phone
        else:
            return format_html('<em style="color: #999;">No contact info</em>')
    contact_info.short_description = 'Contact'

    def coordinates(self, obj):
        """Display coordinates with map link"""
        if obj.latitude and obj.longitude:
            coords = f"{obj.latitude:.4f}, {obj.longitude:.4f}"
            map_url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank" style="color: #007bff;">{}</a>',
                map_url, coords
            )
        else:
            return format_html('<em style="color: #dc3545;">No coordinates</em>')
    coordinates.short_description = 'Coordinates'

    def get_queryset(self, request):
        """Order by county hierarchy"""
        return super().get_queryset(request).order_by('county', '-area_type', 'order', 'name')

    def activate_areas(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} service areas activated.')
    activate_areas.short_description = 'Activate selected areas'

    def deactivate_areas(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} service areas deactivated.')
    deactivate_areas.short_description = 'Deactivate selected areas'

    def update_coordinates(self, request, queryset):
        """Re-geocode selected areas"""
        from .geographic_utils import get_geographic_service

        geo_service = get_geographic_service()
        updated_count = 0

        for area in queryset:
            location_string = f"{area.name}, Kenya"
            if area.county and area.county != area.name:
                location_string = f"{area.name}, {area.county}, Kenya"

            geo_result = geo_service.geocode_location(location_string)
            if geo_result:
                area.latitude = geo_result['latitude']
                area.longitude = geo_result['longitude']
                area.save(update_fields=['latitude', 'longitude'])
                updated_count += 1

        self.message_user(request, f'Updated coordinates for {updated_count} service areas.')
    update_coordinates.short_description = 'Update coordinates for selected areas'

    def clear_contact_info(self, request, queryset):
        updated = queryset.update(
            contact_person='',
            contact_phone='',
            estimated_response_time=''
        )
        self.message_user(request, f'Cleared contact information for {updated} service areas.')
    clear_contact_info.short_description = 'Clear contact information'

    def export_service_areas(self, request, queryset):
        """Export service area data"""
        areas_data = []
        for area in queryset:
            areas_data.append({
                'name': area.name,
                'type': area.area_type,
                'county': area.county,
                'contact': area.contact_person,
                'phone': area.contact_phone,
                'coordinates': f"{area.latitude}, {area.longitude}" if area.latitude else "N/A"
            })

        # Simple text export for now
        export_text = "Service Areas Export\n\n"
        for area in areas_data:
            export_text += f"Name: {area['name']}\n"
            export_text += f"Type: {area['type']}\n"
            export_text += f"County: {area['county']}\n"
            export_text += f"Contact: {area['contact']}\n"
            export_text += f"Phone: {area['phone']}\n"
            export_text += f"Coordinates: {area['coordinates']}\n"
            export_text += "-" * 50 + "\n"

        self.message_user(request, f"Export data prepared for {len(areas_data)} areas.")
    export_service_areas.short_description = 'Export service area data'

    def set_primary_coverage(self, request, queryset):
        updated = queryset.update(coverage_type='primary')
        self.message_user(request, f'{updated} service areas set to Primary coverage.')
    set_primary_coverage.short_description = 'Set to Primary coverage'

    def set_extended_coverage(self, request, queryset):
        updated = queryset.update(coverage_type='extended')
        self.message_user(request, f'{updated} service areas set to Extended coverage.')
    set_extended_coverage.short_description = 'Set to Extended coverage'

    def set_planned_coverage(self, request, queryset):
        updated = queryset.update(coverage_type='planned')
        self.message_user(request, f'{updated} service areas set to Planned coverage.')
    set_planned_coverage.short_description = 'Set to Planned coverage'

    def save_model(self, request, obj, form, change):
        """Auto-geocode if coordinates are missing"""
        super().save_model(request, obj, form, change)

        # Auto-geocode if no coordinates
        if not obj.latitude or not obj.longitude:
            from .geographic_utils import get_geographic_service
            geo_service = get_geographic_service()

            location_string = f"{obj.name}, Kenya"
            if obj.county and obj.county != obj.name:
                location_string = f"{obj.name}, {obj.county}, Kenya"

            geo_result = geo_service.geocode_location(location_string)
            if geo_result:
                obj.latitude = geo_result['latitude']
                obj.longitude = geo_result['longitude']
                obj.save(update_fields=['latitude', 'longitude'])
                messages.success(request, f'Auto-geocoded {obj.name}: {obj.latitude}, {obj.longitude}')


@admin.register(VideoTutorial)
class VideoTutorialAdmin(admin.ModelAdmin):
    list_display = ['title', 'video_type', 'category', 'is_featured', 'is_active', 'order']
    list_filter = ['video_type', 'category', 'is_featured', 'is_active']
    search_fields = ['title', 'description', 'tags']
    list_editable = ['is_featured', 'is_active', 'order']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'tags')
        }),
        ('Video Content', {
            'fields': ('video_type', 'video_url', 'embed_code', 'thumbnail', 'duration')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
    )

    actions = ['activate_tutorials', 'deactivate_tutorials', 'feature_tutorials', 'unfeature_tutorials']

    def activate_tutorials(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} video tutorials activated.')
    activate_tutorials.short_description = 'Activate selected tutorials'

    def deactivate_tutorials(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} video tutorials deactivated.')
    deactivate_tutorials.short_description = 'Deactivate selected tutorials'

    def feature_tutorials(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} video tutorials featured.')
    feature_tutorials.short_description = 'Feature selected tutorials'

    def unfeature_tutorials(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} video tutorials unfeatured.')
    unfeature_tutorials.short_description = 'Unfeature selected tutorials'
