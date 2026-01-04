from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Avg, Count, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
from decimal import Decimal

from .models import (
    Currency, Bank, BankAccount, Transaction, BankReconciliation,
    FixedAsset, AuditTrail, ExchangeRate
)


class FinancialDashboardView(LoginRequiredMixin, ListView):
    """Financial controls dashboard"""
    template_name = 'financial/dashboard.html'
    context_object_name = 'accounts'
    model = BankAccount
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active bank accounts
        context['bank_accounts'] = BankAccount.objects.filter(is_active=True).select_related('bank', 'currency')
        
        # Financial metrics
        context['total_cash'] = BankAccount.objects.filter(is_active=True).aggregate(
            total=Sum('current_balance'))['total'] or 0
        
        context['pending_reconciliations'] = BankReconciliation.objects.filter(
            is_approved=False).count()
        
        context['unreconciled_transactions'] = Transaction.objects.filter(
            is_reconciled=False).count()
        
        context['total_fixed_assets'] = FixedAsset.objects.filter(is_active=True).aggregate(
            total=Sum('current_book_value'))['total'] or 0
        
        # Recent transactions
        context['recent_transactions'] = Transaction.objects.select_related(
            'bank_account', 'currency'
        ).order_by('-created_date')[:10]
        
        # Pending reconciliations
        context['pending_reconciliations_list'] = BankReconciliation.objects.filter(
            is_approved=False
        ).select_related('bank_account').order_by('-created_at')[:5]
        
        # Currency summary
        context['currency_balances'] = BankAccount.objects.values(
            'currency__code', 'currency__symbol'
        ).annotate(
            total_balance=Sum('current_balance')
        ).filter(is_active=True)
        
        # Charts data
        context['cash_flow_data'] = self.get_cash_flow_data()
        context['account_balances_data'] = self.get_account_balances_data()
        
        return context
    
    def get_cash_flow_data(self):
        """Get cash flow data for the last 12 months"""
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=365)
            
            # Get transactions and group by month in Python for database compatibility
            transactions = Transaction.objects.filter(
                transaction_date__range=[start_date, end_date]
            ).values('transaction_date', 'transaction_type', 'amount')
            
            cash_flow = {}
            for txn in transactions:
                month = txn['transaction_date'].strftime('%Y-%m')
                txn_type = txn['transaction_type']
                key = f"{month}_{txn_type}"
                
                if key not in cash_flow:
                    cash_flow[key] = {
                        'month': month,
                        'transaction_type': txn_type,
                        'total': 0
                    }
                cash_flow[key]['total'] += float(txn['amount'])
            
            return list(cash_flow.values())
        except Exception:
            # Return empty list if there's any error
            return []
    
    def get_account_balances_data(self):
        """Get account balances for pie chart"""
        try:
            balances = BankAccount.objects.filter(is_active=True).values(
                'account_name', 'current_balance'
            )
            return list(balances)
        except Exception:
            # Return empty list if there's any error
            return []


class BankAccountListView(LoginRequiredMixin, ListView):
    """List all bank accounts"""
    model = BankAccount
    template_name = 'financial/account_list.html'
    context_object_name = 'accounts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = BankAccount.objects.select_related('bank', 'currency').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(account_name__icontains=search) |
                Q(account_number__icontains=search) |
                Q(bank__name__icontains=search)
            )
        
        # Filter by bank
        bank_id = self.request.GET.get('bank')
        if bank_id:
            queryset = queryset.filter(bank_id=bank_id)
        
        # Filter by currency
        currency_id = self.request.GET.get('currency')
        if currency_id:
            queryset = queryset.filter(currency_id=currency_id)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-is_default', 'account_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banks'] = Bank.objects.filter(is_active=True)
        context['currencies'] = Currency.objects.filter(is_active=True)
        context['current_search'] = self.request.GET.get('search', '')
        context['current_bank'] = self.request.GET.get('bank', '')
        context['current_currency'] = self.request.GET.get('currency', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context


class BankAccountDetailView(LoginRequiredMixin, DetailView):
    """Bank account detail view with transactions"""
    model = BankAccount
    template_name = 'financial/account_detail.html'
    context_object_name = 'account'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.get_object()
        
        # Recent transactions
        context['recent_transactions'] = account.transactions.order_by('-transaction_date')[:20]
        
        # Account statistics
        context['total_deposits'] = account.transactions.filter(
            transaction_type='deposit'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['total_withdrawals'] = account.transactions.filter(
            transaction_type='withdrawal'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['unreconciled_count'] = account.transactions.filter(
            is_reconciled=False
        ).count()
        
        # Recent reconciliations
        context['recent_reconciliations'] = account.reconciliations.order_by('-reconciliation_date')[:5]
        
        return context


class TransactionListView(LoginRequiredMixin, ListView):
    """List all transactions"""
    model = Transaction
    template_name = 'financial/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related('bank_account', 'currency').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(description__icontains=search) |
                Q(reference_number__icontains=search) |
                Q(counterparty_name__icontains=search)
            )
        
        # Filter by account
        account_id = self.request.GET.get('account')
        if account_id:
            queryset = queryset.filter(bank_account_id=account_id)
        
        # Filter by transaction type
        transaction_type = self.request.GET.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by reconciliation status
        reconciled = self.request.GET.get('reconciled')
        if reconciled == 'yes':
            queryset = queryset.filter(is_reconciled=True)
        elif reconciled == 'no':
            queryset = queryset.filter(is_reconciled=False)
        
        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        return queryset.order_by('-transaction_date', '-created_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_accounts'] = BankAccount.objects.filter(is_active=True)
        context['transaction_types'] = Transaction.TRANSACTION_TYPES
        context['status_choices'] = Transaction.TRANSACTION_STATUS
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'account': self.request.GET.get('account', ''),
            'type': self.request.GET.get('type', ''),
            'status': self.request.GET.get('status', ''),
            'reconciled': self.request.GET.get('reconciled', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        return context


class BankReconciliationListView(LoginRequiredMixin, ListView):
    """List all bank reconciliations"""
    model = BankReconciliation
    template_name = 'financial/reconciliation_list.html'
    context_object_name = 'reconciliations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = BankReconciliation.objects.select_related('bank_account').all()
        
        # Filter by account
        account_id = self.request.GET.get('account')
        if account_id:
            queryset = queryset.filter(bank_account_id=account_id)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'balanced':
            queryset = queryset.filter(is_balanced=True)
        elif status == 'unbalanced':
            queryset = queryset.filter(is_balanced=False)
        elif status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif status == 'pending':
            queryset = queryset.filter(is_approved=False)
        
        return queryset.order_by('-reconciliation_date')


class BankReconciliationCreateView(LoginRequiredMixin, CreateView):
    """Create new bank reconciliation"""
    model = BankReconciliation
    template_name = 'financial/reconciliation_form.html'
    fields = [
        'bank_account', 'period_start', 'period_end',
        'opening_book_balance', 'closing_book_balance',
        'opening_bank_balance', 'closing_bank_balance',
        'deposits_in_transit', 'outstanding_checks',
        'bank_errors', 'book_errors', 'notes'
    ]
    
    def form_valid(self, form):
        form.instance.prepared_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('financial:reconciliation_detail', kwargs={'pk': self.object.pk})


class FixedAssetListView(LoginRequiredMixin, ListView):
    """List all fixed assets"""
    model = FixedAsset
    template_name = 'financial/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = FixedAsset.objects.select_related('currency', 'custodian').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset_number__icontains=search) |
                Q(name__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(manufacturer__icontains=search)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'disposed':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('asset_number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = FixedAsset.ASSET_CATEGORIES
        context['current_search'] = self.request.GET.get('search', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        # Asset statistics
        context['total_assets'] = FixedAsset.objects.filter(is_active=True).count()
        context['total_value'] = FixedAsset.objects.filter(is_active=True).aggregate(
            total=Sum('current_book_value'))['total'] or 0
        context['assets_by_category'] = FixedAsset.objects.filter(is_active=True).values(
            'category'
        ).annotate(count=Count('id'), total_value=Sum('current_book_value'))
        
        return context


class AuditTrailListView(LoginRequiredMixin, ListView):
    """List audit trail records"""
    model = AuditTrail
    template_name = 'financial/audit_trail.html'
    context_object_name = 'audit_records'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = AuditTrail.objects.select_related('user', 'content_type').all()
        
        # Filter by user
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by risk level
        risk_level = self.request.GET.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset.order_by('-timestamp')


@login_required
def reconcile_transaction(request, transaction_id):
    """Mark a transaction as reconciled"""
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    if request.method == 'POST':
        if not transaction.is_reconciled:
            transaction.is_reconciled = True
            transaction.reconciled_date = timezone.now()
            transaction.reconciled_by = request.user
            transaction.save()
            
            messages.success(request, f"Transaction {transaction.transaction_id} has been reconciled.")
        else:
            messages.warning(request, "Transaction is already reconciled.")
    
    return redirect('financial:transaction_detail', pk=transaction_id)


@login_required
def currency_conversion_ajax(request):
    """AJAX endpoint for currency conversion"""
    from_currency = request.GET.get('from_currency')
    to_currency = request.GET.get('to_currency')
    amount = request.GET.get('amount')
    
    if not all([from_currency, to_currency, amount]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        amount = Decimal(amount)
        
        # Get latest exchange rate
        exchange_rate = ExchangeRate.objects.filter(
            base_currency__code=from_currency,
            target_currency__code=to_currency
        ).order_by('-rate_date').first()
        
        if exchange_rate:
            converted_amount = amount * exchange_rate.rate
            return JsonResponse({
                'converted_amount': float(converted_amount),
                'rate': float(exchange_rate.rate),
                'rate_date': exchange_rate.rate_date.isoformat()
            })
        else:
            return JsonResponse({'error': 'Exchange rate not found'}, status=404)
    
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid amount'}, status=400)


@login_required
def account_balance_history(request, account_id):
    """Get account balance history for charts"""
    account = get_object_or_404(BankAccount, pk=account_id)
    
    # Get transactions for the last 12 months
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)
    
    transactions = account.transactions.filter(
        transaction_date__range=[start_date, end_date]
    ).order_by('transaction_date')
    
    # Calculate running balance
    balance_history = []
    running_balance = account.current_balance
    
    for transaction in reversed(transactions):
        if transaction.transaction_type in ['deposit', 'receipt']:
            running_balance -= transaction.amount
        else:
            running_balance += transaction.amount
        
        balance_history.insert(0, {
            'date': transaction.transaction_date.isoformat(),
            'balance': float(running_balance),
            'transaction_id': transaction.transaction_id
        })
    
    return JsonResponse({'balance_history': balance_history})


@login_required
def financial_reports(request):
    """Financial reports dashboard"""
    context = {
        'title': 'Financial Reports',
        'report_types': [
            {
                'name': 'Cash Flow Statement',
                'description': 'Track cash inflows and outflows',
                'url': '#',  # TODO: Implement cash flow report
                'status': 'Coming Soon'
            },
            {
                'name': 'Bank Reconciliation Report',
                'description': 'Summary of bank reconciliations',
                'url': reverse('financial:reconciliation_list'),
                'status': 'Available'
            },
            {
                'name': 'Fixed Assets Register',
                'description': 'Complete list of fixed assets',
                'url': reverse('financial:asset_list'),
                'status': 'Available'
            },
            {
                'name': 'Transaction History',
                'description': 'Complete transaction audit trail',
                'url': reverse('financial:transaction_list'),
                'status': 'Available'
            },
            {
                'name': 'Audit Trail',
                'description': 'System activity and security audit',
                'url': reverse('financial:audit_trail'),
                'status': 'Available'
            },
        ]
    }
    
    return render(request, 'financial/reports.html', context)


# ====================== CURRENCY MANAGEMENT ======================

class CurrencyListView(LoginRequiredMixin, ListView):
    """List all currencies"""
    model = Currency
    template_name = 'financial/currency_list.html'
    context_object_name = 'currencies'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Currency.objects.all()
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(symbol__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-is_base_currency', 'code')


class CurrencyDetailView(LoginRequiredMixin, DetailView):
    """Currency detail view"""
    model = Currency
    template_name = 'financial/currency_detail.html'
    context_object_name = 'currency'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        currency = self.get_object()
        
        # Related accounts
        context['bank_accounts'] = currency.bankaccount_set.filter(is_active=True)
        
        # Exchange rates
        context['exchange_rates'] = currency.base_rates.order_by('-rate_date')[:10]
        
        # Usage statistics
        context['total_accounts'] = currency.bankaccount_set.count()
        context['total_balance'] = currency.bankaccount_set.aggregate(
            total=Sum('current_balance'))['total'] or 0
        
        return context


class CurrencyCreateView(LoginRequiredMixin, CreateView):
    """Create new currency"""
    model = Currency
    template_name = 'financial/currency_form.html'
    fields = ['code', 'name', 'symbol', 'decimal_places', 'is_base_currency', 'is_active', 'exchange_rate']
    
    def get_success_url(self):
        return reverse('financial:currency_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Currency {form.instance.code} created successfully.')
        return super().form_valid(form)


class CurrencyUpdateView(LoginRequiredMixin, UpdateView):
    """Update currency"""
    model = Currency
    template_name = 'financial/currency_form.html'
    fields = ['code', 'name', 'symbol', 'decimal_places', 'is_base_currency', 'is_active', 'exchange_rate']
    
    def get_success_url(self):
        return reverse('financial:currency_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Currency {form.instance.code} updated successfully.')
        return super().form_valid(form)


class CurrencyDeleteView(LoginRequiredMixin, DeleteView):
    """Delete currency"""
    model = Currency
    template_name = 'financial/currency_confirm_delete.html'
    success_url = reverse_lazy('financial:currency_list')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Currency {obj.code} deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ====================== BANK MANAGEMENT ======================

class BankListView(LoginRequiredMixin, ListView):
    """List all banks"""
    model = Bank
    template_name = 'financial/bank_list.html'
    context_object_name = 'banks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Bank.objects.all()
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(swift_code__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Bank statistics
        context['total_banks'] = Bank.objects.count()
        context['active_banks'] = Bank.objects.filter(is_active=True).count()
        context['total_accounts'] = BankAccount.objects.count()
        
        return context


class BankDetailView(LoginRequiredMixin, DetailView):
    """Bank detail view"""
    model = Bank
    template_name = 'financial/bank_detail.html'
    context_object_name = 'bank'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bank = self.get_object()
        
        # Related accounts
        context['bank_accounts'] = bank.accounts.filter(is_active=True)
        
        # Bank statistics
        context['total_accounts'] = bank.accounts.count()
        context['active_accounts'] = bank.accounts.filter(is_active=True).count()
        context['total_balance'] = bank.accounts.aggregate(
            total=Sum('current_balance'))['total'] or 0
        
        return context


class BankCreateView(LoginRequiredMixin, CreateView):
    """Create new bank"""
    model = Bank
    template_name = 'financial/bank_form.html'
    fields = ['name', 'code', 'swift_code', 'contact_info', 'central_bank_code', 'is_active']
    
    def get_success_url(self):
        return reverse('financial:bank_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Bank {form.instance.name} created successfully.')
        return super().form_valid(form)


class BankUpdateView(LoginRequiredMixin, UpdateView):
    """Update bank"""
    model = Bank
    template_name = 'financial/bank_form.html'
    fields = ['name', 'code', 'swift_code', 'contact_info', 'central_bank_code', 'is_active']
    
    def get_success_url(self):
        return reverse('financial:bank_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Bank {form.instance.name} updated successfully.')
        return super().form_valid(form)


class BankDeleteView(LoginRequiredMixin, DeleteView):
    """Delete bank"""
    model = Bank
    template_name = 'financial/bank_confirm_delete.html'
    success_url = reverse_lazy('financial:bank_list')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Bank {obj.name} deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ====================== ENHANCED BANK ACCOUNT MANAGEMENT ======================

class BankAccountCreateView(LoginRequiredMixin, CreateView):
    """Create new bank account"""
    model = BankAccount
    template_name = 'financial/account_form.html'
    fields = [
        'account_number', 'account_name', 'bank', 'account_type', 'currency',
        'current_balance', 'available_balance', 'branch_name', 'branch_code',
        'contact_person', 'contact_phone', 'is_active', 'is_default',
        'enable_auto_reconciliation'
    ]
    
    def get_success_url(self):
        return reverse('financial:account_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Bank account {form.instance.account_name} created successfully.')
        return super().form_valid(form)


class BankAccountUpdateView(LoginRequiredMixin, UpdateView):
    """Update bank account"""
    model = BankAccount
    template_name = 'financial/account_form.html'
    fields = [
        'account_number', 'account_name', 'bank', 'account_type', 'currency',
        'current_balance', 'available_balance', 'branch_name', 'branch_code',
        'contact_person', 'contact_phone', 'is_active', 'is_default',
        'enable_auto_reconciliation'
    ]
    
    def get_success_url(self):
        return reverse('financial:account_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Bank account {form.instance.account_name} updated successfully.')
        return super().form_valid(form)


class BankAccountDeleteView(LoginRequiredMixin, DeleteView):
    """Delete bank account"""
    model = BankAccount
    template_name = 'financial/account_confirm_delete.html'
    success_url = reverse_lazy('financial:account_list')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Bank account {obj.account_name} deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ====================== ENHANCED TRANSACTION MANAGEMENT ======================

class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Transaction detail view"""
    model = Transaction
    template_name = 'financial/transaction_detail.html'
    context_object_name = 'transaction'


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create new transaction"""
    model = Transaction
    template_name = 'financial/transaction_form.html'
    fields = [
        'bank_account', 'transaction_type', 'amount', 'currency', 'description',
        'reference_number', 'external_reference', 'counterparty_name',
        'counterparty_account', 'transaction_date', 'value_date', 'status'
    ]
    
    def get_success_url(self):
        return reverse('financial:transaction_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Transaction {form.instance.transaction_id} created successfully.')
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Update transaction"""
    model = Transaction
    template_name = 'financial/transaction_form.html'
    fields = [
        'bank_account', 'transaction_type', 'amount', 'currency', 'description',
        'reference_number', 'external_reference', 'counterparty_name',
        'counterparty_account', 'transaction_date', 'value_date', 'status'
    ]
    
    def get_success_url(self):
        return reverse('financial:transaction_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Transaction {form.instance.transaction_id} updated successfully.')
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete transaction"""
    model = Transaction
    template_name = 'financial/transaction_confirm_delete.html'
    success_url = reverse_lazy('financial:transaction_list')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Transaction {obj.transaction_id} deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ====================== ENHANCED BANK RECONCILIATION ======================

class BankReconciliationDetailView(LoginRequiredMixin, DetailView):
    """Bank reconciliation detail view"""
    model = BankReconciliation
    template_name = 'financial/reconciliation_detail.html'
    context_object_name = 'reconciliation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reconciliation = self.get_object()
        
        # Get unreconciled transactions for this account and period
        context['unreconciled_transactions'] = reconciliation.bank_account.transactions.filter(
            is_reconciled=False,
            transaction_date__range=[reconciliation.period_start, reconciliation.period_end]
        ).order_by('transaction_date')
        
        return context


class BankReconciliationUpdateView(LoginRequiredMixin, UpdateView):
    """Update bank reconciliation"""
    model = BankReconciliation
    template_name = 'financial/reconciliation_form.html'
    fields = [
        'bank_account', 'period_start', 'period_end',
        'opening_book_balance', 'closing_book_balance',
        'opening_bank_balance', 'closing_bank_balance',
        'deposits_in_transit', 'outstanding_checks',
        'bank_errors', 'book_errors', 'notes'
    ]
    
    def get_success_url(self):
        return reverse('financial:reconciliation_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Reconciliation {form.instance.reconciliation_id} updated successfully.')
        return super().form_valid(form)


class BankReconciliationDeleteView(LoginRequiredMixin, DeleteView):
    """Delete bank reconciliation"""
    model = BankReconciliation
    template_name = 'financial/reconciliation_confirm_delete.html'
    success_url = reverse_lazy('financial:reconciliation_list')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Reconciliation {obj.reconciliation_id} deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ====================== ENHANCED FIXED ASSET MANAGEMENT ======================

class FixedAssetDetailView(LoginRequiredMixin, DetailView):
    """Fixed asset detail view"""
    model = FixedAsset
    template_name = 'financial/asset_detail.html'
    context_object_name = 'asset'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_object()
        
        # Calculate depreciation metrics
        context['annual_depreciation'] = asset.calculate_annual_depreciation()
        context['depreciation_percentage'] = (
            (asset.accumulated_depreciation / asset.purchase_price * 100) 
            if asset.purchase_price > 0 else 0
        )
        
        # Age calculation
        if asset.purchase_date:
            context['asset_age_years'] = (timezone.now().date() - asset.purchase_date).days / 365.25
        
        return context


class FixedAssetCreateView(LoginRequiredMixin, CreateView):
    """Create new fixed asset"""
    model = FixedAsset
    template_name = 'financial/asset_form.html'
    fields = [
        'name', 'description', 'category', 'purchase_price', 'currency',
        'purchase_date', 'useful_life_years', 'salvage_value',
        'depreciation_method', 'depreciation_rate', 'serial_number',
        'model_number', 'manufacturer', 'location', 'supplier',
        'warranty_expiry', 'insurance_policy', 'insurance_expiry',
        'custodian', 'department', 'is_active'
    ]
    
    def get_success_url(self):
        return reverse('financial:asset_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Fixed asset {form.instance.name} created successfully.')
        return super().form_valid(form)


class FixedAssetUpdateView(LoginRequiredMixin, UpdateView):
    """Update fixed asset"""
    model = FixedAsset
    template_name = 'financial/asset_form.html'
    fields = [
        'name', 'description', 'category', 'purchase_price', 'currency',
        'purchase_date', 'useful_life_years', 'salvage_value',
        'depreciation_method', 'depreciation_rate', 'accumulated_depreciation',
        'serial_number', 'model_number', 'manufacturer', 'location', 'supplier',
        'warranty_expiry', 'insurance_policy', 'insurance_expiry',
        'custodian', 'department', 'is_active', 'disposal_date',
        'disposal_amount', 'disposal_notes'
    ]
    
    def get_success_url(self):
        return reverse('financial:asset_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Fixed asset {form.instance.name} updated successfully.')
        return super().form_valid(form)


class FixedAssetDeleteView(LoginRequiredMixin, DeleteView):
    """Delete fixed asset"""
    model = FixedAsset
    template_name = 'financial/asset_confirm_delete.html'
    success_url = reverse_lazy('financial:asset_list')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Fixed asset {obj.name} deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ====================== EXCHANGE RATE MANAGEMENT ======================

class ExchangeRateListView(LoginRequiredMixin, ListView):
    """List all exchange rates"""
    model = ExchangeRate
    template_name = 'financial/exchange_rate_list.html'
    context_object_name = 'exchange_rates'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = ExchangeRate.objects.select_related('base_currency', 'target_currency').all()
        
        # Filter by base currency
        base_currency = self.request.GET.get('base_currency')
        if base_currency:
            queryset = queryset.filter(base_currency__code=base_currency)
        
        # Filter by target currency
        target_currency = self.request.GET.get('target_currency')
        if target_currency:
            queryset = queryset.filter(target_currency__code=target_currency)
        
        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(rate_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(rate_date__lte=date_to)
        
        return queryset.order_by('-rate_date', 'base_currency__code', 'target_currency__code')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['currencies'] = Currency.objects.filter(is_active=True).order_by('code')
        context['current_filters'] = {
            'base_currency': self.request.GET.get('base_currency', ''),
            'target_currency': self.request.GET.get('target_currency', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        return context


class ExchangeRateDetailView(LoginRequiredMixin, DetailView):
    """Exchange rate detail view"""
    model = ExchangeRate
    template_name = 'financial/exchange_rate_detail.html'
    context_object_name = 'exchange_rate'


class ExchangeRateCreateView(LoginRequiredMixin, CreateView):
    """Create new exchange rate"""
    model = ExchangeRate
    template_name = 'financial/exchange_rate_form.html'
    fields = ['base_currency', 'target_currency', 'rate', 'rate_date', 'source']
    
    def get_success_url(self):
        return reverse('financial:exchange_rate_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Exchange rate created successfully.')
        return super().form_valid(form)


class ExchangeRateUpdateView(LoginRequiredMixin, UpdateView):
    """Update exchange rate"""
    model = ExchangeRate
    template_name = 'financial/exchange_rate_form.html'
    fields = ['base_currency', 'target_currency', 'rate', 'rate_date', 'source']
    
    def get_success_url(self):
        return reverse('financial:exchange_rate_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Exchange rate updated successfully.')
        return super().form_valid(form)


class ExchangeRateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete exchange rate"""
    model = ExchangeRate
    template_name = 'financial/exchange_rate_confirm_delete.html'
    success_url = reverse_lazy('financial:exchange_rate_list')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, 'Exchange rate deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ====================== ENHANCED AUDIT TRAIL ======================

class AuditTrailDetailView(LoginRequiredMixin, DetailView):
    """Audit trail detail view"""
    model = AuditTrail
    template_name = 'financial/audit_trail_detail.html'
    context_object_name = 'audit_record'
