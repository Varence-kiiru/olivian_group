from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.core.models import TimeStampedModel

class ShoppingCart(TimeStampedModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_items(self):
        """Optimized total items calculation using database aggregation"""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def subtotal(self):
        """Returns VAT-inclusive subtotal (product prices include VAT)"""
        return sum(item.total_price for item in self.items.all())

    @property
    def subtotal_ex_vat(self):
        """Returns subtotal excluding VAT"""
        from apps.core.models import CompanySettings
        from decimal import Decimal
        company_settings = CompanySettings.get_settings()
        vat_rate = company_settings.vat_rate
        vat_multiplier = 1 + (vat_rate / 100)
        return self.subtotal / vat_multiplier

    @property
    def total_with_vat(self):
        """Since prices are already VAT inclusive, this is the same as subtotal"""
        return self.subtotal

    @property
    def vat_amount(self):
        """Returns VAT amount calculated backwards from VAT-inclusive prices"""
        return self.subtotal - self.subtotal_ex_vat

    def add_item(self, product, quantity=1, check_stock=True):
        """Add item to cart or update quantity if already exists - optimized for performance"""
        # Use update_or_create to minimize database hits
        cart_item, created = self.items.update_or_create(
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            # Use F expression to update quantity in database without fetch + save
            from django.db.models import F
            updated_rows = self.items.filter(
                pk=cart_item.pk,
                product=product
            ).update(quantity=F('quantity') + quantity)

            if updated_rows:
                # Refresh the instance to reflect the updated quantity
                cart_item.refresh_from_db()
            else:
                # Fallback if update failed
                cart_item.quantity += quantity
                cart_item.save()

        # Check stock after adding if requested
        if check_stock and cart_item.product.track_quantity and not cart_item.product.can_be_purchased(cart_item.quantity):
            if cart_item.product.allow_backorders:
                pass  # Allow backorders
            else:
                raise ValueError(f'Insufficient stock for {cart_item.product.name}. Only {cart_item.product.quantity_in_stock} units available.')

        return cart_item

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()

class CartItem(TimeStampedModel):
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def unit_price(self):
        return self.product.get_price

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        # Check stock availability
        if self.product.track_quantity and not self.product.can_be_purchased(self.quantity):
            raise ValueError(f"Insufficient stock for {self.product.name}")
        super().save(*args, **kwargs)

class OrderSequence(models.Model):
    """Model to track order sequence numbers"""
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)

    @classmethod
    def get_next_number(cls, year=None):
        if year is None:
            year = timezone.now().year

        sequence, created = cls.objects.get_or_create(year=year, defaults={'last_number': 0})
        sequence.last_number += 1
        sequence.save()
        return f"OG-ORD-{year}-{sequence.last_number:04d}"

class Order(TimeStampedModel):
    STATUS_CHOICES = [
        ('received', 'Order Received'),
        ('pending_payment', 'Pending Payment'),
        ('pay_on_delivery', 'Pay on Delivery'),
        ('paid', 'Payment Confirmed'),
        ('processing', 'Processing'),
        ('packed_ready', 'Packed & Ready'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
    ]

    ORDER_TYPES = [
        ('online', 'Online Order'),
        ('pos', 'POS Sale'),
        ('quotation_conversion', 'Quotation Conversion'),
        ('project_order', 'Project Order'),
    ]

    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('check', 'Check'),
        ('credit', 'Credit'),
    ]

    # Order Information
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='online')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')

    # Customer Information
    customer = models.ForeignKey('quotations.Customer', on_delete=models.CASCADE, related_name='orders')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    # Related Records
    quotation = models.ForeignKey('quotations.Quotation', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True)

    # Financial Information
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Addresses
    billing_address = models.TextField()
    shipping_address = models.TextField()

    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    payment_reference = models.CharField(max_length=100, blank=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True)

    # Delivery Information
    SHIPPING_COMPANY_CHOICES = [
        ('dhl', 'DHL Express'),
        ('fedex', 'FedEx'),
        ('aramex', 'Aramex'),
        ('tnt', 'TNT Express'),
        ('ups', 'UPS'),
        ('ems', 'EMS'),
        ('skynet', 'SkyNet'),
        ('g4s', 'G4S'),
        ('kipya', 'KIPYA Messenger'),
        ('sendy', 'Sendy'),
        ('local', 'Local Courier'),
        ('other', 'Other'),
    ]

    delivery_date = models.DateField(null=True, blank=True)
    shipping_company = models.CharField(max_length=50, choices=SHIPPING_COMPANY_CHOICES, blank=True, help_text="Select the shipping company used")
    tracking_number = models.CharField(max_length=100, blank=True, help_text="Enter the tracking number provided by the shipping company")
    delivery_notes = models.TextField(blank=True)

    # Terms
    payment_terms = models.TextField(blank=True)
    delivery_time = models.CharField(max_length=100, blank=True)

    # Sales Information
    salesperson = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sales'
    )

    # Status tracking
    status_updated_at = models.DateTimeField(auto_now=True)
    status_updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='status_updates'
    )
    status_notes = models.TextField(blank=True, help_text="Internal notes about status changes")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['customer', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = OrderSequence.get_next_number()

        # Only recalculate financial amounts on initial creation
        # If Order was created with explicit amounts (like from checkout), preserve them
        if not self.pk:  # Only for new orders
            # Calculate tax amount
            from django.conf import settings
            from decimal import Decimal
            vat_rate = Decimal(str(getattr(settings, 'VAT_RATE', 16.0)))
            taxable_amount = self.subtotal - self.discount_amount
            self.tax_amount = (taxable_amount * vat_rate) / Decimal('100')

            # Calculate total (only if not already set)
            if not self.total_amount:
                self.total_amount = self.subtotal - self.discount_amount + self.tax_amount + self.shipping_cost

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"

    def can_be_cancelled(self):
        return self.status in ['received', 'pending_payment', 'paid', 'processing']

    def can_be_shipped(self):
        return self.status in ['paid', 'pay_on_delivery', 'processing'] and (self.payment_status == 'paid' or self.status == 'pay_on_delivery')

    def can_be_returned(self):
        return self.status in ['delivered', 'completed']

    def get_next_status_options(self):
        """Get available next status options based on current status"""
        status_flow = {
            'received': ['pending_payment', 'pay_on_delivery', 'cancelled'],
            'pending_payment': ['paid', 'cancelled'],
            'pay_on_delivery': ['processing', 'cancelled'],
            'paid': ['processing', 'cancelled'],
            'processing': ['packed_ready', 'cancelled'],
            'packed_ready': ['shipped'],
            'shipped': ['out_for_delivery', 'delivered'],
            'out_for_delivery': ['delivered', 'returned'],
            'delivered': ['completed', 'paid', 'returned'],
            'completed': ['returned'],
            'cancelled': [],
            'returned': ['refunded'],
            'refunded': [],
        }
        return status_flow.get(self.status, [])

    def update_inventory(self):
        """Update product inventory after order confirmation"""
        for item in self.items.all():
            if item.product.track_quantity:
                item.product.quantity_in_stock -= item.quantity
                item.product.save()

    def generate_receipt(self):
        """Generate or get receipt for this order"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Get or create receipt
        receipt, created = Receipt.objects.get_or_create(
            order=self,
            defaults={
                'issued_by': self.user or User.objects.filter(is_superuser=True).first(),
                'issued_date': timezone.now()
            }
        )

        # Generate PDF if receipt exists but no file
        if not receipt.receipt_file:
            try:
                receipt.generate_receipt_pdf()
            except Exception as e:
                # Log error but don't fail the function
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to generate PDF for receipt {receipt.receipt_number}: {str(e)}")

        return receipt

class OrderStatusHistory(TimeStampedModel):
    """Track order status changes for audit trail"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"

    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status} → {self.new_status}"

class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)

    # Item details at time of order
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    # Additional information
    description = models.TextField(blank=True)
    specifications = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_sku:
            self.product_sku = self.product.sku

        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

class Payment(TimeStampedModel):
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Payment details
    reference_number = models.CharField(max_length=100, unique=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    mpesa_phone_number = models.CharField(max_length=15, blank=True)

    # Transaction details
    transaction_date = models.DateTimeField(null=True, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Payment {self.reference_number} for {self.order.order_number}"

class Receipt(TimeStampedModel):
    """Receipt generation for payments and orders"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=20, unique=True, editable=False)

    # Receipt details
    issued_date = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)

    # Customer copy
    customer_email_sent = models.BooleanField(default=False)
    customer_email_date = models.DateTimeField(null=True, blank=True)

    # Receipt file
    receipt_file = models.FileField(upload_to='receipts/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            year = timezone.now().year
            count = Receipt.objects.filter(created_at__year=year).count() + 1
            self.receipt_number = f"RCT-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_number}"

    def generate_receipt_pdf(self):
        """Generate PDF receipt with company logo and details"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Table, TableStyle
        from django.conf import settings
        from apps.core.models import CompanySettings
        import os

        # Get company settings
        try:
            company = CompanySettings.objects.first()
        except CompanySettings.DoesNotExist:
            company = None

        # Create the PDF
        filename = f"receipt_{self.receipt_number}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, 'receipts', filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4

        # Add company logo if available
        logo_y = height - 80
        if company and company.logo:
            try:
                logo_path = os.path.join(settings.MEDIA_ROOT, company.logo.name)
                if os.path.exists(logo_path):
                    c.drawImage(logo_path, 50, logo_y, width=80, height=60, preserveAspectRatio=True)
                    logo_y = height - 90
            except:
                pass  # Continue without logo if there's an error

        # Company header
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(colors.HexColor('#38b6ff'))
        company_name = company.name if company else settings.COMPANY_NAME
        c.drawString(150, height - 50, company_name)

        # Company details
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        company_address = company.address if company else getattr(settings, 'COMPANY_ADDRESS', '')
        company_phone = company.phone if company else getattr(settings, 'COMPANY_PHONE', '')
        company_email = company.email if company else settings.COMPANY_EMAIL

        c.drawString(150, height - 70, company_address)
        c.drawString(150, height - 85, f"Phone: {company_phone}")
        c.drawString(150, height - 100, f"Email: {company_email}")

        if company and company.website:
            c.drawString(150, height - 115, f"Website: {company.website}")

        # Receipt title with decorative line
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#38b6ff'))
        c.drawString(50, height - 150, "OFFICIAL RECEIPT")
        c.setStrokeColor(colors.HexColor('#38b6ff'))
        c.setLineWidth(2)
        c.line(50, height - 155, width - 50, height - 155)

        # Receipt details in a more structured format
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        y_position = height - 185

        # Left column details
        left_details = [
            f"Receipt Number: {self.receipt_number}",
            f"Order Number: {self.order.order_number}",
            f"Date: {self.issued_date.strftime('%d/%m/%Y at %H:%M')}",
        ]

        # Right column details
        right_details = [
            f"Customer: {self.order.customer.name}",
            f"Payment Method: {self.order.get_payment_method_display()}",
        ]

        if self.order.mpesa_transaction_id:
            right_details.append(f"M-Pesa ID: {self.order.mpesa_transaction_id}")

        for detail in left_details:
            c.drawString(50, y_position, detail)
            y_position -= 15

        y_position = height - 185
        for detail in right_details:
            c.drawString(300, y_position, detail)
            y_position -= 15

        # Items table with better formatting
        y_position -= 30
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y_position, "Items Purchased:")
        y_position -= 20

        # Table headers
        c.setFont("Helvetica-Bold", 9)
        headers = ["Item", "Qty", "Unit Price", "Total"]
        x_positions = [50, 300, 380, 480]

        for i, header in enumerate(headers):
            c.drawString(x_positions[i], y_position, header)

        # Draw header line
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(50, y_position - 5, width - 50, y_position - 5)
        y_position -= 15

        # Table items
        c.setFont("Helvetica", 9)
        for item in self.order.items.all():
            c.drawString(x_positions[0], y_position, str(item.product_name)[:35])
            c.drawString(x_positions[1], y_position, str(item.quantity))
            c.drawString(x_positions[2], y_position, f"KES {item.unit_price:,.2f}")
            c.drawString(x_positions[3], y_position, f"KES {item.total_price:,.2f}")
            y_position -= 12

        # Draw line before totals
        y_position -= 5
        c.line(300, y_position, width - 50, y_position)
        y_position -= 15

        # Totals section
        c.setFont("Helvetica", 10)
        totals_data = [
            ("Subtotal:", f"KES {self.order.subtotal:,.2f}"),
            ("Discount:", f"KES {self.order.discount_amount:,.2f}"),
            ("VAT (16%):", f"KES {self.order.tax_amount:,.2f}"),
        ]

        for label, amount in totals_data:
            c.drawString(400, y_position, label)
            c.drawString(480, y_position, amount)
            y_position -= 12

        # Grand total with emphasis
        y_position -= 10
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#38b6ff'))
        c.drawString(400, y_position, "TOTAL:")
        c.drawString(480, y_position, f"KES {self.order.total_amount:,.2f}")

        # Payment Details Section - Bank accounts and M-Pesa
        try:
            from apps.financial.models import BankAccount
            bank_accounts = BankAccount.objects.filter(is_active=True, is_default=True)

            if not bank_accounts.exists():
                # Fallback to any active account
                bank_accounts = BankAccount.objects.filter(is_active=True)
        except ImportError:
            # Fallback to legacy core model if financial app not available
            from apps.core.models import BankAccount
            bank_accounts = BankAccount.objects.filter(is_active=True)

        # Check if we have any payment methods to show
        has_bank_accounts = bank_accounts.exists()
        has_legacy_bank = company and company.bank_name
        has_mpesa = company and (company.mpesa_till_number or company.mpesa_paybill_number)

        if has_bank_accounts or has_legacy_bank or has_mpesa:
            y_position -= 30
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.HexColor('#38b6ff'))
            c.drawString(50, y_position, "PAYMENT DETAILS")
            y_position -= 20

            # Bank Account Details
            if has_bank_accounts:
                c.setFont("Helvetica-Bold", 10)
                c.setFillColor(colors.black)
                c.drawString(50, y_position, "Bank Transfer:")
                y_position -= 15

                for account in bank_accounts[:2]:  # Show maximum 2 accounts
                    c.setFont("Helvetica-Bold", 9)
                    # Handle both financial app BankAccount and legacy core BankAccount
                    account_name = getattr(account, 'account_name', None) or getattr(account, 'name', 'N/A')
                    c.drawString(70, y_position, f"{account_name}")
                    y_position -= 12
                    c.setFont("Helvetica", 8)

                    # Bank name - handle both models
                    bank_name = getattr(account, 'bank_name', None)
                    if hasattr(account, 'bank') and hasattr(account.bank, 'name'):
                        bank_name = account.bank.name
                    if bank_name:
                        c.drawString(90, y_position, f"Bank: {bank_name}")
                        y_position -= 10

                    c.drawString(90, y_position, f"Account: {account.account_number}")
                    y_position -= 10

                    # Branch information - handle both models
                    branch = getattr(account, 'branch', None) or getattr(account, 'branch_name', None)
                    if branch:
                        c.drawString(90, y_position, f"Branch: {branch}")
                        y_position -= 10

                    # Branch code (only in financial model)
                    if hasattr(account, 'branch_code') and account.branch_code:
                        c.drawString(90, y_position, f"Branch Code: {account.branch_code}")
                        y_position -= 10

                    y_position -= 15

            elif has_legacy_bank:
                # Fallback to legacy bank details
                c.setFont("Helvetica-Bold", 10)
                c.setFillColor(colors.black)
                c.drawString(50, y_position, "Bank Transfer:")
                y_position -= 15
                c.setFont("Helvetica", 9)
                c.drawString(70, y_position, f"Bank: {company.bank_name}")
                y_position -= 12
                c.drawString(70, y_position, f"Account: {company.bank_account_number}")
                y_position -= 12
                c.drawString(70, y_position, f"Branch: {company.bank_branch}")
                y_position -= 20

            # M-Pesa Details
            if has_mpesa:
                c.setFont("Helvetica-Bold", 10)
                c.setFillColor(colors.black)
                c.drawString(50, y_position, "M-Pesa Payment:")
                y_position -= 15
                c.setFont("Helvetica", 8)

                if company.mpesa_business_name:
                    c.drawString(70, y_position, f"Business Name: {company.mpesa_business_name}")
                    y_position -= 10

                if company.mpesa_till_number:
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(70, y_position, f"Till Number: {company.mpesa_till_number}")
                    y_position -= 10
                    c.setFont("Helvetica", 8)
                    c.drawString(70, y_position, "Pay via: Buy Goods and Services")
                    y_position -= 12

                if company.mpesa_paybill_number:
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(70, y_position, f"Paybill: {company.mpesa_paybill_number}")
                    y_position -= 10
                    if company.mpesa_account_number:
                        c.setFont("Helvetica", 8)
                        c.drawString(70, y_position, f"Account: {company.mpesa_account_number}")
                        y_position -= 10
                    c.drawString(70, y_position, "Pay via: Pay Bill")
                    y_position -= 12

                if company.mpesa_phone_number:
                    c.drawString(70, y_position, f"Contact: {company.mpesa_phone_number}")
                    y_position -= 10

        # Footer with company branding
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        footer_text = [
            "Thank you for choosing The Olivian Group Limited!",
            "Your trusted partner in professional solar solutions.",
            "This receipt is computer generated and does not require a signature."
        ]

        footer_y = 70
        for line in footer_text:
            # Calculate text width for centering
            text_width = c.stringWidth(line, "Helvetica", 8)
            c.drawString((width - text_width) / 2, footer_y, line)
            footer_y -= 10

        c.save()

        # Update the file field
        self.receipt_file.name = f"receipts/{filename}"
        self.save()

        return filepath

class Wishlist(TimeStampedModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    products = models.ManyToManyField('products.Product', through='WishlistItem')

    def __str__(self):
        return f"Wishlist for {self.user.username}"

class WishlistItem(TimeStampedModel):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('wishlist', 'product')

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"

class Coupon(TimeStampedModel):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    # Usage limits
    usage_limit = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    # Applicable products/categories
    applicable_products = models.ManyToManyField('products.Product', blank=True)
    applicable_categories = models.ManyToManyField('products.ProductCategory', blank=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )

    def calculate_discount(self, order_amount):
        if not self.is_valid() or (self.minimum_order_amount and order_amount < self.minimum_order_amount):
            return Decimal('0')

        if self.discount_type == 'percentage':
            return min(order_amount * (self.discount_value / 100), order_amount)
        else:
            return min(self.discount_value, order_amount)

class MPesaTransaction(TimeStampedModel):
    """Track M-Pesa STK Push transactions"""
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('timeout', 'Timeout'),  # Added timeout status
    ]

    # Support both ecommerce orders and POS sales
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='mpesa_transactions', null=True, blank=True)
    pos_sale = models.ForeignKey('pos.Sale', on_delete=models.CASCADE, related_name='mpesa_transactions', null=True, blank=True)

    # M-Pesa transaction details
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    account_reference = models.CharField(max_length=100)  # Order number
    transaction_desc = models.CharField(max_length=200)

    # STK Push details
    checkout_request_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)

    # Transaction results
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')

    # API responses
    initiation_response = models.JSONField(default=dict, blank=True)
    callback_response = models.JSONField(default=dict, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)

    # Notification tracking
    notification_sent = models.BooleanField(default=False, help_text="Whether any notification (SMS/email) has been sent")
    sms_sent = models.BooleanField(default=False, help_text="Whether SMS notification has been sent")
    email_sent = models.BooleanField(default=False, help_text="Whether email notification has been sent")
    notification_sent_at = models.DateTimeField(null=True, blank=True, help_text="When notifications were last sent")

    def __str__(self):
        return f"M-Pesa {self.account_reference} - {self.status}"

    @property
    def is_successful(self):
        return self.status == 'completed' and self.mpesa_receipt_number

    def mark_completed(self, receipt_number, transaction_date):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.mpesa_receipt_number = receipt_number
        self.transaction_date = transaction_date
        self.save()

        # Update related order M-Pesa transaction ID
        if self.order and not self.order.mpesa_transaction_id:
            self.order.mpesa_transaction_id = receipt_number
            self.order.save(update_fields=['mpesa_transaction_id'])

        # Update related payment
        payment, created = Payment.objects.get_or_create(
            order=self.order,
            payment_method='mpesa',
            defaults={
                'amount': self.amount,
                'reference_number': receipt_number,
                'mpesa_receipt_number': receipt_number,
                'mpesa_phone_number': self.phone_number,
                'transaction_date': transaction_date,
                'status': 'completed'
            }
        )

        if not created and payment.status != 'completed':
            payment.status = 'completed'
            payment.mpesa_receipt_number = receipt_number
            payment.transaction_date = transaction_date
            payment.save()

    def mark_failed(self, error_message):
        """Mark transaction as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
