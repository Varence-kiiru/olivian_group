from django.contrib import admin
from .models import Category, Product, ProductImage, ProductDocument
from core.admin import admin_site


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'caption', 'is_primary')


class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 1
    fields = ('title', 'file', 'description')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'get_price_display', 'is_featured', 'on_sale', 'created_at')
    list_filter = ('category', 'is_featured', 'on_sale', 'created_at')
    search_fields = ('name', 'description', 'features', 'applications')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductDocumentInline]
    date_hierarchy = 'created_at'
    list_editable = ('is_featured', 'on_sale')
   
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'main_image', 'is_featured')
        }),
        ('Pricing', {
            'fields': ('has_price_range', 'regular_price', 'sale_price', 'on_sale', 'price_min', 'price_max'),
            'classes': ('collapse',),
            'description': 'Set pricing information for this product. For variable products, check "has_price_range" and set min/max prices.'
        }),
        ('Detailed Information', {
            'fields': ('description', 'features', 'applications', 'specifications'),
            'classes': ('wide',)
        }),
    )
   
    def get_price_display(self, obj):
        if obj.has_price_range:
            return f" Ksh {obj.price_min} - Ksh {obj.price_max}" if obj.price_min and obj.price_max else "Price varies"
        elif obj.on_sale and obj.sale_price:
            return f"Ksh {obj.sale_price} (was Ksh {obj.regular_price})"
        elif obj.regular_price:
            return f"Ksh {obj.regular_price}"
        return "No price set"
    get_price_display.short_description = "Price"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'thumbnail', 'caption', 'is_primary')
    list_filter = ('product', 'is_primary')
    search_fields = ('product__name', 'caption')

    def thumbnail(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="50" />'
        return ""
    thumbnail.allow_tags = True
    thumbnail.short_description = "Thumbnail"


@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'product', 'file_link', 'description_preview')
    list_filter = ('product',)
    search_fields = ('product__name', 'title', 'description')

    def file_link(self, obj):
        if obj.file:
            return f'<a href="{obj.file.url}" target="_blank">Download</a>'
        return ""
    file_link.allow_tags = True
    file_link.short_description = "File"
    
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return ""
    description_preview.short_description = "Description"


# Register models with the custom admin site
admin_site.register(Category, CategoryAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(ProductImage, ProductImageAdmin)
admin_site.register(ProductDocument, ProductDocumentAdmin)
