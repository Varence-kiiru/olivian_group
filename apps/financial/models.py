from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
import uuid

User = get_user_model()


class Currency(models.Model):
    """Supported currencies for multi-currency support"""
    code = models.CharField(max_length=3, unique=True, help_text="ISO 4217 currency code")
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    decimal_places = models.PositiveIntegerField(default=2)
    is_base_currency = models.BooleanField(default=False, help_text="Primary business currency")
    is_active = models.BooleanField(default=True)

    # Exchange rate (relative to base currency)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1.000000)
    last_updated = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
    
    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        # Ensure only one base currency
        if self.is_base_currency:
            Currency.objects.filter(is_base_currency=True).update(is_base_currency=False)
            self.exchange_rate = 1.000000
        super().save(*args, **kwargs)


class Bank(models.Model):
    """Bank institutions"""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Bank code (e.g., KCB, EQUITY)")
    swift_code = models.CharField(max_length=11, blank=True, help_text="SWIFT/BIC code")
    contact_info = models.TextField(blank=True)

    # Kenya-specific
    central_bank_code = models.CharField(max_length=10, blank=True, help_text="CBK institution code")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Bank'
        verbose_name_plural = 'Banks'

    def __str__(self):
        return f"{self.name} ({self.code})"


class BankAccount(models.Model):
    """Company bank accounts"""
    ACCOUNT_TYPES = [
        ('current', 'Current Account'),
        ('savings', 'Savings Account'),
        ('fixed_deposit', 'Fixed Deposit'),
        ('credit', 'Credit Account'),
        ('overdraft', 'Overdraft Account'),
        ('mpesa', 'M-Pesa Account'),
        ('mobile_money', 'Mobile Money Account'),
    ]

    account_number = models.CharField(max_length=50, unique=True)
    account_name = models.CharField(max_length=200)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='accounts')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='current')
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    
    # Balance tracking
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_reconciled_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_reconciled_date = models.DateField(null=True, blank=True)
    
    # Account details
    branch_name = models.CharField(max_length=200, blank=True)
    branch_code = models.CharField(max_length=20, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default account for transactions")
    enable_auto_reconciliation = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bank_accounts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', 'account_name']
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'
    
    def __str__(self):
        return f"{self.account_name} - {self.account_number}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default account per currency
        if self.is_default:
            BankAccount.objects.filter(
                currency=self.currency, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('financial:account_detail', kwargs={'pk': self.pk})


class Transaction(models.Model):
    """Financial transactions"""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
        ('receipt', 'Receipt'),
        ('fee', 'Bank Fee'),
        ('interest', 'Interest'),
        ('adjustment', 'Adjustment'),
    ]
    
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
        ('reconciled', 'Reconciled'),
    ]
    
    # Core transaction info
    transaction_id = models.CharField(max_length=50, unique=True, blank=True)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    
    # Transaction details
    description = models.TextField()
    reference_number = models.CharField(max_length=100, blank=True, help_text="Bank reference/check number")
    external_reference = models.CharField(max_length=100, blank=True, help_text="External system reference")
    
    # Parties involved
    counterparty_name = models.CharField(max_length=200, blank=True)
    counterparty_account = models.CharField(max_length=50, blank=True)
    
    # Dates
    transaction_date = models.DateField()
    value_date = models.DateField(help_text="Date when funds are available")
    created_date = models.DateTimeField(auto_now_add=True)
    
    # Status and reconciliation
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    is_reconciled = models.BooleanField(default=False)
    reconciled_date = models.DateTimeField(null=True, blank=True)
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reconciled_transactions')
    
    # Related record (generic foreign key for linking to other models)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Balance after transaction
    running_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    
    class Meta:
        ordering = ['-transaction_date', '-created_date']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['transaction_date', 'bank_account']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['status', 'is_reconciled']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.description}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate transaction ID: TXN-YYYY-XXXXXX
            current_year = timezone.now().year
            last_txn = Transaction.objects.filter(
                transaction_id__startswith=f'TXN-{current_year}'
            ).order_by('-transaction_id').first()
            
            if last_txn:
                last_number = int(last_txn.transaction_id.split('-')[-1])
                next_number = last_number + 1
            else:
                next_number = 1
            
            self.transaction_id = f'TXN-{current_year}-{next_number:06d}'
        
        # Set currency from bank account if not specified
        if not self.currency_id:
            self.currency = self.bank_account.currency
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('financial:transaction_detail', kwargs={'pk': self.pk})


class BankReconciliation(models.Model):
    """Bank reconciliation records"""
    reconciliation_id = models.CharField(max_length=50, unique=True, blank=True)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='reconciliations')
    
    # Reconciliation period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Balances
    opening_book_balance = models.DecimalField(max_digits=15, decimal_places=2)
    closing_book_balance = models.DecimalField(max_digits=15, decimal_places=2)
    opening_bank_balance = models.DecimalField(max_digits=15, decimal_places=2)
    closing_bank_balance = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Reconciliation items
    deposits_in_transit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outstanding_checks = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bank_errors = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    book_errors = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Calculated reconciled balance
    reconciled_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Status
    is_balanced = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    # Workflow
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prepared_reconciliations')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reconciliations')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reconciliations')
    
    # Dates
    reconciliation_date = models.DateField(default=timezone.now)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-reconciliation_date']
        verbose_name = 'Bank Reconciliation'
        verbose_name_plural = 'Bank Reconciliations'
        unique_together = ['bank_account', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.reconciliation_id} - {self.bank_account.account_name}"
    
    def save(self, *args, **kwargs):
        if not self.reconciliation_id:
            # Generate reconciliation ID: REC-YYYY-0001
            current_year = timezone.now().year
            last_rec = BankReconciliation.objects.filter(
                reconciliation_id__startswith=f'REC-{current_year}'
            ).order_by('-reconciliation_id').first()
            
            if last_rec:
                last_number = int(last_rec.reconciliation_id.split('-')[-1])
                next_number = last_number + 1
            else:
                next_number = 1
            
            self.reconciliation_id = f'REC-{current_year}-{next_number:04d}'
        
        # Calculate reconciled balance and variance
        self.reconciled_balance = (
            self.closing_bank_balance + 
            self.deposits_in_transit - 
            self.outstanding_checks + 
            self.bank_errors - 
            self.book_errors
        )
        self.variance = self.closing_book_balance - self.reconciled_balance
        self.is_balanced = abs(self.variance) < 0.01  # Within 1 cent
        
        super().save(*args, **kwargs)


class FixedAsset(models.Model):
    """Fixed asset management"""
    ASSET_CATEGORIES = [
        ('building', 'Buildings'),
        ('equipment', 'Equipment'),
        ('vehicle', 'Vehicles'),
        ('furniture', 'Furniture & Fixtures'),
        ('computer', 'Computer Equipment'),
        ('software', 'Software'),
        ('other', 'Other Assets'),
    ]
    
    DEPRECIATION_METHODS = [
        ('straight_line', 'Straight Line'),
        ('declining_balance', 'Declining Balance'),
        ('sum_of_years', 'Sum of Years Digits'),
        ('units_of_production', 'Units of Production'),
    ]
    
    # Basic information
    asset_number = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=ASSET_CATEGORIES)
    
    # Financial details
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    purchase_date = models.DateField()
    useful_life_years = models.PositiveIntegerField(help_text="Expected useful life in years")
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Depreciation
    depreciation_method = models.CharField(max_length=20, choices=DEPRECIATION_METHODS, default='straight_line')
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Annual depreciation rate %")
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_book_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Asset details
    serial_number = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Ownership and insurance
    supplier = models.ForeignKey('procurement.Vendor', on_delete=models.SET_NULL, null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    insurance_policy = models.CharField(max_length=100, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    disposal_date = models.DateField(null=True, blank=True)
    disposal_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    disposal_notes = models.TextField(blank=True)
    
    # Responsibility
    custodian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='custodian_assets')
    department = models.CharField(max_length=100, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_assets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['asset_number']
        verbose_name = 'Fixed Asset'
        verbose_name_plural = 'Fixed Assets'
    
    def __str__(self):
        return f"{self.asset_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.asset_number:
            # Generate asset number: AST-YYYY-0001
            current_year = timezone.now().year
            last_asset = FixedAsset.objects.filter(
                asset_number__startswith=f'AST-{current_year}'
            ).order_by('-asset_number').first()
            
            if last_asset:
                last_number = int(last_asset.asset_number.split('-')[-1])
                next_number = last_number + 1
            else:
                next_number = 1
            
            self.asset_number = f'AST-{current_year}-{next_number:04d}'
        
        # Calculate current book value
        self.current_book_value = self.purchase_price - self.accumulated_depreciation
        
        super().save(*args, **kwargs)
    
    def calculate_annual_depreciation(self):
        """Calculate annual depreciation amount"""
        if self.depreciation_method == 'straight_line':
            return (self.purchase_price - self.salvage_value) / self.useful_life_years
        elif self.depreciation_method == 'declining_balance':
            return self.current_book_value * (self.depreciation_rate / 100)
        # Add other methods as needed
        return 0


class AuditTrail(models.Model):
    """Enhanced audit trail for financial transactions"""
    ACTION_TYPES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('reconcile', 'Reconciled'),
        ('void', 'Voided'),
        ('export', 'Exported'),
        ('import', 'Imported'),
        ('login', 'User Login'),
        ('logout', 'User Logout'),
    ]
    
    # Core audit info
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # What was affected
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    
    # Change details
    changes = models.JSONField(default=dict, blank=True, help_text="Field changes in JSON format")
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Risk assessment
    risk_level = models.CharField(
        max_length=10, 
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='low'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trails'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['risk_level', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action} {self.object_repr} at {self.timestamp}"


class ExchangeRate(models.Model):
    """Historical exchange rates"""
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='base_rates')
    target_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='target_rates')
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    rate_date = models.DateField()
    source = models.CharField(max_length=100, default='Manual', help_text="Source of exchange rate")
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-rate_date']
        unique_together = ['base_currency', 'target_currency', 'rate_date']
        verbose_name = 'Exchange Rate'
        verbose_name_plural = 'Exchange Rates'
    
    def __str__(self):
        return f"1 {self.base_currency.code} = {self.rate} {self.target_currency.code}"
