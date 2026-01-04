from django.urls import path
from . import views

app_name = 'financial'

urlpatterns = [
    # Dashboard
    path('', views.FinancialDashboardView.as_view(), name='dashboard'),
    
    # Currency Management
    path('currencies/', views.CurrencyListView.as_view(), name='currency_list'),
    path('currencies/<int:pk>/', views.CurrencyDetailView.as_view(), name='currency_detail'),
    path('currencies/create/', views.CurrencyCreateView.as_view(), name='currency_create'),
    path('currencies/<int:pk>/edit/', views.CurrencyUpdateView.as_view(), name='currency_update'),
    path('currencies/<int:pk>/delete/', views.CurrencyDeleteView.as_view(), name='currency_delete'),
    
    # Bank Management
    path('banks/', views.BankListView.as_view(), name='bank_list'),
    path('banks/<int:pk>/', views.BankDetailView.as_view(), name='bank_detail'),
    path('banks/create/', views.BankCreateView.as_view(), name='bank_create'),
    path('banks/<int:pk>/edit/', views.BankUpdateView.as_view(), name='bank_update'),
    path('banks/<int:pk>/delete/', views.BankDeleteView.as_view(), name='bank_delete'),
    
    # Bank Accounts
    path('accounts/', views.BankAccountListView.as_view(), name='account_list'),
    path('accounts/<int:pk>/', views.BankAccountDetailView.as_view(), name='account_detail'),
    path('accounts/create/', views.BankAccountCreateView.as_view(), name='account_create'),
    path('accounts/<int:pk>/edit/', views.BankAccountUpdateView.as_view(), name='account_update'),
    path('accounts/<int:pk>/delete/', views.BankAccountDeleteView.as_view(), name='account_delete'),
    path('accounts/<int:account_id>/balance-history/', views.account_balance_history, name='account_balance_history'),
    
    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('transactions/<int:transaction_id>/reconcile/', views.reconcile_transaction, name='reconcile_transaction'),
    
    # Bank Reconciliation
    path('reconciliations/', views.BankReconciliationListView.as_view(), name='reconciliation_list'),
    path('reconciliations/<int:pk>/', views.BankReconciliationDetailView.as_view(), name='reconciliation_detail'),
    path('reconciliations/create/', views.BankReconciliationCreateView.as_view(), name='reconciliation_create'),
    path('reconciliations/<int:pk>/edit/', views.BankReconciliationUpdateView.as_view(), name='reconciliation_update'),
    path('reconciliations/<int:pk>/delete/', views.BankReconciliationDeleteView.as_view(), name='reconciliation_delete'),
    
    # Fixed Assets
    path('assets/', views.FixedAssetListView.as_view(), name='asset_list'),
    path('assets/<int:pk>/', views.FixedAssetDetailView.as_view(), name='asset_detail'),
    path('assets/create/', views.FixedAssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/edit/', views.FixedAssetUpdateView.as_view(), name='asset_update'),
    path('assets/<int:pk>/delete/', views.FixedAssetDeleteView.as_view(), name='asset_delete'),
    
    # Exchange Rates
    path('exchange-rates/', views.ExchangeRateListView.as_view(), name='exchange_rate_list'),
    path('exchange-rates/<int:pk>/', views.ExchangeRateDetailView.as_view(), name='exchange_rate_detail'),
    path('exchange-rates/create/', views.ExchangeRateCreateView.as_view(), name='exchange_rate_create'),
    path('exchange-rates/<int:pk>/edit/', views.ExchangeRateUpdateView.as_view(), name='exchange_rate_update'),
    path('exchange-rates/<int:pk>/delete/', views.ExchangeRateDeleteView.as_view(), name='exchange_rate_delete'),
    
    # Audit Trail
    path('audit-trail/', views.AuditTrailListView.as_view(), name='audit_trail'),
    path('audit-trail/<int:pk>/', views.AuditTrailDetailView.as_view(), name='audit_trail_detail'),
    
    # Reports
    path('reports/', views.financial_reports, name='reports'),
    
    # AJAX endpoints
    path('api/currency-conversion/', views.currency_conversion_ajax, name='currency_conversion_ajax'),
]
