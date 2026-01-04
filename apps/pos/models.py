from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Store(models.Model):
    """Physical store locations"""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="Store code (e.g., ST001)")
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)

    # Contact information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_stores')

    # Settings
    is_active = models.BooleanField(default=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    currency = models.CharField(max_length=3, default='KES')

    # Business hours
    opening_time = models.TimeField(default='08:00')
    closing_time = models.TimeField(default='18:00')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_absolute_url(self):
        return reverse('pos:store_detail', kwargs={'pk': self.pk})


class Terminal(models.Model):
    """POS terminals within stores"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, help_text="Terminal identifier (e.g., TERM001)")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='terminals')

    # Hardware details
    device_id = models.CharField(max_length=100, blank=True, help_text="Hardware device ID")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True, help_text="MAC address (XX:XX:XX:XX:XX:XX)")

    # Settings
    is_active = models.BooleanField(default=True)
    requires_manager_approval = models.BooleanField(default=False, help_text="Require manager approval for certain operations")
    cash_drawer_enabled = models.BooleanField(default=True)
    receipt_printer_enabled = models.BooleanField(default=True)
    barcode_scanner_enabled = models.BooleanField(default=True)
    
    # Current session
    current_cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_terminal')
    session_start = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['store', 'name']
        verbose_name = 'POS Terminal'
        verbose_name_plural = 'POS Terminals'

    def __str__(self):
        return f"{self.store.name} - {self.name}"
    
    @property
    def is_in_session(self):
        return self.current_cashier is not None and self.session_start is not None


class CashierSession(models.Model):
    """Cashier work sessions"""
    SESSION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('suspended', 'Suspended'),
    ]
    
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cashier_sessions')
    terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE, related_name='sessions')
    
    # Session details
    session_number = models.CharField(max_length=50, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES, default='active')
    
    # Timing
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Cash management
    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    closing_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cash_variance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Notes
    opening_notes = models.TextField(blank=True)
    closing_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Cashier Session'
        verbose_name_plural = 'Cashier Sessions'
    
    def __str__(self):
        return f"{self.session_number} - {self.cashier.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.session_number:
            # Generate session number: SESS-YYYYMMDD-XXXX
            date_str = timezone.now().strftime('%Y%m%d')
            count = CashierSession.objects.filter(start_time__date=timezone.now().date()).count() + 1
            self.session_number = f"SESS-{date_str}-{count:04d}"
        super().save(*args, **kwargs)
    
    @property
    def duration(self):
        """Session duration"""
        end = self.end_time or timezone.now()
        return end - self.start_time
    
    @property
    def total_sales(self):
        """Total sales for this session"""
        return self.sales.aggregate(
            total=models.Sum('grand_total')
        )['total'] or Decimal('0.00')


# POS now uses unified Customer model from apps.quotations.models


class SaleSequence(models.Model):
    """Model to track sale sequence numbers"""
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)
    
    @classmethod
    def get_next_number(cls, year=None):
        if year is None:
            year = timezone.now().year
        
        sequence, created = cls.objects.get_or_create(year=year, defaults={'last_number': 0})
        sequence.last_number += 1
        sequence.save()
        return f"OG-SALE-{year}-{sequence.last_number:04d}"


class Sale(models.Model):
    """POS sales transactions"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit', 'Credit'),
        ('mixed', 'Mixed Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('voided', 'Voided'),
    ]
    
    # Transaction details
    sale_number = models.CharField(max_length=50, unique=True, editable=False)
    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Relationships
    session = models.ForeignKey(CashierSession, on_delete=models.CASCADE, related_name='sales')
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pos_sales')
    customer = models.ForeignKey('quotations.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_purchases')
    
    # Status and payment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    
    # Financial details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Payment details
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Transaction references
    mpesa_transaction_id = models.CharField(max_length=50, blank=True)
    card_reference = models.CharField(max_length=50, blank=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    
    # Metadata
    transaction_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-transaction_time']
        verbose_name = 'Sale'
        verbose_name_plural = 'Sales'
    
    def __str__(self):
        return f"{self.receipt_number} - KES {self.grand_total}"
    
    def save(self, *args, **kwargs):
        # Generate sale number using sequence system
        if not self.sale_number:
            self.sale_number = SaleSequence.get_next_number()
            
        # Generate receipt number using same sequence but different prefix
        if not self.receipt_number:
            year = timezone.now().year
            # Get the current number from sale sequence for receipt numbering
            sequence = SaleSequence.objects.filter(year=year).first()
            if sequence:
                self.receipt_number = f"OG-RCP-{year}-{sequence.last_number:04d}"
            else:
                self.receipt_number = f"OG-RCP-{year}-0001"
        
        # Calculate totals if not already set
        if self.pk is None:  # Only for new sales
            # Calculate from items if subtotal is 0
            if not self.subtotal or self.subtotal == 0:
                self.calculate_totals()
            
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate sale totals from items using VAT-inclusive approach"""
        if self.pk:  # Only if sale exists
            # Sum all line totals (these are VAT-inclusive)
            vat_inclusive_total = sum(item.line_total for item in self.items.all())
            
            # Calculate VAT backwards from inclusive prices
            from apps.core.models import CompanySettings
            company_settings = CompanySettings.get_settings()
            vat_rate = Decimal(str(company_settings.vat_rate))
            vat_multiplier = Decimal('1') + (vat_rate / Decimal('100'))
            
            # Extract VAT amount and ex-VAT subtotal
            self.subtotal = vat_inclusive_total / vat_multiplier  # Ex-VAT subtotal
            self.tax_amount = vat_inclusive_total - self.subtotal  # VAT amount
            self.grand_total = vat_inclusive_total - self.discount_amount  # VAT-inclusive minus discount
        else:
            # For new sales without items yet, keep existing values
            if not self.subtotal:
                self.subtotal = Decimal('0.00')
            if not self.tax_amount:
                # Calculate VAT backwards if subtotal is provided
                from apps.core.models import CompanySettings
                company_settings = CompanySettings.get_settings()
                vat_rate = Decimal(str(company_settings.vat_rate))
                vat_multiplier = Decimal('1') + (vat_rate / Decimal('100'))
                
                # If subtotal is ex-VAT, we need to calculate inclusive total first
                vat_inclusive = self.subtotal * vat_multiplier
                self.tax_amount = vat_inclusive - self.subtotal
            if not self.grand_total:
                self.grand_total = self.subtotal + self.tax_amount
    
    def get_absolute_url(self):
        return reverse('pos:sale_detail', kwargs={'pk': self.pk})


class SaleItem(models.Model):
    """Individual items in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='pos_sale_items')
    
    # Product details (captured at time of sale)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Tax
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('16.00'))  # Kenya VAT
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Totals
    line_total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Sale Item'
        verbose_name_plural = 'Sale Items'
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        from apps.core.models import CompanySettings
        
        # Calculate discount amount
        self.discount_amount = (self.unit_price * self.quantity * self.discount_percentage / 100)
        
        # VAT-inclusive line total (prices include VAT)
        vat_inclusive_total = (self.unit_price * self.quantity) - self.discount_amount
        
        # Calculate VAT backwards (prices are VAT inclusive)
        company_settings = CompanySettings.get_settings()
        vat_rate = Decimal(str(company_settings.vat_rate))
        vat_multiplier = Decimal('1') + (vat_rate / Decimal('100'))
        
        # Extract VAT from the inclusive price
        line_total_ex_vat = vat_inclusive_total / vat_multiplier
        self.tax_amount = vat_inclusive_total - line_total_ex_vat
        self.line_total = vat_inclusive_total  # This is the VAT-inclusive total
        
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment records for sales"""
    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # Amount details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='KES')
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # Payment references
    transaction_id = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # M-Pesa specific
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    mpesa_phone_number = models.CharField(max_length=20, blank=True)
    
    # Card specific
    card_last_four = models.CharField(max_length=4, blank=True)
    card_type = models.CharField(max_length=20, blank=True)  # Visa, Mastercard, etc.
    
    # Additional details
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-processed_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - KES {self.amount}"


class Discount(models.Model):
    """Discount schemes for POS"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('buy_x_get_y', 'Buy X Get Y'),
    ]
    
    APPLIES_TO_CHOICES = [
        ('entire_sale', 'Entire Sale'),
        ('specific_products', 'Specific Products'),
        ('product_categories', 'Product Categories'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True, help_text="Discount code")
    description = models.TextField(blank=True)
    
    # Discount configuration
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    applies_to = models.CharField(max_length=20, choices=APPLIES_TO_CHOICES)
    
    # Values
    percentage_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Buy X Get Y
    buy_quantity = models.PositiveIntegerField(null=True, blank=True)
    get_quantity = models.PositiveIntegerField(null=True, blank=True)
    
    # Restrictions
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of uses")
    current_usage = models.PositiveIntegerField(default=0)
    
    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    requires_manager_approval = models.BooleanField(default=False)
    
    # Relationships
    applicable_products = models.ManyToManyField('products.Product', blank=True)
    applicable_categories = models.ManyToManyField('products.ProductCategory', blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='discounts_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def is_valid(self):
        """Check if discount is currently valid"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        if self.usage_limit and self.current_usage >= self.usage_limit:
            return False
        return True


class CashMovement(models.Model):
    """Cash drawer movements"""
    MOVEMENT_TYPE_CHOICES = [
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('payout', 'Payout'),
        ('float_add', 'Float Addition'),
        ('drop', 'Cash Drop'),
    ]
    
    session = models.ForeignKey(CashierSession, on_delete=models.CASCADE, related_name='cash_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    
    # Amount details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    reason = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    
    # Approval
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_cash_movements')
    approval_time = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cash_movements')
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Cash Movement'
        verbose_name_plural = 'Cash Movements'
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - KES {self.amount}"


class POSSettings(models.Model):
    """POS system configuration"""
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='pos_settings')
    
    # Receipt settings
    receipt_header = models.TextField(blank=True, help_text="Header text for receipts")
    receipt_footer = models.TextField(blank=True, help_text="Footer text for receipts")
    print_customer_copy = models.BooleanField(default=True)
    print_merchant_copy = models.BooleanField(default=True)
    
    # Tax settings
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('16.00'))
    tax_inclusive_pricing = models.BooleanField(default=True)
    
    # Discount settings
    allow_line_item_discounts = models.BooleanField(default=True)
    allow_sale_discounts = models.BooleanField(default=True)
    require_manager_for_discounts = models.BooleanField(default=False)
    max_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'))
    
    # Payment settings
    cash_rounding = models.BooleanField(default=True)
    rounding_precision = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.05'))
    
    # Loyalty settings
    loyalty_points_enabled = models.BooleanField(default=True)
    points_per_shilling = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.010'))
    points_redemption_rate = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.050'))
    
    # Inventory integration
    auto_update_inventory = models.BooleanField(default=True)
    low_stock_warning = models.BooleanField(default=True)
    prevent_negative_stock = models.BooleanField(default=True)
    
    # Security
    require_receipt_signature = models.BooleanField(default=False)
    auto_logout_minutes = models.PositiveIntegerField(default=30)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'POS Settings'
        verbose_name_plural = 'POS Settings'
    
    def __str__(self):
        return f"POS Settings - {self.store.name}"
