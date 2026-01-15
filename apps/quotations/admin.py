from django.contrib import admin
from .models import Customer, QuotationRequest, Quotation, QuotationItem

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'company_name', 'loyalty_tier', 'total_spent')
    list_filter = ('business_type', 'property_type', 'country', 'loyalty_points')
    search_fields = ('name', 'email', 'phone', 'company_name')
    readonly_fields = ('loyalty_points', 'total_orders', 'total_spent', 'last_purchase_date')

@admin.register(QuotationRequest)
class QuotationRequestAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'email', 'system_type', 'status', 'urgency', 'created_at')
    list_filter = ('status', 'urgency', 'system_type', 'property_type', 'roof_access')
    search_fields = ('customer_name', 'email', 'phone', 'company_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'customer', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'system_type', 'created_at')
    search_fields = ('quotation_number', 'customer__name', 'customer__email')
    readonly_fields = ('quotation_number', 'created_at', 'updated_at', 'subtotal', 'tax_amount', 'total_amount')

@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'item_name', 'quantity', 'unit_price', 'total_price')
    list_filter = ('quotation__status',)
    search_fields = ('quotation__quotation_number', 'item_name')
    readonly_fields = ('total_price',)
