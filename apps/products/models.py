from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager
from apps.core.models import TimeStampedModel
from ckeditor.fields import RichTextField
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os

def validate_file_size(value):
    filesize = value.size
    if filesize > 10 * 1024 * 1024:  # 10MB limit
        raise ValidationError("The maximum file size that can be uploaded is 10MB")

def get_upload_path(instance, filename):
    # Get the file extension while keeping original filename
    ext = filename.split('.')[-1]
    filename = f"{instance.sku}_{filename}"

    if isinstance(instance, Product):
        if 'manual' in filename.lower():
            return os.path.join('products', 'manuals', filename)
        return os.path.join('products', 'datasheets', filename)
    return os.path.join('products', 'documents', filename)

class ProductCategory(MPTTModel, TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=150, blank=True)
    meta_description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        default='fas fa-box',
        help_text="Font Awesome icon class (e.g., 'fas fa-solar-panel')"
    )
    default_icon_map = {
        'solar-panels': 'fas fa-solar-panel',
        'inverters': 'fas fa-microchip',
        'batteries': 'fas fa-battery-full',
        'mounting': 'fas fa-tools',
        'cables': 'fas fa-plug',
        'charge-controllers': 'fas fa-charging-station',
        'protection': 'fas fa-shield-alt',
        'switchgear': 'fas fa-toggle-on',
        'connectors': 'fas fa-plug'
    }

    class MPTTMeta:
        order_insertion_by = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.icon:
            # Set default icon based on slug if not specified
            self.icon = self.default_icon_map.get(self.slug, 'fas fa-box')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(TimeStampedModel):
    PRODUCT_TYPES = [
        ('solar_panel', 'Solar Panel'),
        ('inverter', 'Inverter'),
        ('battery', 'Battery'),
        ('mounting', 'Mounting System'),
        ('cable', 'Cables & Wiring'),
        ('monitoring', 'Monitoring Equipment'),
        ('accessory', 'Accessories'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('discontinued', 'Discontinued'),
        ('out_of_stock', 'Out of Stock'),
    ]

    # Basic Information
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    sku = models.CharField(max_length=50, unique=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100, blank=True)

    # Descriptions
    short_description = models.TextField(max_length=500)
    description = RichTextField()
    features = models.JSONField(default=list, blank=True)
    applications = models.TextField(blank=True)

    # Technical Specifications
    power_rating = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Power in Watts")
    power_rating_kva = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Power in KVA (optional alternative rating)")
    efficiency = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Efficiency percentage")
    voltage = models.CharField(max_length=100, blank=True)
    current = models.CharField(max_length=50, blank=True)
    dimensions = models.CharField(max_length=100, blank=True, help_text="L x W x H")
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Weight in KG")
    operating_temperature = models.CharField(max_length=50, blank=True)
    warranty_years = models.IntegerField(null=True, blank=True)
    certifications = models.JSONField(default=list, blank=True)

    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_order_quantity = models.IntegerField(default=1)
    
    # Inventory
    track_quantity = models.BooleanField(default=True)
    quantity_in_stock = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    allow_backorders = models.BooleanField(default=False)
    
    # SEO and Marketing
    meta_title = models.CharField(max_length=150, blank=True)
    meta_description = models.TextField(blank=True)
    featured = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Customer Visibility
    show_to_customers = models.BooleanField(
        default=False, 
        help_text="Display this product on the customer-facing website"
    )
    customer_inquiry_only = models.BooleanField(
        default=False,
        help_text="Show product but require inquiry for pricing (hide prices)"
    )
    
    # Files and Documents
    installation_manual = models.FileField(
        upload_to=get_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_file_size
        ],
        blank=True,
        null=True,
        help_text="Accepted formats: PDF, DOC, DOCX (max 10MB)"
    )
    datasheet = models.FileField(
        upload_to=get_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size
        ],
        blank=True,
        null=True,
        help_text="Accepted format: PDF (max 10MB)"
    )
    
    tags = TaggableManager(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'featured']),
            models.Index(fields=['product_type', 'category']),
            models.Index(fields=['sku']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.sku}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})
    
    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.selling_price
    
    @property
    def get_price(self):
        return self.sale_price if self.is_on_sale else self.selling_price
    
    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((self.selling_price - self.sale_price) / self.selling_price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        if not self.track_quantity:
            return True
        return self.quantity_in_stock > 0
    
    @property
    def is_low_stock(self):
        if not self.track_quantity:
            return False
        return self.quantity_in_stock <= self.low_stock_threshold
    
    def can_be_purchased(self, quantity=1):
        if not self.track_quantity:
            return True
        if self.quantity_in_stock >= quantity:
            return True
        return self.allow_backorders
    
    @property
    def is_available_for_customers(self):
        """Check if product should be visible to customers"""
        return (
            self.status == 'active' and 
            self.show_to_customers and 
            (self.is_in_stock or not self.track_quantity or self.allow_backorders)
        )
    
    @property
    def customer_display_price(self):
        """Get price for customer display or None if inquiry only"""
        if self.customer_inquiry_only:
            return None
        return self.get_price
    
    @property
    def stock_status_for_customers(self):
        """Get customer-friendly stock status"""
        if not self.track_quantity:
            return "In Stock"
        elif self.quantity_in_stock > self.low_stock_threshold:
            return "In Stock"
        elif self.quantity_in_stock > 0:
            return "Limited Stock"
        elif self.allow_backorders:
            return "Available on Order"
        else:
            return "Out of Stock"
    
    @property
    def total_inventory_quantity(self):
        """Get total quantity across all warehouses"""
        from apps.inventory.models import InventoryItem
        total = self.inventory_items.aggregate(
            total=models.Sum('quantity_on_hand')
        )['total']
        return total or 0
    
    @property
    def inventory_by_warehouse(self):
        """Get inventory breakdown by warehouse"""
        return self.inventory_items.select_related('warehouse').values(
            'warehouse__name', 'warehouse__code', 'quantity_on_hand'
        )
    
    def sync_inventory_to_product_stock(self):
        """Sync inventory quantities back to product stock field"""
        total_qty = self.total_inventory_quantity
        if self.quantity_in_stock != total_qty:
            self.quantity_in_stock = total_qty
            self.save(update_fields=['quantity_in_stock'])
        return total_qty
    
    def get_primary_image(self):
        """Get the primary image for this product"""
        return self.images.filter(is_primary=True).first() or self.images.first()
    
    def get_primary_image_url(self):
        """Get the URL of the primary image with fallback"""
        image = self.get_primary_image()
        if image and image.image:
            return image.image.url
        return None

class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', '-is_primary']
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary image per product
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} - Image"

class ProductDocument(TimeStampedModel):
    DOCUMENT_TYPES = [
        ('manual', 'Installation Manual'),
        ('datasheet', 'Datasheet'),
        ('warranty', 'Warranty Document'),
        ('certificate', 'Certificate'),
        ('brochure', 'Brochure'),
        ('other', 'Other'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='product_documents/')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.title}"

class ProductReview(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('product', 'user')
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars"
