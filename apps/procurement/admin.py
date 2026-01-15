from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Vendor, PurchaseRequisition, RFQ, PurchaseOrder, 
    PurchaseOrderItem, VendorPerformance
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['vendor_code', 'company_name', 'contact_person', 'vendor_type', 'status', 'rating', 'created_at']
    list_filter = ['vendor_type', 'status', 'rating', 'country', 'created_at']
    search_fields = ['vendor_code', 'company_name', 'contact_person', 'email', 'phone']
    readonly_fields = ['vendor_code', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor_code', 'company_name', 'contact_person', 'email', 'phone', 'alternative_phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'postal_code', 'country')
        }),
        ('Business Details', {
            'fields': ('vendor_type', 'tax_number', 'bank_name', 'bank_account', 'payment_terms')
        }),
        ('Status & Performance', {
            'fields': ('status', 'credit_limit', 'rating')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new vendor
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['item_name', 'description', 'quantity', 'unit_price', 'total_price', 'quantity_received']
    readonly_fields = ['total_price']


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = ['requisition_number', 'title', 'department', 'priority', 'status', 'requested_by', 'requested_date']
    list_filter = ['status', 'priority', 'department', 'requested_date']
    search_fields = ['requisition_number', 'title', 'description']
    readonly_fields = ['requisition_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('requisition_number', 'title', 'description', 'department', 'priority')
        }),
        ('Dates', {
            'fields': ('requested_date', 'required_date')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('Budget', {
            'fields': ('estimated_total', 'budget_code')
        }),
        ('Metadata', {
            'fields': ('requested_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new requisition
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ['rfq_number', 'title', 'status', 'issue_date', 'closing_date', 'created_by']
    list_filter = ['status', 'issue_date', 'closing_date']
    search_fields = ['rfq_number', 'title', 'description']
    readonly_fields = ['rfq_number', 'created_at', 'updated_at']
    filter_horizontal = ['vendors']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('rfq_number', 'title', 'description', 'status')
        }),
        ('Dates', {
            'fields': ('issue_date', 'closing_date')
        }),
        ('Related Records', {
            'fields': ('requisition', 'vendors')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new RFQ
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'vendor', 'status', 'priority', 'total_amount', 'order_date', 'required_date']
    list_filter = ['status', 'priority', 'order_date', 'currency']
    search_fields = ['po_number', 'title', 'vendor__company_name']
    readonly_fields = ['po_number', 'created_at', 'updated_at']
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('po_number', 'vendor', 'title', 'description', 'status', 'priority')
        }),
        ('References', {
            'fields': ('requisition', 'rfq')
        }),
        ('Dates', {
            'fields': ('order_date', 'required_date', 'promised_date')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'currency')
        }),
        ('Terms', {
            'fields': ('payment_terms', 'delivery_terms')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new PO
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(VendorPerformance)
class VendorPerformanceAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'purchase_order', 'overall_rating_display', 'days_late', 'evaluation_date']
    list_filter = ['delivery_rating', 'quality_rating', 'service_rating', 'price_rating', 'evaluation_date']
    search_fields = ['vendor__company_name', 'purchase_order__po_number']
    readonly_fields = ['days_late', 'overall_rating_display', 'evaluation_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'purchase_order')
        }),
        ('Performance Ratings', {
            'fields': ('delivery_rating', 'quality_rating', 'service_rating', 'price_rating', 'overall_rating_display')
        }),
        ('Delivery Performance', {
            'fields': ('promised_date', 'actual_delivery_date', 'days_late')
        }),
        ('Comments & Evaluation', {
            'fields': ('comments', 'evaluated_by', 'evaluation_date')
        }),
    )
    
    def overall_rating_display(self, obj):
        rating = obj.overall_rating
        stars = '⭐' * int(rating)
        return f"{rating:.1f} {stars}"
    overall_rating_display.short_description = 'Overall Rating'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new performance record
            obj.evaluated_by = request.user
        super().save_model(request, obj, form, change)
