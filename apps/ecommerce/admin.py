from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

from .models import Order, OrderItem, OrderStatusHistory, ShoppingCart, CartItem, Payment, Receipt, MPesaTransaction

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('previous_status', 'new_status', 'changed_by', 'notes', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'total_price')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_info', 'status_badge', 'payment_status_badge', 'total_amount', 'created_at', 'action_buttons')
    list_filter = ('status', 'payment_status', 'order_type', 'created_at', 'salesperson')
    search_fields = ('order_number', 'customer__email', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'subtotal', 'tax_amount', 'total_amount', 'status_updated_at')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'order_type', 'status', 'status_notes')
        }),
        ('Customer Information', {
            'fields': ('customer', 'user', 'billing_address', 'shipping_address')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'discount_amount', 'discount_percentage', 'tax_amount', 'shipping_cost', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'payment_reference', 'mpesa_transaction_id')
        }),
        ('Delivery Information', {
            'fields': ('delivery_date', 'shipping_company', 'tracking_number', 'delivery_notes')
        }),
        ('Status Tracking', {
            'fields': ('status_updated_at', 'status_updated_by')
        }),
        ('Related Records', {
            'fields': ('quotation', 'project', 'salesperson'),
            'classes': ('collapse',)
        }),
        ('Terms', {
            'fields': ('payment_terms', 'delivery_time'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def customer_info(self, obj):
        try:
            if obj.customer:
                name = f"{obj.customer.first_name} {obj.customer.last_name}".strip() or obj.customer.email
                return format_html(
                    '<strong>{}</strong><br><small>{}</small>',
                    name,
                    obj.customer.email
                )
            return "-"
        except Exception as e:
            logger.error(f"Error displaying customer info: {str(e)}")
            return "Customer Info Unavailable"
    customer_info.short_description = "Customer"

    def status_badge(self, obj):
        try:
            color_map = {
                'received': 'info',
                'pending_payment': 'warning',
                'paid': 'success',
                'processing': 'primary',
                'packed_ready': 'info',
                'shipped': 'primary',
                'out_for_delivery': 'warning',
                'delivered': 'success',
                'completed': 'success',
                'cancelled': 'danger',
                'returned': 'warning',
                'refunded': 'secondary',
            }
            color = color_map.get(obj.status, 'secondary')
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color,
                obj.get_status_display() or obj.status
            )
        except Exception as e:
            logger.error(f"Error displaying status badge: {str(e)}")
            return "Status Unavailable"
    status_badge.short_description = "Status"

    def payment_status_badge(self, obj):
        color_map = {
            'pending': 'warning',
            'paid': 'success',
            'failed': 'danger',
            'refunded': 'info',
        }
        color = color_map.get(obj.payment_status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = "Payment Status"
    
    def action_buttons(self, obj):
        try:
            view_url = reverse('admin:ecommerce_order_change', args=[obj.pk])
            return format_html(
                '<a class="btn btn-sm btn-outline-primary" href="{}">{}</a> '
                '<a class="btn btn-sm btn-outline-success" href="javascript:void(0)" '
                'onclick="updateStatus(\'{}\', event)">{}</a>',
                view_url,
                'View',
                obj.order_number if obj.order_number else '',
                'Update Status'
            )
        except Exception as e:
            logger.error(f"Error rendering action buttons: {str(e)}")
            return "Actions Unavailable"
    action_buttons.short_description = "Actions"

    def save_model(self, request, obj, form, change):
        try:
            if change:
                # Get old object safely using get_object_or_404
                old_obj = self.model.objects.filter(pk=obj.pk).first()
                if old_obj and old_obj.status != obj.status:
                    obj.status_updated_by = request.user
                    # Create status history with error handling
                    try:
                        OrderStatusHistory.objects.create(
                            order=obj,
                            previous_status=old_obj.status,
                            new_status=obj.status,
                            changed_by=request.user,
                            notes=f"Status updated via admin interface"
                        )
                    except Exception as e:
                        # Log the error but don't prevent saving
                        logger.error(f"Error creating status history: {str(e)}")
            
            super().save_model(request, obj, form, change)
        except Exception as e:
            logger.error(f"Error saving order {obj.order_number}: {str(e)}")
            raise
    
    class Media:
        css = {
            'all': (
                'admin/css/custom_order_admin.css',
            )
        }
        js = (
            'admin/js/vendor/jquery/jquery.min.js',
            'admin/js/jquery.init.js',
            'admin/js/order_admin.js',
        )

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'previous_status_display', 'new_status_display', 'changed_by', 'created_at')
    list_filter = ('new_status', 'previous_status', 'changed_by', 'created_at')
    search_fields = ('order__order_number', 'notes')
    readonly_fields = ('order', 'previous_status', 'new_status', 'changed_by', 'created_at', 'updated_at')

    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = "Order Number"

    def previous_status_display(self, obj):
        if obj.previous_status:
            return dict(Order.STATUS_CHOICES).get(obj.previous_status, obj.previous_status)
        return "-"
    previous_status_display.short_description = "From"
    
    def new_status_display(self, obj):
        return dict(Order.STATUS_CHOICES).get(obj.new_status, obj.new_status)
    new_status_display.short_description = "To"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'product', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__status', 'product__category')
    search_fields = ('order__order_number', 'product__name')
    readonly_fields = ('order', 'product', 'quantity', 'unit_price', 'total_price', 'created_at', 'updated_at')
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = "Order Number"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# Register other models with basic admin
@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    readonly_fields = ('user', 'created_at', 'updated_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'created_at')
    readonly_fields = ('cart', 'product', 'quantity', 'created_at', 'updated_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'amount', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    readonly_fields = ('order', 'created_at', 'updated_at')

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'order', 'issued_by', 'created_at')
    readonly_fields = ('receipt_number', 'order', 'issued_by', 'created_at', 'updated_at')

@admin.register(MPesaTransaction)
class MPesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('order', 'phone_number', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('order', 'checkout_request_id', 'created_at', 'updated_at')
