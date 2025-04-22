from django.contrib import admin
from .models import (
    SiteSettings, MainMenu, SocialLink, FooterSection, FooterLink, 
    ContactInfo, Newsletter, HeroBanner, WelcomeSection, WhatWeDoItem, 
    AboutBanner, Achievement, AboutSection, TeamSection, TeamMember, 
    ContactSection, PolicyPage, FAQItem, Certification, QuoteRequest,
    AdminNotification, QuoteFollowUp
)
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta
import csv
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name',)
   
    def has_add_permission(self, request):
        # Allow only one instance of site settings
        if self.model.objects.exists():
            return False
        return True


@admin.register(MainMenu)
class MainMenuAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'order')
    list_editable = ('order',)
    ordering = ('order',)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'icon_class')
    search_fields = ('name',)


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1


@admin.register(FooterSection)
class FooterSectionAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = [FooterLinkInline]


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'whatsapp', 'address')
   
    def has_add_permission(self, request):
        # Allow only one instance of contact info
        if self.model.objects.exists():
            return False
        return True


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'subscribed_at', 'is_active', 'confirmed')
    list_filter = ('subscribed_at', 'is_active', 'confirmed')
    search_fields = ('email', 'name')
    date_hierarchy = 'subscribed_at'
    actions = ['activate_subscribers', 'deactivate_subscribers', 'export_subscribers']
   
    fieldsets = (
        ('Newsletter Settings', {
            'fields': ('title', 'description'),
            'description': 'These settings control how the newsletter subscription form appears on the site.'
        }),
        ('Subscriber Information', {
            'fields': ('email', 'name', 'is_active', 'confirmed', 'interests', 'confirmation_token'),
        }),
    )
   
    def activate_subscribers(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} subscribers were successfully activated.")
    activate_subscribers.short_description = "Activate selected subscribers"
   
    def deactivate_subscribers(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} subscribers were successfully deactivated.")
    deactivate_subscribers.short_description = "Deactivate selected subscribers"
   
    def export_subscribers(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="newsletter_subscribers.csv"'
       
        writer = csv.writer(response)
        writer.writerow(['Email', 'Name', 'Subscribed At', 'Active', 'Confirmed'])
       
        for subscriber in queryset:
            writer.writerow([
                subscriber.email,
                subscriber.name,
                subscriber.subscribed_at,
                subscriber.is_active,
                subscriber.confirmed
            ])
       
        return response
    export_subscribers.short_description = "Export selected subscribers to CSV"


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)


@admin.register(WelcomeSection)
class WelcomeSectionAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(WhatWeDoItem)
class WhatWeDoItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)


@admin.register(AboutBanner)
class AboutBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)


@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(TeamSection)
class TeamSectionAdmin(admin.ModelAdmin):
    pass


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order')
    list_editable = ('order',)


@admin.register(ContactSection)
class ContactSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'cta_title')


@admin.register(PolicyPage)
class PolicyPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'last_updated', 'is_published')
    list_filter = ('type', 'is_published')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'type', 'slug', 'is_published')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('SEO', {
            'fields': ('meta_description',),
            'classes': ('collapse',)
        }),
    )


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order')
    list_filter = ('category',)
    list_editable = ('order', 'category')
    search_fields = ('question', 'answer')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'issuing_authority', 'issue_date', 'expiry_date', 'order')
    list_filter = ('issuing_authority',)
    list_editable = ('order',)
    search_fields = ('name', 'description', 'issuing_authority')
    date_hierarchy = 'issue_date'


class QuoteFollowUpInline(admin.TabularInline):
    model = QuoteFollowUp
    extra = 1
    fields = ('notes', 'follow_up_date', 'created_by')
    readonly_fields = ('follow_up_date',)
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    """Admin panel configuration for QuoteRequest model"""
    list_display = ('name', 'email', 'phone', 'company', 'product_interest', 'created_at', 'status_badge')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'phone', 'company', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    actions = ['export_as_csv', 'mark_as_in_progress', 'mark_as_completed', 'mark_as_declined']
    inlines = [QuoteFollowUpInline]

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('Request Details', {
            'fields': ('product_interest', 'message', 'created_at')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )

    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            'new': '#007bff',  # blue
            'in_progress': '#ffc107',  # yellow
            'completed': '#28a745',  # green
            'declined': '#dc3545',  # red
        }

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 5px;">{}</span>',
            colors.get(obj.status, '#6c757d'),  # default gray
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def export_as_csv(self, request, queryset):
        """Export selected quote requests as CSV"""
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.model_name}_export.csv'

        writer = csv.writer(response)
        writer.writerow(field_names)  # Write CSV headers
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])  # Write row data

        return response
    export_as_csv.short_description = "Export selected quote requests as CSV"

    def mark_as_in_progress(self, request, queryset):
        """Mark selected quote requests as in progress and notify customers"""
        updated = queryset.update(status='in_progress')

        for quote in queryset:
            # Send email notification
            subject = f"Update on your quote request - {settings.SITE_NAME}"
            html_message = render_to_string('core/emails/quote_in_progress.html', {
                'name': quote.name,
                'site_name': SiteSettings.objects.first().site_name,
                'contact_info': ContactInfo.objects.first(),
            })

            send_mail(
                subject=subject,
                message=f"We're currently working on your quote request.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[quote.email],
                html_message=html_message,
                fail_silently=True,
            )

        self.message_user(request, f"{updated} quote requests marked as in progress.")
    mark_as_in_progress.short_description = "Mark selected requests as in progress"
    
    def mark_as_completed(self, request, queryset):
        """Mark selected quote requests as completed and notify customers"""
        updated = queryset.update(status='completed')
        
        for quote in queryset:
            # Send email notification
            subject = f"Your quote is ready - {settings.SITE_NAME}"
            html_message = render_to_string('core/emails/quote_completed.html', {
                'name': quote.name,
                'site_name': SiteSettings.objects.first().site_name,
                'contact_info': ContactInfo.objects.first(),
            })
            
            send_mail(
                subject=subject,
                message=f"Your quote is now ready. Our team will contact you shortly.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[quote.email],
                html_message=html_message,
                fail_silently=True,
            )
        
        self.message_user(request, f"{updated} quote requests marked as completed.")
    mark_as_completed.short_description = "Mark selected requests as completed"
    
    def mark_as_declined(self, request, queryset):
        """Mark selected quote requests as declined"""
        updated = queryset.update(status='declined')
        self.message_user(request, f"{updated} quote requests marked as declined.")
    mark_as_declined.short_description = "Mark selected requests as declined"

    def has_add_permission(self, request):
        """Prevent adding quote requests manually via admin panel"""
        return False


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"


class QuoteRequestCounterMixin:
    """Mixin to add quote request counter to admin site"""
    
    def each_context(self, request):
        context = super().each_context(request)
        context['new_quote_count'] = QuoteRequest.objects.filter(status='new').count()
        return context


class CustomAdminSite(QuoteRequestCounterMixin, admin.AdminSite):
    """Custom admin site with dashboard"""

    site_header = 'Jazminn Administration'
    site_title = 'Jazminn Admin'
    index_title = 'Dashboard'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        """Custom admin dashboard view"""
        # Get quote request stats
        total_quotes = QuoteRequest.objects.count()
        new_quotes = QuoteRequest.objects.filter(status='new').count()
        
        # Get quotes from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_quotes = QuoteRequest.objects.filter(created_at__gte=thirty_days_ago).count()
        
        # Get unread notifications
        unread_notifications = AdminNotification.objects.filter(is_read=False)
        
        # Get installed apps
        from django.apps import apps
        installed_apps = [app.label for app in apps.get_app_configs()]
        
        context = {
            'title': 'Dashboard',
            'total_quotes': total_quotes,
            'new_quotes': new_quotes,
            'recent_quotes': recent_quotes,
            'unread_notifications': unread_notifications,
            'installed_apps': installed_apps,
            **self.each_context(request),
        }
        
        return TemplateResponse(request, 'admin/dashboard.html', context)

    def index(self, request, extra_context=None):
        """Override the default index to redirect to our dashboard"""
        return self.dashboard_view(request)


# Create an instance of the custom admin site
admin_site = CustomAdminSite(name='customadmin')

# Register models with the custom admin site if you want to use it
# Otherwise


# Register models with the custom admin site
admin_site.register(SiteSettings, SiteSettingsAdmin)
admin_site.register(MainMenu, MainMenuAdmin)
admin_site.register(SocialLink, SocialLinkAdmin)
admin_site.register(FooterSection, FooterSectionAdmin)
admin_site.register(ContactInfo, ContactInfoAdmin)
admin_site.register(Newsletter, NewsletterAdmin)
admin_site.register(HeroBanner, HeroBannerAdmin)
admin_site.register(WelcomeSection, WelcomeSectionAdmin)
admin_site.register(WhatWeDoItem, WhatWeDoItemAdmin)
admin_site.register(AboutBanner, AboutBannerAdmin)
admin_site.register(Achievement, AchievementAdmin)
admin_site.register(AboutSection, AboutSectionAdmin)
admin_site.register(TeamSection, TeamSectionAdmin)
admin_site.register(TeamMember, TeamMemberAdmin)
admin_site.register(ContactSection, ContactSectionAdmin)
admin_site.register(PolicyPage, PolicyPageAdmin)
admin_site.register(FAQItem, FAQItemAdmin)
admin_site.register(Certification, CertificationAdmin)
admin_site.register(QuoteRequest, QuoteRequestAdmin)
admin_site.register(AdminNotification, AdminNotificationAdmin)

