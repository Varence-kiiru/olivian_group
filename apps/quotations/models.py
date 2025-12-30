from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.core.models import TimeStampedModel
from apps.core.email_utils import EmailService
import json
import logging

logger = logging.getLogger(__name__)

class QuotationSequence(models.Model):
    """Model to track quotation sequence numbers"""
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)

    @classmethod
    def get_next_number(cls, year=None):
        if year is None:
            year = timezone.now().year

        sequence, created = cls.objects.get_or_create(year=year, defaults={'last_number': 0})
        sequence.last_number += 1
        sequence.save()
        return f"OG-QUO-{year}-{sequence.last_number:04d}"

class Customer(TimeStampedModel):
    """Customer model for quotations"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Kenya')

    # Business details
    company_name = models.CharField(max_length=200, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)
    business_type = models.CharField(
        max_length=20,
        choices=[
            ('individual', 'Individual'),
            ('business', 'Business'),
            ('government', 'Government'),
            ('ngo', 'NGO'),
        ],
        default='individual'
    )

    # System information
    monthly_consumption = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="kWh per month")
    average_monthly_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="KES")
    property_type = models.CharField(
        max_length=20,
        choices=[
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
            ('industrial', 'Industrial'),
        ],
        default='residential'
    )
    roof_type = models.CharField(
        max_length=20,
        choices=[
            ('iron_sheets', 'Iron Sheets'),
            ('tiles', 'Tiles'),
            ('concrete', 'Concrete'),
            ('asbestos', 'Asbestos'),
        ],
        default='iron_sheets'
    )
    roof_area = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Square meters")
    shading_issues = models.TextField(blank=True)

    # Loyalty system
    loyalty_points = models.IntegerField(default=0, help_text="Customer loyalty points")
    total_orders = models.IntegerField(default=0, help_text="Total number of orders")
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total amount spent")
    last_purchase_date = models.DateTimeField(null=True, blank=True, help_text="Date of last purchase")

    def __str__(self):
        return self.company_name if self.company_name else self.name

    def add_loyalty_points(self, points):
        """Add loyalty points to customer"""
        self.loyalty_points += points
        self.save(update_fields=['loyalty_points'])

    def redeem_loyalty_points(self, points):
        """Redeem loyalty points (subtract from total)"""
        if self.loyalty_points >= points:
            self.loyalty_points -= points
            self.save(update_fields=['loyalty_points'])
            return True
        return False

    def calculate_loyalty_points_from_purchase(self, amount):
        """Calculate loyalty points based on purchase amount"""
        # 1 point per 100 KES spent
        return int(amount / 100)

    def update_purchase_stats(self, amount, purchase_date=None):
        """Update customer purchase statistics"""
        if purchase_date is None:
            purchase_date = timezone.now()
        
        self.total_orders += 1
        self.total_spent += amount
        self.last_purchase_date = purchase_date
        
        # Add loyalty points
        points_earned = self.calculate_loyalty_points_from_purchase(amount)
        self.loyalty_points += points_earned

        self.save(update_fields=['total_orders', 'total_spent', 'last_purchase_date', 'loyalty_points'])
        return points_earned

    @property
    def loyalty_tier(self):
        """Determine customer loyalty tier based on points"""
        if self.loyalty_points >= 10000:
            return 'Platinum'
        elif self.loyalty_points >= 5000:
            return 'Gold'
        elif self.loyalty_points >= 1000:
            return 'Silver'
        else:
            return 'Bronze'

    @property
    def is_vip(self):
        """Check if customer is VIP (Gold or Platinum tier)"""
        return self.loyalty_tier in ['Gold', 'Platinum']

class Quotation(TimeStampedModel):
    QUOTATION_TYPES = [
        ('product_sale', 'Product Sale'),
        ('installation', 'Installation Service'),
        ('maintenance', 'Maintenance Contract'),
        ('consultation', 'Consultation Service'),
        ('custom_solution', 'Custom Solar Solution'),
    ]

    SYSTEM_TYPES = [
        ('grid_tied', 'Grid-Tied System'),
        ('off_grid', 'Off-Grid System'),
        ('hybrid', 'Hybrid System'),
        ('backup', 'Backup Power System'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Sale'),
    ]

    # Basic Information
    quotation_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    salesperson = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='quotations')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_quotations')
    quotation_type = models.CharField(max_length=20, choices=QUOTATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # System Specifications
    system_type = models.CharField(max_length=20, choices=SYSTEM_TYPES)
    system_capacity = models.DecimalField(max_digits=8, decimal_places=2, help_text="kW")
    estimated_generation = models.DecimalField(max_digits=10, decimal_places=2, help_text="kWh per month")
    installation_complexity = models.CharField(
        max_length=20,
        choices=[
            ('simple', 'Simple'),
            ('moderate', 'Moderate'),
            ('complex', 'Complex'),
        ],
        default='simple'
    )
    
    # Financial Information
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Savings Calculations
    estimated_monthly_savings = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_annual_savings = models.DecimalField(max_digits=10, decimal_places=2)
    payback_period_months = models.IntegerField()
    roi_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Financing Options
    financing_available = models.BooleanField(default=False)
    financing_options = models.JSONField(default=dict, blank=True)
    
    # Terms and Conditions
    validity_days = models.IntegerField(default=30)
    valid_until = models.DateField()
    payment_terms = models.TextField(default="50% deposit, 50% on completion")
    delivery_time = models.CharField(max_length=100, default="2-4 weeks")
    warranty_terms = models.TextField()
    
    # Additional Information
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['quotation_number']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['salesperson', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.quotation_number:
            self.quotation_number = QuotationSequence.get_next_number()
        
        if not self.valid_until:
            self.valid_until = timezone.now().date() + timezone.timedelta(days=self.validity_days)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Quotation {self.quotation_number}"
    
    def calculate_totals(self):
        """Calculate quotation totals"""
        items = self.items.all()
        self.subtotal = sum(item.total_price for item in items)
        
        # Apply discount
        if self.discount_percentage > 0:
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        
        # Calculate tax (VAT)
        from django.conf import settings
        vat_rate = Decimal(str(getattr(settings, 'VAT_RATE', 16.0)))
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = (taxable_amount * vat_rate) / 100
        
        # Calculate total
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount

        self.save()

    def is_expired(self):
        return timezone.now().date() > self.valid_until
    
    def can_be_converted(self):
        return self.status in ['sent', 'viewed', 'accepted'] and not self.is_expired()
    
    def convert_to_sale(self):
        """Convert quotation to sale/order"""
        if not self.can_be_converted():
            raise ValueError("Quotation cannot be converted to sale")
        
        # Import here to avoid circular imports
        from apps.ecommerce.models import Order, OrderItem
        
        # Create order
        order = Order.objects.create(
            customer=self.customer,
            quotation=self,
            order_type='quotation_conversion',
            status='pending',
            subtotal=self.subtotal,
            discount_amount=self.discount_amount,
            tax_amount=self.tax_amount,
            total_amount=self.total_amount,
            payment_terms=self.payment_terms,
            delivery_time=self.delivery_time,
        )
        
        # Create order items
        for quotation_item in self.items.all():
            OrderItem.objects.create(
                order=order,
                product=quotation_item.product,
                quantity=quotation_item.quantity,
                unit_price=quotation_item.unit_price,
                total_price=quotation_item.total_price,
                description=quotation_item.description,
            )
        
        # Update quotation status
        self.status = 'converted'
        self.save()
        
        return order

class QuotationItem(TimeStampedModel):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    
    # Item details
    item_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='pcs')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Technical specifications for the quote
    specifications = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Recalculate quotation totals
        self.quotation.calculate_totals()
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit}"

class QuotationTemplate(TimeStampedModel):
    """Pre-defined quotation templates for common solar systems"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    system_type = models.CharField(max_length=20, choices=Quotation.SYSTEM_TYPES)
    system_capacity_range = models.CharField(max_length=50, help_text="e.g., 5-10 kW")
    template_data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class QuotationRequest(TimeStampedModel):
    """Store customer quotation requests received via the 'Get Quotation' form"""

    SYSTEM_TYPES = [
        ('grid_tied', 'Grid-Tied System'),
        ('off_grid', 'Off-Grid System'),
        ('hybrid', 'Hybrid System'),
        ('backup', 'Backup Power System'),
        ('not_sure', 'Not Sure - Please Advise'),
    ]

    URGENCY_LEVELS = [
        ('low', 'Low - No Rush'),
        ('medium', 'Medium - Within 1-2 weeks'),
        ('high', 'High - Urgent (within 3-5 days)'),
        ('critical', 'Critical - ASAP'),
    ]

    STATUS_CHOICES = [
        ('new', 'New Request'),
        ('reviewed', 'Under Review'),
        ('contacted', 'Contact Initiated'),
        ('quotation_created', 'Quotation Created'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    def get_status_choices(self):
        """Return status choices for model instance"""
        return self.STATUS_CHOICES

    # Customer Information
    customer_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company_name = models.CharField(max_length=200, blank=True)

    # System Requirements
    system_type = models.CharField(max_length=20, choices=SYSTEM_TYPES, default='not_sure')
    system_requirements = models.TextField(help_text="Detailed description of the system requirements")
    estimated_budget = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Estimated budget in KES (optional)"
    )

    # Location and Installation
    location = models.CharField(max_length=100, help_text="City/Location")
    property_type = models.CharField(
        max_length=50,
        choices=[
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
            ('industrial', 'Industrial'),
            ('other', 'Other'),
        ],
        default='residential'
    )
    roof_access = models.CharField(
        max_length=50,
        choices=[
            ('easy', 'Easy Access'),
            ('difficult', 'Difficult Access'),
            ('limited', 'Limited Access'),
            ('not_sure', 'Not Sure'),
        ],
        default='not_sure'
    )

    # Urgency and Timeline
    urgency = models.CharField(max_length=20, choices=URGENCY_LEVELS, default='medium')
    preferred_contact_time = models.CharField(max_length=100, blank=True,
        help_text="Preferred time for contact (e.g., 'Morning', 'Afternoon')")

    # Processing Information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Staff member assigned to process this request")

    # Timeline tracking
    estimated_completion_days = models.IntegerField(default=3,
        help_text="Estimated days to complete the quotation")

    # Notes
    internal_notes = models.TextField(blank=True, help_text="Internal processing notes")
    customer_notes = models.TextField(blank=True, help_text="Additional notes from customer")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"Quotation Request - {self.customer_name} ({self.get_system_type_display()})"

    @property
    def urgency_color(self):
        """Get color class for urgency display"""
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'danger'
        }
        return colors.get(self.urgency, 'secondary')

    @property
    def status_color(self):
        """Get color class for status display"""
        colors = {
            'new': 'info',
            'reviewed': 'primary',
            'contacted': 'warning',
            'quotation_created': 'success',
            'completed': 'success',
            'cancelled': 'secondary'
        }
        return colors.get(self.status, 'secondary')

    @property
    def estimated_completion_date(self):
        """Calculate estimated completion date based on urgency"""
        days_map = {
            'low': 7,
            'medium': 5,
            'high': 3,
            'critical': 1
        }
        working_days = days_map.get(self.urgency, 3)
        return self.created_at.date() + timezone.timedelta(days=working_days)

    def send_request_received_email(self):
        """Send confirmation email to customer"""
        try:
            context = {
                'request': self,
                'customer_name': self.customer_name,
                'estimated_completion': self.estimated_completion_date,
                'system_type': self.get_system_type_display(),
                'urgency': self.get_urgency_display(),
            }

            success = EmailService.send_email_notification(
                'quotation_request_received',
                context,
                self.email,
                f'Quotation Request Received - {self.get_system_type_display()}'
            )
            return success
        except Exception as e:
            logger.error(f"Error sending request received email: {str(e)}")
            return False

    def send_management_notification(self):
        """Notify management team of new request"""
        try:
            # Get management users (admins, managers, sales managers)
            from django.contrib.auth import get_user_model
            User = get_user_model()

            management_emails = list(User.objects.filter(
                role__in=['super_admin', 'manager', 'sales_manager']
            ).values_list('email', flat=True))

            if not management_emails:
                # Fallback to default admin email
                management_emails = ['admin@olivian.co.ke']

            context = {
                'request': self,
                'customer_name': self.customer_name,
                'customer_email': self.email,
                'customer_phone': self.phone,
                'system_type': self.get_system_type_display(),
                'system_requirements': self.system_requirements,
                'urgency': self.get_urgency_display(),
                'estimated_budget': self.estimated_budget,
                'location': self.location,
                'status': self.get_status_display(),
                'request_url': f"https://olivian.co.ke/admin/quotations/quotationrequest/{self.pk}/change/",
            }

            success = EmailService.send_email_notification(
                'quotation_request_management',
                context,
                management_emails,
                f'New Quotation Request - {self.customer_name}',
                EmailService.EMAILS['noreply']
            )
            return success
        except Exception as e:
            logger.error(f"Error sending management notification: {str(e)}")
            return False

    def save(self, *args, **kwargs):
        is_new = not self.pk

        # Set estimated completion days based on urgency
        urgency_days = {
            'low': 7,
            'medium': 5,
            'high': 3,
            'critical': 1
        }
        self.estimated_completion_days = urgency_days.get(self.urgency, 3)

        super().save(*args, **kwargs)

        # Send emails on creation
        if is_new:
            try:
                # Send confirmation email to customer
                self.send_request_received_email()
                # Send notification to management
                self.send_management_notification()
            except Exception as e:
                logger.error(f"Error sending emails for quotation request {self.pk}: {str(e)}")


class QuotationFollowUp(TimeStampedModel):
    """Track follow-ups on quotations"""
    FOLLOW_UP_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('visit', 'Site Visit'),
        ('whatsapp', 'WhatsApp'),
    ]

    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='follow_ups')
    follow_up_type = models.CharField(max_length=20, choices=FOLLOW_UP_TYPES)
    notes = models.TextField()
    scheduled_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)  # Add this field

    @property
    def is_overdue(self):
        return not self.completed and self.scheduled_date < timezone.now()

    def send_reminder_email(self):
        """Send reminder email to assigned staff"""
        try:
            context = {
                'follow_up': self,
                'quotation': self.quotation,
                'customer': self.quotation.customer,
                'scheduled_date': self.scheduled_date,
                'follow_up_type': self.get_follow_up_type_display(),
                'notes': self.notes
            }

            success = EmailService.send_email_notification(
                'follow_up_reminder',
                context,
                self.created_by.email if self.created_by else self.quotation.salesperson.email,
                f'Follow-up Reminder: {self.quotation.quotation_number}'
            )

            if success:
                logger.info(f"Reminder email sent for follow-up {self.pk}")
            else:
                logger.error(f"Failed to send reminder email for follow-up {self.pk}")

            return success
        except Exception as e:
            logger.error(f"Error sending reminder email: {str(e)}")
            return False

    def save(self, *args, **kwargs):
        # Schedule reminder if this is a new follow-up
        is_new = not self.pk

        super().save(*args, **kwargs)

        if is_new:
            try:
                from django.core.cache import cache
                from datetime import timedelta

                # Schedule reminder for 1 hour before
                reminder_time = self.scheduled_date - timedelta(hours=1)
                cache_key = f'follow_up_reminder_{self.pk}'

                # Only set cache if reminder time is in the future
                if reminder_time > timezone.now():
                    timeout = (reminder_time - timezone.now()).seconds
                    cache.set(cache_key, True, timeout=timeout)
                    logger.info(f"Scheduled reminder for follow-up {self.pk}")
            except Exception as e:
                logger.error(f"Error scheduling reminder: {str(e)}")
