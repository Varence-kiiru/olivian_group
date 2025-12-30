from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    # Main POS Interface
    path('', views.POSMainView.as_view(), name='main'),
    path('terminal/<int:terminal_id>/', views.POSTerminalView.as_view(), name='terminal'),
    
    # Session Management
    path('session/start/', views.StartSessionView.as_view(), name='start_session'),
    path('session/<int:session_id>/close/', views.CloseSessionView.as_view(), name='close_session'),
    path('session/<int:session_id>/suspend/', views.SuspendSessionView.as_view(), name='suspend_session'),
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    
    # Sales
    path('sale/new/', views.NewSaleView.as_view(), name='new_sale'),
    path('sale/<int:sale_id>/', views.SaleDetailView.as_view(), name='sale_detail'),
    path('sale/<int:sale_id>/payment/', views.ProcessPaymentView.as_view(), name='process_payment'),
    path('sale/<int:sale_id>/receipt/', views.PrintReceiptView.as_view(), name='print_receipt'),
    path('sales/', views.SaleListView.as_view(), name='sale_list'),
    
    # Customers
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_update'),
    
    # Products & Inventory
    path('products/search/', views.ProductSearchView.as_view(), name='product_search'),
    path('products/<int:product_id>/details/', views.ProductDetailsView.as_view(), name='product_details'),
    path('inventory/check/', views.InventoryCheckView.as_view(), name='inventory_check'),
    
    # Cash Management
    path('cash/movements/', views.CashMovementListView.as_view(), name='cash_movement_list'),
    path('cash/movement/create/', views.CashMovementCreateView.as_view(), name='cash_movement_create'),
    path('cash/drop/', views.CashDropView.as_view(), name='cash_drop'),
    path('cash/payout/', views.CashPayoutView.as_view(), name='cash_payout'),
    
    # Discounts
    path('discounts/', views.DiscountListView.as_view(), name='discount_list'),
    path('discounts/apply/', views.ApplyDiscountView.as_view(), name='apply_discount'),
    
    # Reports
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/daily-sales/', views.DailySalesReportView.as_view(), name='daily_sales_report'),
    path('reports/cashier-performance/', views.CashierPerformanceReportView.as_view(), name='cashier_performance'),
    path('reports/product-sales/', views.ProductSalesReportView.as_view(), name='product_sales'),
    
    # Settings
    path('settings/', views.POSSettingsView.as_view(), name='settings'),
    path('settings/stores/', views.StoreManagementView.as_view(), name='store_management'),
    path('settings/stores/add/', views.AddStoreView.as_view(), name='add_store'),
    path('settings/stores/<int:pk>/edit/', views.EditStoreView.as_view(), name='edit_store'),
    path('settings/stores/<int:pk>/delete/', views.DeleteStoreView.as_view(), name='delete_store'),
    path('settings/terminals/', views.TerminalManagementView.as_view(), name='terminal_management'),
    path('settings/terminals/add/', views.AddTerminalView.as_view(), name='add_terminal'),
    path('settings/terminals/<int:pk>/edit/', views.EditTerminalView.as_view(), name='edit_terminal'),
    path('settings/terminals/<int:pk>/delete/', views.DeleteTerminalView.as_view(), name='delete_terminal'),
    
    # API Endpoints for AJAX/Real-time functionality
    path('api/cart/add-item/', views.AddToCartAPIView.as_view(), name='api_add_to_cart'),
    path('api/cart/remove-item/', views.RemoveFromCartAPIView.as_view(), name='api_remove_from_cart'),
    path('api/cart/update-quantity/', views.UpdateCartQuantityAPIView.as_view(), name='api_update_quantity'),
    path('api/cart/apply-discount/', views.ApplyDiscountAPIView.as_view(), name='api_apply_discount'),
    path('api/customer/search/', views.CustomerSearchAPIView.as_view(), name='api_customer_search'),
    path('api/customer/create/', views.CustomerCreateAPIView.as_view(), name='api_customer_create'),
    path('api/product/barcode/', views.ProductBarcodeAPIView.as_view(), name='api_product_barcode'),
    path('api/payment/process/', views.ProcessPaymentAPIView.as_view(), name='api_process_payment'),
    path('api/receipt/print/', views.PrintReceiptAPIView.as_view(), name='api_print_receipt'),
    path('api/terminal/active/', views.GetActiveTerminalAPIView.as_view(), name='api_get_active_terminal'),
    path('api/mpesa/status/', views.POSMPesaStatusAPIView.as_view(), name='api_mpesa_status'),
    path('api/mpesa/callback/', views.POSMPesaCallbackView.as_view(), name='api_mpesa_callback'),
    
    # Offline sync endpoints
    path('api/sync/sales/', views.SyncSalesAPIView.as_view(), name='api_sync_sales'),
    path('api/sync/inventory/', views.SyncInventoryAPIView.as_view(), name='api_sync_inventory'),
]
