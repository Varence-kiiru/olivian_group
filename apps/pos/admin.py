from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    Store, Terminal, CashierSession, Sale, SaleItem, 
    Payment, Discount, CashMovement, POSSettings
)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'city', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'county', 'created_at']
    search_fields = ['name', 'code', 'address_line_1', 'city']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Store Information', {
            'fields': ('name', 'code', 'manager', 'is_active')
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'county', 'postal_code')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email')
        }),
        ('Settings', {
            'fields': ('timezone', 'currency', 'opening_time', 'closing_time'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'store', 'current_cashier', 'is_active', 'session_status']
    list_filter = ['is_active', 'store', 'created_at']
    search_fields = ['name', 'code', 'device_id']
    ordering = ['store', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Terminal Information', {
            'fields': ('name', 'code', 'store', 'is_active')
        }),
        ('Hardware Details', {
            'fields': ('device_id', 'ip_address', 'mac_address'),
            'classes': ('collapse',)
        }),
        ('Features', {
            'fields': ('requires_manager_approval', 'cash_drawer_enabled', 'receipt_printer_enabled', 'barcode_scanner_enabled')
        }),
        ('Current Session', {
            'fields': ('current_cashier', 'session_start')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def session_status(self, obj):
        if obj.is_in_session:
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: red;">Inactive</span>')
    session_status.short_description = 'Session Status'


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['line_total', 'tax_amount', 'discount_amount']
    fields = ['product', 'product_name', 'quantity', 'unit_price', 'discount_percentage', 'tax_rate', 'line_total']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['processed_at']
    fields = ['payment_type', 'amount', 'status', 'transaction_id', 'processed_at']


@admin.register(CashierSession)
class CashierSessionAdmin(admin.ModelAdmin):
    list_display = ['session_number', 'cashier', 'terminal', 'status', 'start_time', 'duration_hours', 'total_sales_amount']
    list_filter = ['status', 'terminal__store', 'start_time']
    search_fields = ['session_number', 'cashier__first_name', 'cashier__last_name']
    ordering = ['-start_time']
    readonly_fields = ['session_number', 'created_at', 'updated_at', 'duration', 'total_sales']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_number', 'cashier', 'terminal', 'status')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'duration')
        }),
        ('Cash Management', {
            'fields': ('opening_cash', 'closing_cash', 'expected_cash', 'cash_variance')
        }),
        ('Performance', {
            'fields': ('total_sales',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('opening_notes', 'closing_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_hours(self, obj):
        if obj.end_time:
            duration = obj.end_time - obj.start_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.1f} hours"
        else:
            duration = timezone.now() - obj.start_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.1f} hours (ongoing)"
    duration_hours.short_description = 'Duration'
    
    def total_sales_amount(self, obj):
        return f"KES {obj.total_sales:,.2f}"
    total_sales_amount.short_description = 'Total Sales'


# Customer admin is now handled in quotations app since we use unified Customer model


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'cashier', 'customer', 'grand_total', 'payment_method', 'status', 'transaction_time']
    list_filter = ['status', 'payment_method', 'session__terminal__store', 'transaction_time']
    search_fields = ['receipt_number', 'sale_number', 'customer__name', 'customer__email']
    ordering = ['-transaction_time']
    readonly_fields = ['sale_number', 'receipt_number', 'created_at', 'updated_at']
    inlines = [SaleItemInline, PaymentInline]
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('sale_number', 'receipt_number', 'status')
        }),
        ('Relationships', {
            'fields': ('session', 'cashier', 'customer')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'grand_total')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'amount_paid', 'change_amount')
        }),
        ('Transaction References', {
            'fields': ('mpesa_transaction_id', 'card_reference'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('transaction_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cashier', 'customer', 'session')


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product_name', 'quantity', 'unit_price', 'discount_amount', 'line_total']
    list_filter = ['sale__transaction_time', 'product']
    search_fields = ['product_name', 'product_sku', 'sale__receipt_number']
    ordering = ['-sale__transaction_time']
    readonly_fields = ['line_total', 'tax_amount', 'discount_amount', 'created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['sale', 'payment_type', 'amount', 'status', 'transaction_id', 'processed_at']
    list_filter = ['payment_type', 'status', 'processed_at']
    search_fields = ['transaction_id', 'reference_number', 'sale__receipt_number']
    ordering = ['-processed_at']
    readonly_fields = ['processed_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('sale', 'payment_type', 'amount', 'currency', 'status')
        }),
        ('Transaction References', {
            'fields': ('transaction_id', 'reference_number')
        }),
        ('M-Pesa Details', {
            'fields': ('mpesa_receipt_number', 'mpesa_phone_number'),
            'classes': ('collapse',)
        }),
        ('Card Details', {
            'fields': ('card_last_four', 'card_type'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('processed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'discount_type', 'is_active', 'start_date', 'end_date', 'usage_status']
    list_filter = ['is_active', 'discount_type', 'applies_to', 'start_date']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    readonly_fields = ['current_usage', 'created_at', 'updated_at']
    filter_horizontal = ['applicable_products', 'applicable_categories']
    
    fieldsets = (
        ('Discount Information', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Configuration', {
            'fields': ('discount_type', 'applies_to')
        }),
        ('Values', {
            'fields': ('percentage_value', 'fixed_amount', 'buy_quantity', 'get_quantity')
        }),
        ('Restrictions', {
            'fields': ('minimum_purchase', 'maximum_discount', 'usage_limit', 'current_usage', 'requires_manager_approval')
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date')
        }),
        ('Applicable Items', {
            'fields': ('applicable_products', 'applicable_categories'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def usage_status(self, obj):
        if obj.usage_limit:
            percentage = (obj.current_usage / obj.usage_limit) * 100
            if percentage >= 100:
                color = 'red'
                status = 'Exhausted'
            elif percentage >= 75:
                color = 'orange'
                status = f'{obj.current_usage}/{obj.usage_limit}'
            else:
                color = 'green'
                status = f'{obj.current_usage}/{obj.usage_limit}'
            return format_html(f'<span style="color: {color};">{status}</span>')
        return f'{obj.current_usage} (unlimited)'
    usage_status.short_description = 'Usage'


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ['session', 'movement_type', 'amount', 'reason', 'performed_by', 'approved_by', 'timestamp']
    list_filter = ['movement_type', 'requires_approval', 'timestamp']
    search_fields = ['reason', 'notes', 'session__session_number']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Movement Information', {
            'fields': ('session', 'movement_type', 'amount', 'reason')
        }),
        ('Approval', {
            'fields': ('requires_approval', 'approved_by', 'approval_time')
        }),
        ('Details', {
            'fields': ('notes', 'performed_by')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )


@admin.register(POSSettings)
class POSSettingsAdmin(admin.ModelAdmin):
    list_display = ['store', 'default_tax_rate', 'loyalty_points_enabled', 'auto_update_inventory']
    list_filter = ['loyalty_points_enabled', 'auto_update_inventory', 'tax_inclusive_pricing']
    search_fields = ['store__name']
    
    fieldsets = (
        ('Store', {
            'fields': ('store',)
        }),
        ('Receipt Settings', {
            'fields': ('receipt_header', 'receipt_footer', 'print_customer_copy', 'print_merchant_copy')
        }),
        ('Tax Settings', {
            'fields': ('default_tax_rate', 'tax_inclusive_pricing')
        }),
        ('Discount Settings', {
            'fields': ('allow_line_item_discounts', 'allow_sale_discounts', 'require_manager_for_discounts', 'max_discount_percentage')
        }),
        ('Payment Settings', {
            'fields': ('cash_rounding', 'rounding_precision')
        }),
        ('Loyalty Settings', {
            'fields': ('loyalty_points_enabled', 'points_per_shilling', 'points_redemption_rate')
        }),
        ('Inventory Integration', {
            'fields': ('auto_update_inventory', 'low_stock_warning', 'prevent_negative_stock')
        }),
        ('Security', {
            'fields': ('require_receipt_signature', 'auto_logout_minutes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
