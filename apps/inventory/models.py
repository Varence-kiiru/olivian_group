from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.core.models import TimeStampedModel

class Supplier(TimeStampedModel):
    """Supplier information for inventory management"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Kenya')
    
    # Business details
    tax_number = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    bank_details = models.TextField(blank=True)
    
    # Terms and conditions
    payment_terms = models.CharField(max_length=100, default='Net 30')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lead_time_days = models.IntegerField(default=30)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Rating and status
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(default=False)
    
    # Additional information
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    def get_outstanding_balance(self):
        """Calculate outstanding balance with this supplier"""
        return self.purchase_orders.filter(
            status__in=['sent', 'partially_received']
        ).aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0')

class Warehouse(TimeStampedModel):
    """Warehouse/storage location information"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    manager = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Capacity information
    total_capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Square meters")
    used_capacity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def capacity_utilization(self):
        if self.total_capacity == 0:
            return 0
        return (self.used_capacity / self.total_capacity) * 100

class InventoryItem(TimeStampedModel):
    """Enhanced inventory tracking for products"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='inventory_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_items')
    
    # Stock levels
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_on_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Thresholds
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    maximum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    safety_stock = models.DecimalField(max_digits=10, decimal_places=2, default=5)
    
    # Costing
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Location
    bin_location = models.CharField(max_length=50, blank=True)
    row = models.CharField(max_length=10, blank=True)
    shelf = models.CharField(max_length=10, blank=True)
    
    # Tracking dates
    last_counted = models.DateField(null=True, blank=True)
    last_received = models.DateField(null=True, blank=True)
    last_issued = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ('product', 'warehouse')
    
    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name}"
    
    @property
    def available_quantity(self):
        """Available quantity = On hand - Allocated"""
        return self.quantity_on_hand - self.quantity_allocated
    
    @property
    def needs_reorder(self):
        """Check if item needs reordering"""
        return self.available_quantity <= self.reorder_point
    
    @property
    def is_overstocked(self):
        """Check if item is overstocked"""
        return self.quantity_on_hand > self.maximum_stock
    
    def update_average_cost(self, new_quantity, new_cost):
        """Update average cost using weighted average method"""
        total_value = (self.quantity_on_hand * self.average_cost) + (new_quantity * new_cost)
        total_quantity = self.quantity_on_hand + new_quantity
        
        if total_quantity > 0:
            self.average_cost = total_value / total_quantity
        
        self.save()

class PurchaseOrderSequence(models.Model):
    """Model to track purchase order sequence numbers"""
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)
    
    @classmethod
    def get_next_number(cls, year=None):
        if year is None:
            year = timezone.now().year
        
        sequence, created = cls.objects.get_or_create(year=year, defaults={'last_number': 0})
        sequence.last_number += 1
        sequence.save()
        return f"OG-PO-{year}-{sequence.last_number:04d}"

class PurchaseOrder(TimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed by Supplier'),
        ('partially_received', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ]
    
    # Order information
    po_number = models.CharField(max_length=20, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    order_date = models.DateField(default=timezone.now)
    expected_delivery = models.DateField()
    actual_delivery = models.DateField(null=True, blank=True)
    
    # Financial information
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Terms
    payment_terms = models.CharField(max_length=100)
    delivery_terms = models.CharField(max_length=100, blank=True)
    
    # Personnel
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='created_pos')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    supplier_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['status', 'order_date']),
            models.Index(fields=['supplier', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = PurchaseOrderSequence.get_next_number()
        
        # Calculate totals
        items = self.items.all()
        self.subtotal = sum(item.total_amount for item in items)
        
        # Calculate tax
        from django.conf import settings
        vat_rate = getattr(settings, 'VAT_RATE', 16.0)
        self.tax_amount = (self.subtotal * vat_rate) / 100
        
        # Calculate total
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"PO {self.po_number}"
    
    def can_be_received(self):
        return self.status in ['sent', 'confirmed', 'partially_received']
    
    def update_status(self):
        """Update status based on received quantities"""
        items = self.items.all()
        if not items:
            return
        
        all_received = all(item.received_quantity >= item.ordered_quantity for item in items)
        any_received = any(item.received_quantity > 0 for item in items)
        
        if all_received:
            self.status = 'received'
        elif any_received:
            self.status = 'partially_received'
        
        self.save()

class PurchaseOrderItem(TimeStampedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    # Order details
    description = models.CharField(max_length=200)
    ordered_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Additional information
    supplier_part_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.description:
            self.description = self.product.name
        
        self.total_amount = self.ordered_quantity * self.unit_cost
        super().save(*args, **kwargs)
        
        # Update purchase order totals
        self.purchase_order.save()
    
    def __str__(self):
        return f"{self.ordered_quantity} x {self.product.name}"
    
    @property
    def pending_quantity(self):
        return self.ordered_quantity - self.received_quantity

class StockMovement(TimeStampedModel):
    MOVEMENT_TYPES = [
        ('receipt', 'Receipt'),
        ('issue', 'Issue'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damage'),
        ('theft', 'Theft'),
        ('sale', 'Sale'),
    ]
    
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    
    # Quantity information
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Reference information
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)
    
    # Before and after quantities
    quantity_before = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional information
    reason = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.movement_type} - {self.quantity} {self.inventory_item.product.name}"

class StockAdjustment(TimeStampedModel):
    """Stock adjustments for corrections and cycle counts"""
    ADJUSTMENT_TYPES = [
        ('cycle_count', 'Cycle Count'),
        ('physical_count', 'Physical Count'),
        ('correction', 'Correction'),
        ('damage', 'Damage Write-off'),
        ('theft', 'Theft Write-off'),
        ('expiry', 'Expiry Write-off'),
    ]
    
    adjustment_number = models.CharField(max_length=20, unique=True, editable=False)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    
    # Adjustment details
    reason = models.TextField()
    adjustment_date = models.DateField(default=timezone.now)
    
    # Approval
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Personnel
    performed_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='stock_adjustments')
    
    def save(self, *args, **kwargs):
        if not self.adjustment_number:
            year = timezone.now().year
            count = StockAdjustment.objects.filter(created_at__year=year).count() + 1
            self.adjustment_number = f"ADJ-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Adjustment {self.adjustment_number}"

class StockAdjustmentItem(TimeStampedModel):
    adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    
    # Quantities
    system_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    actual_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    adjustment_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional information
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        self.adjustment_quantity = self.actual_quantity - self.system_quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.inventory_item.product.name} - Adj: {self.adjustment_quantity}"

class StockTransfer(TimeStampedModel):
    """Transfer stock between warehouses"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    transfer_number = models.CharField(max_length=20, unique=True, editable=False)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='outbound_transfers')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inbound_transfers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    transfer_date = models.DateField(default=timezone.now)
    expected_arrival = models.DateField()
    actual_arrival = models.DateField(null=True, blank=True)
    
    # Personnel
    initiated_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='initiated_transfers')
    received_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional information
    reason = models.TextField()
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.transfer_number:
            year = timezone.now().year
            count = StockTransfer.objects.filter(created_at__year=year).count() + 1
            self.transfer_number = f"TRF-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Transfer {self.transfer_number}"

class StockTransferItem(TimeStampedModel):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity_sent = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.quantity_sent} x {self.product.name}"

class InventoryValuation(TimeStampedModel):
    """Inventory valuation records"""
    VALUATION_METHODS = [
        ('fifo', 'First In, First Out'),
        ('lifo', 'Last In, First Out'),
        ('weighted_average', 'Weighted Average'),
        ('standard_cost', 'Standard Cost'),
    ]
    
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    valuation_date = models.DateField()
    valuation_method = models.CharField(max_length=20, choices=VALUATION_METHODS, default='weighted_average')
    
    # Totals
    total_quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Personnel
    performed_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Valuation {self.warehouse.name} - {self.valuation_date}"

class InventoryValuationItem(TimeStampedModel):
    valuation = models.ForeignKey(InventoryValuation, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_value = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_value = self.quantity * self.unit_value
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.inventory_item.product.name} - {self.quantity} @ {self.unit_value}"
