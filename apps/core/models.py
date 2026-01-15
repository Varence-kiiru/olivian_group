from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

User = get_user_model()

class TimeStampedModel(models.Model):
    """Base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CompanySettings(models.Model):
    """Company configuration and branding settings"""
    name = models.CharField(max_length=200, default='The Olivian Group Limited')
    email = models.EmailField(default='info@olivian.co.ke')
    phone = models.CharField(max_length=20, default='+254-719-728-666')
    website = models.URLField(default='https://olivian.co.ke')
    address = models.TextField(default='Kahawa Sukari Road, Nairobi, Kenya')

    # Company messaging
    tagline = models.CharField(max_length=200, default='Professional Solar Solutions', blank=True)
    about_description = models.TextField(default='Professional solar solutions for homes and businesses in Kenya.', blank=True)
    mission_statement = models.TextField(blank=True)
    vision_statement = models.TextField(blank=True)

    # SEO and Meta
    meta_description = models.TextField(blank=True, help_text="Meta description for SEO")
    meta_keywords = models.TextField(blank=True, help_text="Meta keywords for SEO")

    # Branding and Media
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    favicon = models.ImageField(upload_to='company/', blank=True, null=True)
    hero_image = models.ImageField(upload_to='company/', blank=True, null=True)
    about_hero_image = models.ImageField(upload_to='company/', blank=True, null=True)
    company_story_image = models.ImageField(upload_to='company/', blank=True, null=True)
    hero_title = models.CharField(max_length=200, blank=True,
                                  default="Save KES 150,000+ on Your First Year - Go Solar Today!")
    hero_subtitle = models.TextField(blank=True,
                                     default="Join 500+ Kenya families who cut electricity bills by 75% with professional solar installations. Complete system design, financing & installation - starts from KES 250,000.")
    hero_disclaimer = models.TextField(blank=True,
                                       default="Professional site assessment and 10-year warranty included. Payback period: 3-5 years.")

    # Urgency/offer elements
    urgency_banner_enabled = models.BooleanField(default=True,
                                                help_text="Enable/disable urgency banner")
    urgency_banner_text = models.CharField(max_length=200, blank=True,
                                           default="Limited Time: Get FREE installation assessment this month!")
    urgency_banner_end_date = models.DateField(null=True, blank=True,
                                               help_text="End date for the urgency banner")

    # Homepage sections
    testimonial_section_title = models.CharField(max_length=200, blank=True,
                                                 default="What Our Customers Say")
    testimonial_section_subtitle = models.TextField(blank=True,
                                                    default="Real stories from real customers who chose solar energy with {{ company.name }}")
    hero_featured_customers_count = models.CharField(max_length=50, default="500+",
                                                     help_text="Number shown in hero and testimonials")

    primary_color = models.CharField(max_length=7, default='#38b6ff')
    secondary_color = models.CharField(max_length=7, default='#ffffff')

    # Contact Information
    sales_email = models.EmailField(blank=True)
    sales_phone = models.CharField(max_length=20, blank=True)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # Business Hours
    business_hours_weekday = models.CharField(max_length=100, default='8:00 AM - 6:00 PM', blank=True)
    business_hours_saturday = models.CharField(max_length=100, default='9:00 AM - 4:00 PM', blank=True)
    business_hours_sunday = models.CharField(max_length=100, default='Closed', blank=True)
    showroom_hours_weekday = models.CharField(max_length=100, blank=True)
    showroom_hours_saturday = models.CharField(max_length=100, blank=True)
    showroom_hours_sunday = models.CharField(max_length=100, blank=True)

    # Support Hours
    support_hours_weekday = models.CharField(max_length=100, default='8:00 AM - 6:00 PM', blank=True,
                                           help_text="Support hours Monday-Friday")
    support_hours_saturday = models.CharField(max_length=100, default='9:00 AM - 4:00 PM', blank=True,
                                            help_text="Support hours Saturday")
    support_hours_sunday = models.CharField(max_length=100, default='Closed', blank=True,
                                          help_text="Support hours Sunday")
    emergency_support_available = models.BooleanField(default=True,
                                                    help_text="Whether emergency support is available outside normal hours")
    emergency_support_description = models.CharField(max_length=200, default='24/7 for active projects',
                                                   help_text="Description of emergency support availability")
    
    # Location & Maps
    google_maps_url = models.URLField(blank=True)
    google_maps_embed_url = models.URLField(blank=True)
    latitude = models.DecimalField(max_digits=18, decimal_places=14, null=True, blank=True,
                                  help_text="Latitude coordinate for company location")
    longitude = models.DecimalField(max_digits=18, decimal_places=14, null=True, blank=True,
                                   help_text="Longitude coordinate for company location")

    # Payment Integration - M-Pesa
    mpesa_business_name = models.CharField(max_length=100, blank=True)
    mpesa_paybill_number = models.CharField(max_length=20, blank=True)
    mpesa_account_number = models.CharField(max_length=50, blank=True)
    mpesa_phone_number = models.CharField(max_length=20, blank=True)
    mpesa_till_number = models.CharField(max_length=20, blank=True)
    
    # Business details  
    registration_number = models.CharField(max_length=50, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    
    # Statistics (for homepage display) - match existing DB field types
    projects_completed = models.CharField(max_length=10, default='100+')
    total_capacity = models.CharField(max_length=10, default='1MW+')
    customer_satisfaction = models.CharField(max_length=10, default='99.5%')
    cities_served = models.CharField(max_length=10, default='20+', help_text="Number of cities/areas served")
    co2_saved_tons = models.CharField(max_length=10, default='450+', help_text="Total CO2 saved in tons")
    founded_year = models.IntegerField(default=2020)
    
    # System settings
    default_currency = models.CharField(max_length=3, default='KES')
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.00, help_text="VAT rate percentage")
    installation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00, help_text="Installation service fee in KES")

    # Backup tracking
    last_backup_datetime = models.DateTimeField(null=True, blank=True, help_text="Date and time of the last successful system backup")
    
    class Meta:
        verbose_name = 'Company Settings'
        verbose_name_plural = 'Company Settings'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-adjust coordinate precision to fit database field limits"""
        # Get field definitions
        lat_field = self._meta.get_field('latitude')
        lng_field = self._meta.get_field('longitude')

        # Auto-adjust latitude precision if needed
        if self.latitude is not None:
            # Round to fit within decimal_places limit (14 decimal places)
            self.latitude = round(float(self.latitude), lat_field.decimal_places)

        # Auto-adjust longitude precision if needed
        if self.longitude is not None:
            # Round to fit within decimal_places limit (14 decimal places)
            self.longitude = round(float(self.longitude), lng_field.decimal_places)

        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get company settings singleton"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'name': 'The Olivian Group Limited',
                'email': 'info@olivian.co.ke',
                'phone': '+254-719-728-666',
                'website': 'https://olivian.co.ke',
                'address': 'Kahawa Sukari Road, Nairobi, Kenya',
                'primary_color': '#38b6ff',
                'secondary_color': '#ffffff',
            }
        )
        return settings
    
    def get_whatsapp_url(self):
        """Get WhatsApp URL"""
        phone = self.phone.replace('+', '').replace('-', '').replace(' ', '')
        return f"https://wa.me/{phone}"
    
    def get_social_media_links(self):
        """Get social media links"""
        return {
            'facebook': getattr(self, 'facebook_url', ''),
            'twitter': getattr(self, 'twitter_url', ''),
            'linkedin': getattr(self, 'linkedin_url', ''),
            'instagram': getattr(self, 'instagram_url', ''),
            'youtube': getattr(self, 'youtube_url', ''),
        }
    
    def has_social_media(self):
        """Check if any social media links are configured"""
        links = self.get_social_media_links()
        return any(links.values())


class ContactMessage(models.Model):
    """Contact form messages from website visitors"""
    PROPERTY_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('agricultural', 'Agricultural'),
        ('other', 'Other'),
    ]
    
    INQUIRY_TYPE_CHOICES = [
        ('general', 'General Inquiry'),
        ('quotation', 'Request Quote'),
        ('installation', 'Installation Question'),
        ('maintenance', 'Maintenance & Support'),
        ('financing', 'Financing Options'),
        ('commercial', 'Commercial Projects'),
        ('other', 'Other'),
    ]
    
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100, blank=True)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='residential')
    monthly_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Monthly electricity bill in KES')
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES, default='general')
    message = models.TextField()
    subscribe_newsletter = models.BooleanField(default=False)
    agree_privacy = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_read = models.BooleanField(default=False, help_text='Mark as read by admin')
    is_responded = models.BooleanField(default=False, help_text='Mark as responded to')
    admin_notes = models.TextField(blank=True, help_text='Internal notes for staff')
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.inquiry_type}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Currency(models.Model):
    """Supported currencies for the system"""
    code = models.CharField(max_length=3, unique=True, help_text="ISO currency code (e.g., USD, KES)")
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=5)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000, help_text="Rate to base currency (KES)")
    is_active = models.BooleanField(default=True)
    is_base = models.BooleanField(default=False, help_text="Base currency for calculations")
    
    class Meta:
        verbose_name_plural = 'Currencies'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class AuditLog(models.Model):
    """System audit log for tracking important actions"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('export', 'Export'),
        ('import', 'Import'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Use timestamp instead of inheriting from TimeStampedModel to avoid conflicts
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log Entry'
        verbose_name_plural = 'Audit Log Entries'
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} ({self.timestamp})"

class Notification(TimeStampedModel):
    """System notifications for users"""
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    NOTIFICATION_CATEGORIES = [
        ('inventory', 'Inventory'),
        ('quotation', 'Quotation'),
        ('project', 'Project'),
        ('order', 'Order'),
        ('budget', 'Budget'),
        ('system', 'System'),
        ('user', 'User'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    category = models.CharField(max_length=20, choices=NOTIFICATION_CATEGORIES, default='system')
    
    # Optional link to related object
    link_url = models.URLField(blank=True, null=True)
    link_text = models.CharField(max_length=100, blank=True, null=True)
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Email notification
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='info', category='system', link_url=None, link_text=None, send_email=False):
        """Create a new notification"""
        notification = cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            link_url=link_url,
            link_text=link_text
        )
        
        if send_email:
            from .email_utils import EmailService
            EmailService.send_notification_email(notification)
            
        return notification

class ActivityLog(models.Model):
    LOG_TYPES = [
        ('system', 'System'),
        ('user', 'User'),
        ('security', 'Security'),
        ('error', 'Error')
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ]
    
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info')
    metric = models.CharField(max_length=50, null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    message = models.TextField()
    description = models.TextField(blank=True)  # Added this field
    action = models.CharField(max_length=50, blank=True)  # Added this field
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                           on_delete=models.SET_NULL,
                           null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)  # Added this field

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.log_type} - {self.message[:50]}"

class TeamMember(TimeStampedModel):
    """Team member information for About page"""
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='team/', blank=True, null=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.position}"

class ProjectShowcase(TimeStampedModel):
    """Featured projects for website showcase"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='projects/', blank=True, null=True)
    location = models.CharField(max_length=100)
    capacity = models.CharField(max_length=50, help_text="e.g., 10kW, 5.5kW")
    project_type = models.CharField(
        max_length=20,
        choices=[
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
            ('industrial', 'Industrial'),
            ('government', 'Government'),
        ],
        default='residential'
    )
    completion_date = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ['order', '-completion_date']

    def __str__(self):
        return f"{self.title} - {self.location}"


class Testimonial(TimeStampedModel):
    """Customer testimonials for homepage showcase"""
    author_name = models.CharField(max_length=100, help_text="Full name of the testimonial author")
    author_initials = models.CharField(max_length=2, default='?', help_text="Initials for avatar (e.g., 'MK' for Mohammed K.)")
    location = models.CharField(max_length=100, blank=True, help_text="Location (e.g., 'Westlands, Nairobi')")
    quote = models.TextField(help_text="Testimonial quote text")
    rating = models.PositiveIntegerField(default=5, choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    is_featured = models.BooleanField(default=True, help_text="Display this testimonial on the homepage")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        return f"{self.author_name} - {self.location or 'Unknown Location'}"

    @property
    def short_quote(self):
        """Return truncated quote for previews"""
        words = self.quote.split()
        if len(words) > 25:
            return ' '.join(words[:25]) + '...'
        return self.quote


# Legacy models - keeping to prevent unwanted migrations
class BankAccount(models.Model):
    """Legacy bank account model - deprecated"""
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False  # Don't manage this table
    
    def __str__(self):
        return f"{self.name} - {self.account_number}"


class NewsletterSubscriber(models.Model):
    """Newsletter subscriber model for managing email subscriptions"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True, help_text="Whether this subscriber should receive newsletters")
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    subscription_source = models.CharField(max_length=50, default='website',
                                         help_text="Where they subscribed from")

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'

    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return f"{name} ({self.email})" if name else self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_unsubscribe_token(self):
        """Generate a secure token for unsubscribe links"""
        import hashlib
        import time
        # Create token from email and timestamp
        token_string = f"{self.email}{self.id}{int(time.time()) // 86400}"  # Daily token
        return hashlib.sha256(token_string.encode()).hexdigest()[:32]

    def get_unsubscribe_url(self):
        """Generate the full unsubscribe URL"""
        from django.urls import reverse
        from django.conf import settings
        token = self.get_unsubscribe_token()
        site_url = getattr(settings, 'SITE_URL', 'https://olivian.co.ke').rstrip('/')
        return f"{site_url}{reverse('core:unsubscribe', kwargs={'token': token, 'subscriber_id': self.id})}"


class NewsletterCampaign(models.Model):
    """Newsletter campaign model for creating and managing email campaigns"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    content = models.TextField(help_text="HTML content of the newsletter")
    preview_text = models.CharField(max_length=250, blank=True,
                                  help_text="Preview text shown in email clients")

    # Template and content settings
    template_type = models.CharField(max_length=50, default='default',
                                   help_text="Template type for rendering (default, promotional, etc.)")
    call_to_action_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="Text for the call-to-action button (e.g., 'Get a Free Consultation')"
    )
    call_to_action_url = models.URLField(blank=True, null=True,
                                       help_text="URL for the main call-to-action button", default='')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True,
                                       help_text="When to send this campaign")
    sent_at = models.DateTimeField(null=True, blank=True)

    # Analytics
    total_recipients = models.PositiveIntegerField(default=0)
    total_sent = models.PositiveIntegerField(default=0)
    total_failed = models.PositiveIntegerField(default=0)
    opens_count = models.PositiveIntegerField(default=0)
    clicks_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                 related_name='newsletter_campaigns')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter Campaign'
        verbose_name_plural = 'Newsletter Campaigns'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def can_send(self):
        """Check if this campaign can be sent"""
        return self.status in ['draft', 'scheduled'] and self.content.strip()

    def get_target_subscribers(self):
        """Get the target subscribers for this campaign"""
        return NewsletterSubscriber.objects.filter(is_active=True)

    @property
    def delivery_rate(self):
        try:
            recipients = float(self.total_recipients or 0)
            sent = float(self.total_sent or 0)
            if recipients == 0:
                return 0.0
            return (sent / recipients) * 100
        except (TypeError, ValueError):
            return 0.0

    @property
    def open_rate(self):
        """Calculate open rate percentage"""
        try:
            sent = float(self.total_sent or 0)
            opens = float(self.opens_count or 0)
            if sent == 0:
                return 0.0
            return (opens / sent) * 100
        except (TypeError, ValueError):
            return 0.0

    @property
    def click_rate(self):
        """Calculate click rate percentage"""
        try:
            sent = float(self.total_sent or 0)
            clicks = float(self.clicks_count or 0)
            if sent == 0:
                return 0.0
            return (clicks / sent) * 100
        except (TypeError, ValueError):
            return 0.0


class NewsletterSendLog(models.Model):
    """Log of newsletter sends to individual subscribers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]

    campaign = models.ForeignKey(NewsletterCampaign, on_delete=models.CASCADE,
                               related_name='send_logs')
    subscriber = models.ForeignKey(NewsletterSubscriber, on_delete=models.CASCADE,
                                 related_name='send_logs')

    # Status and delivery tracking
    delivery_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    email_address = models.EmailField(help_text="Email address the newsletter was sent to")
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)

    # Analytics tracking
    opened_at = models.DateTimeField(null=True, blank=True, help_text="When the email was opened")
    clicked_at = models.DateTimeField(null=True, blank=True, help_text="When links were clicked")
    unsubscribed_at = models.DateTimeField(null=True, blank=True, help_text="When unsubscribed via this email")

    # Keep legacy status field for backward compatibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ['campaign', 'subscriber']
        ordering = ['-sent_at']
        verbose_name = 'Newsletter Send Log'
        verbose_name_plural = 'Newsletter Send Logs'

    def __str__(self):
        return f"{self.campaign.title} -> {self.subscriber.email} ({self.get_delivery_status_display()})"

    def save(self, *args, **kwargs):
        # Sync delivery_status and status fields
        if self.delivery_status != self.status:
            self.status = self.delivery_status
        super().save(*args, **kwargs)


class LegalDocument(models.Model):
    """Base model for legal documents like Privacy Policy and Terms of Service"""
    DOCUMENT_TYPES = [
        ('privacy_policy', 'Privacy Policy'),
        ('terms_of_service', 'Terms of Service'),
        ('cookie_policy', 'Cookie Policy'),
        ('disclaimer', 'Disclaimer'),
        ('refund_policy', 'Refund Policy'),
        ('data_deletion', 'Data Deletion'),
    ]
    
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Full content of the legal document (HTML supported)")
    short_description = models.TextField(blank=True, help_text="Brief summary for meta descriptions")
    
    last_updated = models.DateTimeField(auto_now=True)
    version = models.CharField(max_length=10, default='1.0', help_text="Document version for tracking changes")
    is_active = models.BooleanField(default=True, help_text="Whether this document is currently active")
    effective_date = models.DateField(help_text="Date when this version becomes effective")
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-last_updated']
        verbose_name = 'Legal Document'
        verbose_name_plural = 'Legal Documents'
    
    def __str__(self):
        return f"{self.get_document_type_display()} v{self.version}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('core:legal_document', kwargs={'doc_type': self.document_type})
    
    @classmethod
    def get_privacy_policy(cls):
        """Get the active privacy policy"""
        return cls.objects.filter(document_type='privacy_policy', is_active=True).first()

    @classmethod
    def get_terms_of_service(cls):
        """Get the active terms of service"""
        return cls.objects.filter(document_type='terms_of_service', is_active=True).first()

    @classmethod
    def get_data_deletion(cls):
        """Get the active data deletion document"""
        return cls.objects.filter(document_type='data_deletion', is_active=True).first()

    @classmethod
    def get_disclaimer(cls):
        """Get the active disclaimer document"""
        return cls.objects.filter(document_type='disclaimer', is_active=True).first()

    @classmethod
    def get_refund_policy(cls):
        """Get the active refund policy document"""
        return cls.objects.filter(document_type='refund_policy', is_active=True).first()


class CookieConsent(models.Model):
    """Model to store user cookie consent preferences"""
    
    # Cookie categories
    COOKIE_CATEGORIES = [
        ('essential', 'Essential'),
        ('analytics', 'Analytics'),
        ('marketing', 'Marketing'),
        ('preferences', 'Preferences'),
        ('social', 'Social Media'),
    ]
    
    # Consent choices
    CONSENT_CHOICES = [
        ('granted', 'Granted'),
        ('denied', 'Denied'),
        ('pending', 'Pending'),
    ]
    
    # Identifier (IP + User Agent hash or user ID)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    identifier = models.CharField(max_length=64, help_text="Anonymous identifier for non-logged users")
    
    # Consent preferences for each category
    essential_consent = models.CharField(max_length=10, choices=CONSENT_CHOICES, default='pending')
    analytics_consent = models.CharField(max_length=10, choices=CONSENT_CHOICES, default='pending')
    marketing_consent = models.CharField(max_length=10, choices=CONSENT_CHOICES, default='pending')
    preferences_consent = models.CharField(max_length=10, choices=CONSENT_CHOICES, default='pending')
    social_consent = models.CharField(max_length=10, choices=CONSENT_CHOICES, default='pending')
    
    # Metadata
    consent_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Consent version (to track policy changes)
    consent_version = models.CharField(max_length=10, default='1.0')
    
    class Meta:
        ordering = ['-consent_date']
        unique_together = ['user', 'identifier']
        verbose_name = 'Cookie Consent'
        verbose_name_plural = 'Cookie Consents'
    
    def __str__(self):
        if self.user:
            return f"Cookie consent for {self.user.email}"
        return f"Cookie consent for {self.identifier[:10]}..."
    
    @property
    def has_analytics_consent(self):
        return self.analytics_consent == 'granted'
    
    @property
    def has_marketing_consent(self):
        return self.marketing_consent == 'granted'
    
    @property
    def has_preferences_consent(self):
        return self.preferences_consent == 'granted'
    
    @property
    def has_social_consent(self):
        return self.social_consent == 'granted'
    
    @classmethod
    def get_or_create_consent(cls, user=None, identifier=None, ip_address=None, user_agent=''):
        """Get or create cookie consent for a user or anonymous visitor"""
        if user:
            consent, created = cls.objects.get_or_create(
                user=user,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'essential_consent': 'granted'  # Essential cookies are always granted
                }
            )
        else:
            consent, created = cls.objects.get_or_create(
                identifier=identifier,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'essential_consent': 'granted'  # Essential cookies are always granted
                }
            )
        return consent, created


class CookieCategory(models.Model):
    """Model to define cookie categories and their descriptions"""
    
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    is_essential = models.BooleanField(default=False, help_text="Essential cookies cannot be disabled")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Cookie Category'
        verbose_name_plural = 'Cookie Categories'
    
    def __str__(self):
        return self.display_name


class CookieDetail(models.Model):
    """Model to store details about specific cookies"""

    name = models.CharField(max_length=100)
    category = models.ForeignKey(CookieCategory, on_delete=models.CASCADE, related_name='cookies')
    purpose = models.TextField(help_text="What this cookie is used for")
    duration = models.CharField(max_length=100, help_text="How long the cookie lasts")
    third_party = models.BooleanField(default=False, help_text="Is this a third-party cookie?")
    provider = models.CharField(max_length=100, blank=True, help_text="Who sets this cookie")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Cookie Detail'
        verbose_name_plural = 'Cookie Details'

    def __str__(self):
        return f"{self.name} ({self.category.display_name})"


class KenyanHoliday(TimeStampedModel):
    """Model to define Kenyan holidays for automated offers"""

    HOLIDAY_TYPES = [
        ('national', 'National Holiday'),
        ('religious', 'Religious Holiday'),
        ('cultural', 'Cultural Holiday'),
    ]

    DATE_TYPES = [
        ('fixed', 'Fixed Date'),
        ('variable', 'Variable Date'),
        ('calculated', 'Calculated Date'),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="Name of the holiday")
    holiday_type = models.CharField(max_length=20, choices=HOLIDAY_TYPES, default='national')
    date_type = models.CharField(max_length=20, choices=DATE_TYPES, default='fixed')

    # For fixed dates
    fixed_month = models.IntegerField(null=True, blank=True, help_text="Month (1-12) for fixed holidays")
    fixed_day = models.IntegerField(null=True, blank=True, help_text="Day for fixed holidays")

    # For variable holidays
    lead_time_days = models.IntegerField(default=14, help_text="Days before holiday to start showing offers")
    duration_days = models.IntegerField(default=7, help_text="How many days the holiday period lasts")

    # Additional metadata
    description = models.TextField(blank=True, help_text="Description of the holiday")
    is_active = models.BooleanField(default=True, help_text="Enable/disable this holiday for offers")
    emoji = models.CharField(max_length=10, blank=True, help_text="Emoji to represent the holiday")

    class Meta:
        ordering = ['fixed_month', 'fixed_day', 'name']
        verbose_name = 'Kenyan Holiday'
        verbose_name_plural = 'Kenyan Holidays'

    def __str__(self):
        return f"{self.emoji} {self.name}"

    def get_holiday_period(self, year=None):
        """Calculate the holiday period for a given year"""
        from datetime import date, timedelta

        if year is None:
            year = date.today().year

        if self.date_type == 'fixed' and self.fixed_month and self.fixed_day:
            # Fixed date holiday
            holiday_date = date(year, self.fixed_month, self.fixed_day)
            start_date = holiday_date - timedelta(days=self.lead_time_days)
            end_date = holiday_date + timedelta(days=self.duration_days - 1)
            return start_date, end_date

        elif self.name == 'Christmas/New Year':
            # Special handling for Christmas/New Year season
            christmas = date(year, 12, 25)
            new_year = date(year + 1, 1, 1)
            start_date = christmas - timedelta(days=self.lead_time_days)
            end_date = new_year + timedelta(days=self.duration_days - 1)
            return start_date, end_date

        elif self.name == 'Easter':
            # Calculate Easter using dateutil or approximation
            try:
                import dateutil.easter
                easter_sunday = dateutil.easter.easter(year)
            except ImportError:
                # Fallback approximation (not perfectly accurate)
                a = year % 19
                b = year // 100
                c = year % 100
                d = b // 4
                e = b % 4
                f = (b + 8) // 25
                g = (b - f + 1) // 3
                h = (19 * a + b - d - g + 15) % 30
                i = c // 4
                k = c % 4
                l = (32 + 2 * e + 2 * i - h - k) % 7
                m = (a + 11 * h + 22 * l) // 451
                month = (h + l - 7 * m + 114) // 31
                day = ((h + l - 7 * m + 114) % 31) + 1
                easter_sunday = date(year, month, day)

            # Good Friday to Easter Monday
            good_friday = easter_sunday - timedelta(days=2)
            easter_monday = easter_sunday + timedelta(days=1)
            start_date = good_friday - timedelta(days=self.lead_time_days)
            end_date = easter_monday
            return start_date, end_date

        elif self.name == 'Eid al-Fitr':
            # Approximate Eid al-Fitr (after Ramadan)
            # This is a rough approximation - ideally would use Islamic calendar
            eid_approx = date(year, 4, 21)  # Approximate for 2025
            start_date = eid_approx - timedelta(days=self.lead_time_days)
            end_date = eid_approx + timedelta(days=self.duration_days - 1)
            return start_date, end_date

        elif self.name == 'Eid al-Adha':
            # Approximate Eid al-Adha
            eid_approx = date(year, 6, 17)  # Approximate for 2025
            start_date = eid_approx - timedelta(days=self.lead_time_days)
            end_date = eid_approx + timedelta(days=self.duration_days - 1)
            return start_date, end_date

        return None, None

    @property
    def is_currently_active(self):
        """Check if this holiday is currently active"""
        from datetime import date
        today = date.today()
        start_date, end_date = self.get_holiday_period(today.year)

        if start_date and end_date:
            return start_date <= today <= end_date

        return False

    @property
    def end_date(self):
        """Get the end date for countdowns"""
        from datetime import date
        today = date.today()
        start_date, end_date = self.get_holiday_period(today.year)

        if end_date:
            return end_date.strftime('%Y-%m-%d')
        return today.strftime('%Y-%m-%d')  # Fallback to today if no end date


class HolidayOffer(TimeStampedModel):
    """Holiday-specific offers that automatically display during holiday periods"""

    holiday = models.ForeignKey(KenyanHoliday, on_delete=models.CASCADE, related_name='offers')

    # Offer details
    banner_text = models.CharField(max_length=200, help_text="Text to display in the banner")
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Discount percentage (e.g., 10.00 for 10%)"
    )
    discount_description = models.TextField(blank=True, help_text="Detailed discount information")
    special_benefits = models.TextField(blank=True, help_text="Additional benefits or terms")

    # Timing overrides (optional)
    custom_lead_days = models.IntegerField(null=True, blank=True,
                                         help_text="Override holiday's default lead time")
    custom_duration_days = models.IntegerField(null=True, blank=True,
                                             help_text="Override holiday's default duration")

    # Status and priority
    is_active = models.BooleanField(default=True, help_text="Enable/disable this offer")
    priority = models.IntegerField(default=1, help_text="Higher priority wins for overlapping holidays")
    order = models.IntegerField(default=0, help_text="Display order for multiple offers")

    class Meta:
        ordering = ['-priority', 'order', '-created_at']
        verbose_name = 'Holiday Offer'
        verbose_name_plural = 'Holiday Offers'

    def __str__(self):
        return f"{self.holiday.name}: {self.banner_text[:50]}"

    @property
    def effective_lead_days(self):
        """Get effective lead time (custom or holiday default)"""
        return self.custom_lead_days or self.holiday.lead_time_days

    @property
    def effective_duration_days(self):
        """Get effective duration (custom or holiday default)"""
        return self.custom_duration_days or self.holiday.duration_days

    def is_currently_applicable(self):
        """Check if this offer should be shown right now"""
        return self.is_active and self.holiday.is_currently_active


class VideoTutorial(TimeStampedModel):
    """Video tutorials for the help page"""

    VIDEO_TYPES = [
        ('youtube', 'YouTube'),
        ('vimeo', 'Vimeo'),
        ('direct', 'Direct Video URL'),
        ('embed', 'Embed Code'),
    ]

    title = models.CharField(max_length=200, help_text="Title of the video tutorial")
    description = models.TextField(help_text="Brief description of what the tutorial covers")
    video_type = models.CharField(max_length=20, choices=VIDEO_TYPES, default='youtube',
                                help_text="Type of video hosting platform")
    video_url = models.URLField(help_text="Video URL (YouTube, Vimeo, or direct video link)")
    embed_code = models.TextField(blank=True, help_text="Custom embed code (for embed type)")
    thumbnail = models.ImageField(upload_to='tutorials/', blank=True, null=True,
                                help_text="Custom thumbnail image (optional)")
    duration = models.CharField(max_length=20, blank=True, help_text="Video duration (e.g., '5 minutes')")
    category = models.CharField(max_length=100, blank=True, help_text="Tutorial category (e.g., 'Getting Started', 'Advanced')")
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags for filtering")
    is_featured = models.BooleanField(default=False, help_text="Feature this tutorial prominently")
    is_active = models.BooleanField(default=True, help_text="Whether this tutorial is visible on the help page")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")

    class Meta:
        ordering = ['order', '-is_featured', 'title']
        verbose_name = 'Video Tutorial'
        verbose_name_plural = 'Video Tutorials'

    def __str__(self):
        return self.title

    def get_video_id(self):
        """Extract video ID from URL for embedding"""
        if self.video_type == 'youtube':
            # Extract YouTube video ID
            import re
            patterns = [
                r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            ]
            for pattern in patterns:
                match = re.search(pattern, self.video_url)
                if match:
                    return match.group(1)
        elif self.video_type == 'vimeo':
            # Extract Vimeo video ID
            import re
            match = re.search(r'vimeo\.com\/(\d+)', self.video_url)
            if match:
                return match.group(1)
        return None

    def get_embed_url(self):
        """Get embed URL for iframe"""
        if self.video_type == 'youtube':
            video_id = self.get_video_id()
            return f'https://www.youtube.com/embed/{video_id}' if video_id else None
        elif self.video_type == 'vimeo':
            video_id = self.get_video_id()
            return f'https://player.vimeo.com/video/{video_id}' if video_id else None
        elif self.video_type == 'direct':
            return self.video_url
        return None

    def get_thumbnail_url(self):
        """Get thumbnail URL for display"""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.video_type == 'youtube':
            video_id = self.get_video_id()
            return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg' if video_id else None
        elif self.video_type == 'vimeo':
            # Vimeo thumbnails require API call, return None for now
            return None
        return None


class ServiceArea(TimeStampedModel):
    """Service areas and coverage information for different locations"""

    COVERAGE_TYPES = [
        ('primary', 'Primary Service Area'),
        ('extended', 'Extended Service Area'),
        ('planned', 'Planned Expansion'),
    ]

    AREA_TYPES = [
        ('county', 'County'),
        ('town', 'Town/City'),
        ('region', 'Region'),
    ]

    name = models.CharField(max_length=100, help_text="Name of the area (e.g., Nairobi, Kiambu)")
    area_type = models.CharField(max_length=20, choices=AREA_TYPES, default='county')
    coverage_type = models.CharField(max_length=20, choices=COVERAGE_TYPES, default='primary')
    county = models.CharField(max_length=100, blank=True, help_text="County name if applicable")
    description = models.TextField(blank=True, help_text="Additional information about service in this area")
    estimated_response_time = models.CharField(max_length=50, blank=True,
                                             help_text="Estimated response/installation time")
    contact_person = models.CharField(max_length=100, blank=True, help_text="Local contact person")
    contact_phone = models.CharField(max_length=20, blank=True, help_text="Local contact phone")
    is_active = models.BooleanField(default=True, help_text="Whether this area is currently serviced")
    order = models.IntegerField(default=0, help_text="Display order")

    # Geographic fields for Google Maps integration
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True,
                                  help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True,
                                   help_text="Longitude coordinate")
    boundary_geojson = models.JSONField(null=True, blank=True,
                                       help_text="GeoJSON polygon defining the service area boundary")
    center_point = models.JSONField(null=True, blank=True,
                                   help_text="Center point coordinates [lat, lng] for area")
    radius_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                   help_text="Service radius in kilometers (for circular areas)")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Service Area'
        verbose_name_plural = 'Service Areas'
        unique_together = ['name', 'area_type']

    def __str__(self):
        return f"{self.name} ({self.get_coverage_type_display()})"

    @property
    def display_name(self):
        """Get display name with area type"""
        return f"{self.name} ({self.get_area_type_display()})"

    @classmethod
    def check_coverage(cls, location):
        """Check if a location is covered and return coverage info with geographic intelligence"""
        if not location:
            return {
                'covered': False,
                'coverage_type': None,
                'area': None,
                'distance_km': None,
                'message': 'Please enter a location to check coverage.'
            }

        location_lower = location.lower().strip()

        # Try exact match first
        area = cls.objects.filter(
            is_active=True,
            name__iexact=location_lower
        ).first()

        if area:
            return {
                'covered': True,
                'coverage_type': area.coverage_type,
                'area': area,
                'distance_km': 0,
                'message': f"Great! {area.name} is in our {area.get_coverage_type_display().lower()}."
            }

        # Try partial match on name
        areas = cls.objects.filter(
            is_active=True,
            name__icontains=location_lower
        )

        if areas.exists():
            area = areas.first()
            return {
                'covered': True,
                'coverage_type': area.coverage_type,
                'area': area,
                'distance_km': 0,
                'message': f"Great! {area.name} is in our {area.get_coverage_type_display().lower()}."
            }

        # Check if it's a county match - geographic inheritance
        county_areas = cls.objects.filter(
            is_active=True,
            county__icontains=location_lower
        )

        if county_areas.exists():
            area = county_areas.first()
            return {
                'covered': True,
                'coverage_type': area.coverage_type,
                'area': area,
                'distance_km': 0,
                'message': f"Great! {area.name} is in our {area.get_coverage_type_display().lower()}. As a location within {area.county}, you can benefit from our services."
            }

        # Geographic proximity check - geocode the location and find nearest areas
        from .geographic_utils import get_geographic_service

        geo_service = get_geographic_service()
        geo_result = geo_service.geocode_location(f"{location}, Kenya")

        if geo_result:
            user_lat = geo_result['latitude']
            user_lng = geo_result['longitude']

            # Check point-in-polygon for areas with boundaries
            all_active_areas = cls.objects.filter(is_active=True)

            for area in all_active_areas:
                # Check polygon boundaries first
                if area.boundary_geojson:
                    try:
                        import json
                        boundary_data = json.loads(area.boundary_geojson) if isinstance(area.boundary_geojson, str) else area.boundary_geojson
                        if geo_service.is_point_in_polygon(user_lat, user_lng, boundary_data):
                            return {
                                'covered': True,
                                'coverage_type': area.coverage_type,
                                'area': area,
                                'distance_km': 0,
                                'message': f"Great! Your location is within our {area.get_coverage_type_display().lower()} area for {area.name}."
                            }
                    except Exception:
                        pass  # Continue to next checks

                # Check circular boundaries
                if area.radius_km and area.latitude and area.longitude:
                    if geo_service.is_point_in_circle(user_lat, user_lng, area.latitude, area.longitude, area.radius_km):
                        return {
                            'covered': True,
                            'coverage_type': area.coverage_type,
                            'area': area,
                            'distance_km': 0,
                            'message': f"Great! Your location is within our {area.get_coverage_type_display().lower()} area for {area.name}."
                        }

            # Check extended coverage areas with geographic proximity
            extended_areas = cls.objects.filter(
                is_active=True,
                coverage_type='extended'
            )

            # Simple fuzzy matching for extended areas
            for area in extended_areas:
                if (location_lower in area.name.lower() or
                    (area.county and location_lower in area.county.lower())):
                    return {
                        'covered': True,
                        'coverage_type': 'extended',
                        'area': area,
                        'distance_km': 0,
                        'message': f"{area.name} is in our extended service area. Contact us to discuss your specific location."
                    }

            # Find nearest service area
            nearest = geo_service.find_nearest_service_area(user_lat, user_lng, all_active_areas)
            if nearest:
                area = nearest['area']
                distance = nearest['distance_km']

                if distance <= 50:  # Within 50km, suggest extended coverage discussion
                    return {
                        'covered': False,
                        'coverage_type': 'nearby',
                        'area': area,
                        'distance_km': distance,
                        'message': f"Your location is {distance:.1f}km from our nearest service area in {area.name}. We can discuss extended coverage options for your location."
                    }
                else:
                    return {
                        'covered': False,
                        'coverage_type': None,
                        'area': None,
                        'distance_km': distance,
                        'message': f"We're currently expanding our services. Your location is {distance:.1f}km from our nearest service area in {area.name}, but we'd love to discuss bringing solar solutions to your area."
                    }

        # Fallback to text-based extended area matching
        extended_areas = cls.objects.filter(
            is_active=True,
            coverage_type='extended'
        )

        # Simple fuzzy matching for extended areas
        for area in extended_areas:
            if (location_lower in area.name.lower() or
                (area.county and location_lower in area.county.lower())):
                return {
                    'covered': True,
                    'coverage_type': 'extended',
                    'area': area,
                    'distance_km': 0,
                    'message': f"{area.name} is in our extended service area. Contact us to discuss your specific location."
                }

        # Not covered
        return {
            'covered': False,
            'coverage_type': None,
            'area': None,
            'distance_km': None,
            'message': f"We're currently expanding our services. {location.title()} is not in our current service area, but we'd love to discuss bringing solar solutions to your location."
        }

    @classmethod
    def get_primary_areas(cls):
        """Get all primary service areas"""
        return cls.objects.filter(is_active=True, coverage_type='primary').order_by('order', 'name')

    @classmethod
    def get_extended_areas(cls):
        """Get all extended service areas"""
        return cls.objects.filter(is_active=True, coverage_type='extended').order_by('order', 'name')

    @classmethod
    def get_all_active_areas(cls):
        """Get all active service areas"""
        return cls.objects.filter(is_active=True).order_by('order', 'name')
