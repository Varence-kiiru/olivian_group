from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin
from .models import ProductCategory, Product, ProductImage, ProductDocument, ProductReview

@admin.register(ProductCategory)
class ProductCategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'icon', 'is_active')
    list_display_links = ('indented_title',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'parent', 'is_active')
        }),
        ('Display Options', {
            'fields': ('icon', 'description'),
            'classes': ('collapse',)
        }),
    )

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'sort_order')

class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 1
    fields = ('title', 'document_type', 'file', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'product_type', 'selling_price', 'status', 'featured', 'show_to_customers', 'share_actions')
    list_filter = ('product_type', 'category', 'status', 'featured', 'show_to_customers', 'brand')
    search_fields = ('name', 'sku', 'brand', 'model_number')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductDocumentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'product_type', 'category', 'brand', 'model_number')
        }),
        ('Description', {
            'fields': ('short_description', 'description', 'features', 'applications')
        }),
        ('Technical Specifications', {
            'fields': ('power_rating', 'power_rating_kva', 'efficiency', 'voltage', 'current', 'dimensions', 'weight',
                      'operating_temperature', 'warranty_years', 'certifications')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price', 'sale_price', 'minimum_order_quantity')
        }),
        ('Inventory', {
            'fields': ('track_quantity', 'quantity_in_stock', 'low_stock_threshold', 'allow_backorders')
        }),
        ('Marketing', {
            'fields': ('meta_title', 'meta_description', 'featured', 'status', 'tags')
        }),
        ('Customer Visibility', {
            'fields': ('show_to_customers', 'customer_inquiry_only'),
            'description': 'Control how this product appears to customers on the website'
        }),
        ('Documents', {
            'fields': ('installation_manual', 'datasheet')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

    def share_actions(self, obj):
        """Display share action buttons for the product"""
        share_url = reverse('products:share_facebook', args=[obj.slug])
        return format_html(
            '<a href="{}" class="button" style="background: #1877f2; color: white; padding: 3px 6px; border-radius: 3px; text-decoration: none; font-size: 11px;">Share to FB</a>',
            share_url
        )
    share_actions.short_description = 'Actions'

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = "Disapprove selected reviews"
