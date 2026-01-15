from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

User = get_user_model()


class Vendor(models.Model):
    """Vendor/Supplier management"""
    VENDOR_TYPES = [
        ('supplier', 'Supplier'),
        ('contractor', 'Contractor'),
        ('service', 'Service Provider'),
        ('manufacturer', 'Manufacturer'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blacklisted', 'Blacklisted'),
        ('pending', 'Pending Approval'),
    ]
    
    PAYMENT_TERMS = [
        ('cash', 'Cash on Delivery'),
        ('net7', 'Net 7 Days'),
        ('net15', 'Net 15 Days'),
        ('net30', 'Net 30 Days'),
        ('net45', 'Net 45 Days'),
        ('net60', 'Net 60 Days'),
    ]
    
    # Basic Information
    vendor_code = models.CharField(max_length=20, unique=True, blank=True)
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    
    # Address Information
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    
    # Business Information
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPES, default='supplier')
    tax_number = models.CharField(max_length=50, blank=True, help_text="KRA PIN Number")
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=10, choices=PAYMENT_TERMS, default='net30')
    
    # Status and Performance
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    rating = models.PositiveIntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 star rating"
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_vendors')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['company_name']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
    
    def __str__(self):
        return f"{self.vendor_code} - {self.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.vendor_code:
            # Generate vendor code: VEN-YYYY-0001
            current_year = timezone.now().year
            last_vendor = Vendor.objects.filter(
                vendor_code__startswith=f'VEN-{current_year}'
            ).order_by('-vendor_code').first()
            
            if last_vendor:
                last_number = int(last_vendor.vendor_code.split('-')[-1])
                next_number = last_number + 1
            else:
                next_number = 1
            
            self.vendor_code = f'VEN-{current_year}-{next_number:04d}'
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('procurement:vendor_detail', kwargs={'pk': self.pk})


class PurchaseRequisition(models.Model):
    """Internal purchase requests"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted to PO'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    requisition_number = models.CharField(max_length=50, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=100)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    requested_date = models.DateField(default=timezone.now)
    required_date = models.DateField()
    
    # People
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requisitions')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Budget
    estimated_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_code = models.CharField(max_length=50, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Purchase Requisition'
        verbose_name_plural = 'Purchase Requisitions'
    
    def __str__(self):
        return f"{self.requisition_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.requisition_number:
            # Generate requisition number: PR-YYYY-0001
            current_year = timezone.now().year
            last_req = PurchaseRequisition.objects.filter(
                requisition_number__startswith=f'PR-{current_year}'
            ).order_by('-requisition_number').first()
            
            if last_req:
                last_number = int(last_req.requisition_number.split('-')[-1])
                next_number = last_number + 1
            else:
                next_number = 1
            
            self.requisition_number = f'PR-{current_year}-{next_number:04d}'
        
        super().save(*args, **kwargs)


class RFQ(models.Model):
    """Request for Quotation"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Vendors'),
        ('received', 'Quotations Received'),
        ('evaluated', 'Evaluated'),
        ('awarded', 'Awarded'),
        ('cancelled', 'Cancelled'),
    ]
    
    rfq_number = models.CharField(max_length=50, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    issue_date = models.DateField(default=timezone.now)
    closing_date = models.DateField()
    
    # Related
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True)
    vendors = models.ManyToManyField(Vendor, blank=True, help_text="Vendors to send RFQ to")
    
    # People
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rfqs')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Request for Quotation'
        verbose_name_plural = 'Requests for Quotation'
    
    def __str__(self):
        return f"{self.rfq_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.rfq_number:
            # Generate RFQ number: RFQ-YYYY-0001
            current_year = timezone.now().year
            last_rfq = RFQ.objects.filter(
                rfq_number__startswith=f'RFQ-{current_year}'
            ).order_by('-rfq_number').first()
            
            if last_rfq:
                last_number = int(last_rfq.rfq_number.split('-')[-1])
                next_number = last_number + 1
            else:
                next_number = 1
            
            self.rfq_number = f'RFQ-{current_year}-{next_number:04d}'
        
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    """Purchase Orders"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Vendor'),
        ('confirmed', 'Confirmed by Vendor'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    
    # References
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True)
    rfq = models.ForeignKey(RFQ, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Basic Info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Dates
    order_date = models.DateField(default=timezone.now)
    required_date = models.DateField()
    promised_date = models.DateField(null=True, blank=True)
    
    # Financial
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='KES')
    
    # Terms
    payment_terms = models.CharField(max_length=100, blank=True)
    delivery_terms = models.CharField(max_length=100, blank=True)
    
    # People
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='procurement_pos_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='procurement_pos_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
    
    def __str__(self):
        return f"{self.po_number} - {self.vendor.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            # Generate PO number: PO-YYYY-0001
            current_year = timezone.now().year
            last_po = PurchaseOrder.objects.filter(
                po_number__startswith=f'PO-{current_year}'
            ).order_by('-po_number').first()
            
            if last_po:
                last_number = int(last_po.po_number.split('-')[-1])
                next_number = last_number + 1
            else:
                next_number = 1
            
            self.po_number = f'PO-{current_year}-{next_number:04d}'
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('procurement:po_detail', kwargs={'pk': self.pk})


class PurchaseOrderItem(models.Model):
    """Items within a Purchase Order"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    
    # Item details
    item_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Receiving tracking
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_pending = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Optional product link
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='procurement_po_items')
    
    class Meta:
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'
    
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        self.quantity_pending = self.quantity - self.quantity_received
        super().save(*args, **kwargs)


class VendorPerformance(models.Model):
    """Track vendor performance metrics"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='performance_records')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    
    # Performance metrics
    delivery_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Poor, 5=Excellent"
    )
    quality_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Poor, 5=Excellent"
    )
    service_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Poor, 5=Excellent"
    )
    price_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Poor, 5=Excellent"
    )
    
    # Delivery performance
    promised_date = models.DateField()
    actual_delivery_date = models.DateField()
    days_late = models.IntegerField(default=0)
    
    # Comments
    comments = models.TextField(blank=True)
    
    # Metadata
    evaluated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    evaluation_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Vendor Performance'
        verbose_name_plural = 'Vendor Performance Records'
        unique_together = ['vendor', 'purchase_order']
    
    def __str__(self):
        return f"{self.vendor.company_name} - {self.purchase_order.po_number}"
    
    @property
    def overall_rating(self):
        """Calculate overall performance rating"""
        return (self.delivery_rating + self.quality_rating + 
                self.service_rating + self.price_rating) / 4
    
    def save(self, *args, **kwargs):
        # Calculate days late
        if self.actual_delivery_date and self.promised_date:
            delta = self.actual_delivery_date - self.promised_date
            self.days_late = max(0, delta.days)
        super().save(*args, **kwargs)
