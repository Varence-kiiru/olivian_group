from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),

    # Suppliers
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),

    # Warehouses
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/create/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/<int:pk>/edit/', views.WarehouseUpdateView.as_view(), name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', views.WarehouseDeleteView.as_view(), name='warehouse_delete'),

    # Inventory Items
    path('items/', views.InventoryItemListView.as_view(), name='item_list'),
    path('items/create/', views.InventoryItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.InventoryItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.InventoryItemUpdateView.as_view(), name='item_edit'),

    # Purchase Orders
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('purchase-orders/create/', views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('purchase-orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/edit/', views.PurchaseOrderUpdateView.as_view(), name='purchase_order_edit'),

    # Stock Movements
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),

    # Stock Adjustments
    path('adjustments/', views.StockAdjustmentListView.as_view(), name='adjustment_list'),
    path('adjustments/create/', views.StockAdjustmentCreateView.as_view(), name='adjustment_create'),
    path('adjustments/<int:pk>/', views.StockAdjustmentDetailView.as_view(), name='adjustment_detail'),
    path('adjustments/<int:pk>/edit/', views.StockAdjustmentUpdateView.as_view(), name='adjustment_edit'),

    # Stock Transfers
    path('transfers/', views.StockTransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', views.StockTransferCreateView.as_view(), name='transfer_create'),
    path('transfers/<int:pk>/', views.StockTransferDetailView.as_view(), name='transfer_detail'),
    path('transfers/<int:pk>/edit/', views.StockTransferUpdateView.as_view(), name='transfer_edit'),

    # Inventory Valuations
    path('valuations/', views.InventoryValuationListView.as_view(), name='valuation_list'),
    path('valuations/create/', views.InventoryValuationCreateView.as_view(), name='valuation_create'),
    path('valuations/<int:pk>/', views.InventoryValuationDetailView.as_view(), name='valuation_detail'),
    
    # API Endpoints
    path('api/low-stock-alerts/', views.LowStockAlertsAPIView.as_view(), name='api_low_stock_alerts'),
    path('api/stock-levels/', views.StockLevelsAPIView.as_view(), name='api_stock_levels'),
    path('api/products/', views.ProductsAPIView.as_view(), name='api_products'),

    # Legacy URLs (for backward compatibility)
    path('items/', views.InventoryItemListView.as_view(), name='items'),
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='purchase_orders'),
    path('stock-movements/', views.StockMovementListView.as_view(), name='stock_movements'),
]
