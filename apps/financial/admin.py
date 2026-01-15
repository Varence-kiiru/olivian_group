from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Currency, Bank, BankAccount, Transaction, BankReconciliation,
    FixedAsset, AuditTrail, ExchangeRate
)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'exchange_rate', 'is_base_currency', 'is_active', 'last_updated']
    list_filter = ['is_base_currency', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'symbol', 'decimal_places')
        }),
        ('Exchange Rate', {
            'fields': ('exchange_rate', 'last_updated')
        }),
        ('Settings', {
            'fields': ('is_base_currency', 'is_active')
        }),
    )


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'swift_code', 'central_bank_code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'swift_code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'swift_code')
        }),
        ('Kenya Banking', {
            'fields': ('central_bank_code',)
        }),
        ('Contact Information', {
            'fields': ('contact_info',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_name', 'account_number', 'bank', 'account_type', 'currency', 'current_balance', 'is_active', 'is_default']
    list_filter = ['bank', 'account_type', 'currency', 'is_active', 'is_default']
    search_fields = ['account_name', 'account_number', 'bank__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_number', 'account_name', 'bank', 'account_type', 'currency')
        }),
        ('Balance Information', {
            'fields': ('current_balance', 'available_balance', 'last_reconciled_balance', 'last_reconciled_date')
        }),
        ('Bank Details', {
            'fields': ('branch_name', 'branch_code', 'contact_person', 'contact_phone')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_default', 'enable_auto_reconciliation')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new account
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'bank_account', 'transaction_type', 'amount', 'currency', 'transaction_date', 'status', 'is_reconciled']
    list_filter = ['transaction_type', 'status', 'is_reconciled', 'currency', 'transaction_date']
    search_fields = ['transaction_id', 'description', 'reference_number', 'counterparty_name']
    readonly_fields = ['transaction_id', 'created_date', 'running_balance']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'bank_account', 'transaction_type', 'amount', 'currency')
        }),
        ('Details', {
            'fields': ('description', 'reference_number', 'external_reference')
        }),
        ('Counterparty', {
            'fields': ('counterparty_name', 'counterparty_account')
        }),
        ('Dates', {
            'fields': ('transaction_date', 'value_date', 'created_date')
        }),
        ('Status & Reconciliation', {
            'fields': ('status', 'is_reconciled', 'reconciled_date', 'reconciled_by', 'running_balance')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new transaction
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = ['reconciliation_id', 'bank_account', 'period_start', 'period_end', 'variance', 'is_balanced', 'is_approved']
    list_filter = ['is_balanced', 'is_approved', 'reconciliation_date', 'bank_account']
    search_fields = ['reconciliation_id', 'bank_account__account_name']
    readonly_fields = ['reconciliation_id', 'reconciled_balance', 'variance', 'is_balanced', 'created_at']
    date_hierarchy = 'reconciliation_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('reconciliation_id', 'bank_account', 'period_start', 'period_end', 'reconciliation_date')
        }),
        ('Opening Balances', {
            'fields': ('opening_book_balance', 'opening_bank_balance')
        }),
        ('Closing Balances', {
            'fields': ('closing_book_balance', 'closing_bank_balance')
        }),
        ('Reconciliation Items', {
            'fields': ('deposits_in_transit', 'outstanding_checks', 'bank_errors', 'book_errors')
        }),
        ('Results', {
            'fields': ('reconciled_balance', 'variance', 'is_balanced')
        }),
        ('Approval Workflow', {
            'fields': ('is_approved', 'notes', 'prepared_by', 'reviewed_by', 'approved_by')
        }),
        ('Dates', {
            'fields': ('reviewed_date', 'approved_date', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new reconciliation
            obj.prepared_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FixedAsset)
class FixedAssetAdmin(admin.ModelAdmin):
    list_display = ['asset_number', 'name', 'category', 'purchase_price', 'current_book_value', 'custodian', 'is_active']
    list_filter = ['category', 'is_active', 'purchase_date', 'manufacturer']
    search_fields = ['asset_number', 'name', 'serial_number', 'model_number']
    readonly_fields = ['asset_number', 'current_book_value', 'created_at', 'updated_at']
    date_hierarchy = 'purchase_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_number', 'name', 'description', 'category')
        }),
        ('Financial Details', {
            'fields': ('purchase_price', 'currency', 'purchase_date', 'useful_life_years', 'salvage_value')
        }),
        ('Depreciation', {
            'fields': ('depreciation_method', 'depreciation_rate', 'accumulated_depreciation', 'current_book_value')
        }),
        ('Asset Details', {
            'fields': ('serial_number', 'model_number', 'manufacturer', 'location')
        }),
        ('Ownership & Insurance', {
            'fields': ('supplier', 'warranty_expiry', 'insurance_policy', 'insurance_expiry')
        }),
        ('Responsibility', {
            'fields': ('custodian', 'department')
        }),
        ('Status', {
            'fields': ('is_active', 'disposal_date', 'disposal_amount', 'disposal_notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new asset
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'object_repr', 'risk_level', 'ip_address']
    list_filter = ['action', 'risk_level', 'timestamp', 'content_type']
    search_fields = ['user__username', 'object_repr', 'ip_address']
    readonly_fields = ['timestamp', 'user', 'action', 'content_type', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('timestamp', 'user', 'action', 'risk_level')
        }),
        ('Object Information', {
            'fields': ('content_type', 'object_id', 'object_repr')
        }),
        ('Changes', {
            'fields': ('changes', 'additional_data')
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'session_key'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Audit trails should only be created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit trails should be immutable
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit trails


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['rate_date', 'base_currency', 'target_currency', 'rate', 'source', 'created_by']
    list_filter = ['base_currency', 'target_currency', 'rate_date', 'source']
    search_fields = ['base_currency__code', 'target_currency__code']
    readonly_fields = ['created_at']
    date_hierarchy = 'rate_date'
    
    fieldsets = (
        ('Exchange Rate Information', {
            'fields': ('base_currency', 'target_currency', 'rate', 'rate_date', 'source')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new exchange rate
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
