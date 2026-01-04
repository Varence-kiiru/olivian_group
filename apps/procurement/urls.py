from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    # Dashboard
    path('', views.ProcurementDashboardView.as_view(), name='dashboard'),
    
    # Vendors
    path('vendors/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/create/', views.VendorCreateView.as_view(), name='vendor_create'),
    path('vendors/<int:pk>/', views.VendorDetailView.as_view(), name='vendor_detail'),
    path('vendors/<int:pk>/edit/', views.VendorUpdateView.as_view(), name='vendor_edit'),
    
    # Purchase Orders
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='po_list'),
    path('purchase-orders/create/', views.PurchaseOrderCreateView.as_view(), name='po_create'),
    path('purchase-orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='po_detail'),
    path('purchase-orders/<int:pk>/receive/', views.goods_receipt_view, name='goods_receipt'),
    
    # RFQs
    path('rfqs/', views.RFQListView.as_view(), name='rfq_list'),
    path('rfqs/<int:pk>/', views.RFQDetailView.as_view(), name='rfq_detail'),
    
    # Purchase Requisitions
    path('requisitions/', views.PurchaseRequisitionListView.as_view(), name='requisition_list'),
    path('requisitions/create/', views.requisition_create_view, name='requisition_create'),
    path('requisitions/<int:pk>/', views.requisition_detail_view, name='requisition_detail'),
    path('requisitions/<int:pk>/edit/', views.requisition_edit_view, name='requisition_edit'),
    path('requisitions/<int:pk>/approve/', views.approve_requisition, name='approve_requisition'),
    
    # Supplier Performance
    path('performance/', views.supplier_performance_view, name='supplier_performance'),
    
    # Contract Management
    path('contracts/', views.contract_management_view, name='contract_management'),
    
    # Three-Way Matching
    path('three-way-matching/', views.three_way_matching_view, name='three_way_matching'),
    
    # Reports
    path('reports/', views.procurement_reports_view, name='reports'),
    
    # AJAX endpoints
    path('api/vendor-performance/', views.vendor_performance_ajax, name='vendor_performance_ajax'),
]
