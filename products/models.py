from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/')
   
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = CKEditor5Field()
    features = CKEditor5Field()
    applications = CKEditor5Field()
    specifications = CKEditor5Field()
    main_image = models.ImageField(upload_to='products/')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Price fields
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                   help_text="Minimum price in a range (for variable products)")
    price_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                   help_text="Maximum price in a range (for variable products)")
    has_price_range = models.BooleanField(default=False)
    on_sale = models.BooleanField(default=False)

    def discount_percentage(self):
        if self.regular_price and self.sale_price and self.regular_price > 0:
            discount = ((self.regular_price - self.sale_price) / self.regular_price) * 100
            return int(discount)
        return 0

    def get_display_price(self):
        if self.has_price_range:
            if self.price_min and self.price_max:
                return f"${self.price_min} - ${self.price_max}"
            return "Price varies"
        elif self.on_sale and self.sale_price:
            return self.sale_price
        elif self.regular_price:
            return self.regular_price
        return None

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductDocument(models.Model):
    product = models.ForeignKey(Product, related_name='documents', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='products/documents/')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title
