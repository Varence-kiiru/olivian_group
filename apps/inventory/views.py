from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, 
    TemplateView, FormView
)
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count, Avg, F
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    InventoryItem, PurchaseOrder, PurchaseOrderItem, StockMovement,
    Supplier, Warehouse, StockAdjustment, StockAdjustmentItem,
    StockTransfer, StockTransferItem, InventoryValuation, InventoryValuationItem
)
from apps.products.models import Product

# Dashboard
class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Summary statistics  
        total_quantity = InventoryItem.objects.aggregate(
            total=Sum('quantity_on_hand')
        )['total'] or Decimal('0')
        
        # Get low stock items with details
        low_stock_items = InventoryItem.objects.filter(
            quantity_on_hand__lte=F('reorder_point')
        ).select_related('product', 'warehouse')[:10]
        
        # Get out of stock items
        out_of_stock_items = InventoryItem.objects.filter(
            quantity_on_hand=0
        ).count()
        
        # Get overstock items
        overstock_items = InventoryItem.objects.filter(
            quantity_on_hand__gt=F('maximum_stock')
        ).select_related('product', 'warehouse')[:5]
        
        context.update({
            'total_products': InventoryItem.objects.count(),
            'total_quantity': total_quantity,
            'total_warehouses': Warehouse.objects.filter(is_active=True).count(),
            'total_suppliers': Supplier.objects.filter(is_active=True).count(),
            'pending_orders': PurchaseOrder.objects.filter(status__in=['sent', 'confirmed']).count(),
            'low_stock_items_count': low_stock_items.count(),
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'overstock_items_count': InventoryItem.objects.filter(
                quantity_on_hand__gt=F('maximum_stock')
            ).count(),
            'overstock_items': overstock_items,
            'total_stock_value': InventoryItem.objects.aggregate(
                total=Sum(F('quantity_on_hand') * F('average_cost'))
            )['total'] or Decimal('0'),
            'recent_movements': StockMovement.objects.select_related(
                'inventory_item__product', 'performed_by'
            ).order_by('-created_at')[:10],
        })
        
        return context

# Supplier Views
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier/list.html'
    context_object_name = 'suppliers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Supplier.objects.all()
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'preferred':
            queryset = queryset.filter(is_preferred=True)
            
        return queryset.order_by('-created_at')

class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'inventory/supplier/detail.html'
    context_object_name = 'supplier'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.get_object()
        
        context.update({
            'purchase_orders': supplier.purchase_orders.all()[:10],
            'total_orders': supplier.purchase_orders.count(),
            'total_amount': supplier.purchase_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0'),
            'outstanding_balance': supplier.get_outstanding_balance(),
        })
        
        return context

class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    template_name = 'inventory/supplier/form.html'
    fields = [
        'name', 'contact_person', 'email', 'phone', 'address', 'city', 'country',
        'tax_number', 'registration_number', 'bank_details', 'payment_terms',
        'credit_limit', 'lead_time_days', 'minimum_order_amount', 'rating',
        'is_active', 'is_preferred', 'website', 'notes'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, f'Supplier "{form.instance.name}" created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:supplier_detail', kwargs={'pk': self.object.pk})

class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    template_name = 'inventory/supplier/form.html'
    fields = [
        'name', 'contact_person', 'email', 'phone', 'address', 'city', 'country',
        'tax_number', 'registration_number', 'bank_details', 'payment_terms',
        'credit_limit', 'lead_time_days', 'minimum_order_amount', 'rating',
        'is_active', 'is_preferred', 'website', 'notes'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, f'Supplier "{form.instance.name}" updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:supplier_detail', kwargs={'pk': self.object.pk})

class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'inventory/supplier/confirm_delete.html'
    success_url = reverse_lazy('inventory:supplier_list')
    
    def delete(self, request, *args, **kwargs):
        supplier = self.get_object()
        if supplier.purchase_orders.exists():
            messages.error(request, f'Cannot delete supplier "{supplier.name}" - it has associated purchase orders.')
            return redirect('inventory:supplier_list')
        
        messages.success(request, f'Supplier "{supplier.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Warehouse Views
class WarehouseListView(LoginRequiredMixin, ListView):
    model = Warehouse
    template_name = 'inventory/warehouse/list.html'
    context_object_name = 'warehouses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Warehouse.objects.select_related('manager')
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(address__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset.order_by('-created_at')

class WarehouseDetailView(LoginRequiredMixin, DetailView):
    model = Warehouse
    template_name = 'inventory/warehouse/detail.html'
    context_object_name = 'warehouse'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouse = self.get_object()
        
        context.update({
            'inventory_items': warehouse.inventory_items.select_related('product')[:20],
            'total_items': warehouse.inventory_items.count(),
            'total_stock_value': warehouse.inventory_items.aggregate(
                total=Sum(F('quantity_on_hand') * F('average_cost'))
            )['total'] or Decimal('0'),
            'low_stock_count': warehouse.inventory_items.filter(
                quantity_on_hand__lte=F('reorder_point')
            ).count(),
            'capacity_utilization': warehouse.capacity_utilization,
        })
        
        return context

class WarehouseCreateView(LoginRequiredMixin, CreateView):
    model = Warehouse
    template_name = 'inventory/warehouse/form.html'
    fields = ['name', 'code', 'address', 'manager', 'total_capacity', 'is_active']
    
    def form_valid(self, form):
        messages.success(self.request, f'Warehouse "{form.instance.name}" created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:warehouse_detail', kwargs={'pk': self.object.pk})

class WarehouseUpdateView(LoginRequiredMixin, UpdateView):
    model = Warehouse
    template_name = 'inventory/warehouse/form.html'
    fields = ['name', 'code', 'address', 'manager', 'total_capacity', 'used_capacity', 'is_active']
    
    def form_valid(self, form):
        messages.success(self.request, f'Warehouse "{form.instance.name}" updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:warehouse_detail', kwargs={'pk': self.object.pk})

class WarehouseDeleteView(LoginRequiredMixin, DeleteView):
    model = Warehouse
    template_name = 'inventory/warehouse/confirm_delete.html'
    success_url = reverse_lazy('inventory:warehouse_list')
    
    def delete(self, request, *args, **kwargs):
        warehouse = self.get_object()
        if warehouse.inventory_items.exists():
            messages.error(request, f'Cannot delete warehouse "{warehouse.name}" - it contains inventory items.')
            return redirect('inventory:warehouse_list')
        
        messages.success(request, f'Warehouse "{warehouse.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Enhanced Inventory Item Views
class InventoryItemListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = 'inventory/items/list.html'
    context_object_name = 'items'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = InventoryItem.objects.select_related('product', 'warehouse')
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search) |
                Q(product__sku__icontains=search) |
                Q(bin_location__icontains=search)
            )
        
        # Warehouse filter
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Stock status filter
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low':
            queryset = queryset.filter(quantity_on_hand__lte=F('reorder_point'))
        elif stock_status == 'overstock':
            queryset = queryset.filter(quantity_on_hand__gt=F('maximum_stock'))
        elif stock_status == 'out_of_stock':
            queryset = queryset.filter(quantity_on_hand=0)
            
        return queryset.order_by('product__name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        return context

class InventoryItemDetailView(LoginRequiredMixin, DetailView):
    model = InventoryItem
    template_name = 'inventory/items/detail.html'
    context_object_name = 'item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.get_object()
        
        context.update({
            'recent_movements': item.movements.select_related(
                'performed_by'
            ).order_by('-created_at')[:20],
            'stock_value': item.quantity_on_hand * item.average_cost,
        })
        
        return context

class InventoryItemCreateView(LoginRequiredMixin, CreateView):
    model = InventoryItem
    template_name = 'inventory/items/form.html'
    fields = [
        'product', 'warehouse', 'quantity_on_hand', 'reorder_point', 'maximum_stock', 
        'safety_stock', 'average_cost', 'last_cost', 'bin_location', 'row', 'shelf'
    ]
    
    def get_initial(self):
        initial = super().get_initial()
        # Pre-select warehouse if passed in query params
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            initial['warehouse'] = warehouse_id
        return initial
    
    def form_valid(self, form):
        messages.success(self.request, f'Inventory item for "{form.instance.product.name}" created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:item_detail', kwargs={'pk': self.object.pk})

class InventoryItemUpdateView(LoginRequiredMixin, UpdateView):
    model = InventoryItem
    template_name = 'inventory/items/form.html'
    fields = [
        'warehouse', 'quantity_on_hand', 'reorder_point', 'maximum_stock', 'safety_stock',
        'average_cost', 'last_cost', 'bin_location', 'row', 'shelf'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, f'Inventory item "{form.instance.product.name}" updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:item_detail', kwargs={'pk': self.object.pk})

# Enhanced Purchase Order Views
class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order/list.html'
    context_object_name = 'purchase_orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PurchaseOrder.objects.select_related('supplier', 'warehouse', 'created_by')
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(po_number__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(supplier_reference__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Supplier filter
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suppliers'] = Supplier.objects.filter(is_active=True)
        return context

class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order/detail.html'
    context_object_name = 'purchase_order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        po = self.get_object()
        
        context.update({
            'items': po.items.select_related('product'),
            'can_receive': po.can_be_received(),
        })
        
        return context

class PurchaseOrderCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order/form.html'
    fields = [
        'supplier', 'warehouse', 'expected_delivery', 'payment_terms',
        'delivery_terms', 'notes', 'supplier_reference', 'shipping_cost'
    ]
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Purchase Order "{form.instance.po_number}" created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:purchase_order_detail', kwargs={'pk': self.object.pk})

class PurchaseOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order/form.html'
    fields = [
        'supplier', 'warehouse', 'expected_delivery', 'payment_terms',
        'delivery_terms', 'notes', 'supplier_reference', 'shipping_cost', 'status'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, f'Purchase Order "{form.instance.po_number}" updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:purchase_order_detail', kwargs={'pk': self.object.pk})

# Stock Movement Views
class StockMovementListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = 'inventory/movement/list.html'
    context_object_name = 'movements'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = StockMovement.objects.select_related(
            'inventory_item__product', 'inventory_item__warehouse', 'performed_by'
        )
        
        # Date filter
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Movement type filter
        movement_type = self.request.GET.get('movement_type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        
        # Warehouse filter
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(inventory_item__warehouse_id=warehouse_id)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        context['movement_types'] = StockMovement.MOVEMENT_TYPES
        return context

# Stock Adjustment Views
class StockAdjustmentListView(LoginRequiredMixin, ListView):
    model = StockAdjustment
    template_name = 'inventory/adjustment/list.html'
    context_object_name = 'adjustments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = StockAdjustment.objects.select_related('warehouse', 'performed_by', 'approved_by')
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(adjustment_number__icontains=search) |
                Q(reason__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status == 'approved':
            queryset = queryset.filter(approved=True)
        elif status == 'pending':
            queryset = queryset.filter(approved=False)
        
        # Warehouse filter
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        return context

class StockAdjustmentDetailView(LoginRequiredMixin, DetailView):
    model = StockAdjustment
    template_name = 'inventory/adjustment/detail.html'
    context_object_name = 'adjustment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        adjustment = self.get_object()
        
        context.update({
            'items': adjustment.items.select_related('inventory_item__product'),
            'total_adjustment_value': sum(
                item.adjustment_quantity * item.inventory_item.average_cost 
                for item in adjustment.items.all()
            ),
        })
        
        return context

class StockAdjustmentCreateView(LoginRequiredMixin, CreateView):
    model = StockAdjustment
    template_name = 'inventory/adjustment/form.html'
    fields = ['adjustment_type', 'warehouse', 'reason', 'adjustment_date']
    
    def form_valid(self, form):
        form.instance.performed_by = self.request.user
        messages.success(self.request, f'Stock Adjustment "{form.instance.adjustment_number}" created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:adjustment_detail', kwargs={'pk': self.object.pk})

class StockAdjustmentUpdateView(LoginRequiredMixin, UpdateView):
    model = StockAdjustment
    template_name = 'inventory/adjustment/form.html'
    fields = ['adjustment_type', 'warehouse', 'reason', 'adjustment_date', 'approved']
    
    def form_valid(self, form):
        if form.instance.approved and not form.instance.approved_by:
            form.instance.approved_by = self.request.user
            form.instance.approved_date = timezone.now()
        
        messages.success(self.request, f'Stock Adjustment "{form.instance.adjustment_number}" updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:adjustment_detail', kwargs={'pk': self.object.pk})

# Stock Transfer Views
class StockTransferListView(LoginRequiredMixin, ListView):
    model = StockTransfer
    template_name = 'inventory/transfer/list.html'
    context_object_name = 'transfers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = StockTransfer.objects.select_related(
            'from_warehouse', 'to_warehouse', 'initiated_by', 'received_by'
        )
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(transfer_number__icontains=search) |
                Q(reason__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Warehouse filter
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(
                Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
            )
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        return context

class StockTransferDetailView(LoginRequiredMixin, DetailView):
    model = StockTransfer
    template_name = 'inventory/transfer/detail.html'
    context_object_name = 'transfer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transfer = self.get_object()
        
        context.update({
            'items': transfer.items.select_related('product'),
            'total_items': transfer.items.count(),
            'total_quantity': transfer.items.aggregate(
                total=Sum('quantity_sent')
            )['total'] or Decimal('0'),
        })
        
        return context

class StockTransferCreateView(LoginRequiredMixin, CreateView):
    model = StockTransfer
    template_name = 'inventory/transfer/form.html'
    fields = ['from_warehouse', 'to_warehouse', 'expected_arrival', 'reason', 'notes']
    
    def form_valid(self, form):
        form.instance.initiated_by = self.request.user
        messages.success(self.request, f'Stock Transfer "{form.instance.transfer_number}" created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:transfer_detail', kwargs={'pk': self.object.pk})

class StockTransferUpdateView(LoginRequiredMixin, UpdateView):
    model = StockTransfer
    template_name = 'inventory/transfer/form.html'
    fields = [
        'from_warehouse', 'to_warehouse', 'expected_arrival', 'actual_arrival',
        'reason', 'notes', 'status'
    ]
    
    def form_valid(self, form):
        if form.instance.status == 'received' and not form.instance.received_by:
            form.instance.received_by = self.request.user
            if not form.instance.actual_arrival:
                form.instance.actual_arrival = timezone.now().date()
        
        messages.success(self.request, f'Stock Transfer "{form.instance.transfer_number}" updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('inventory:transfer_detail', kwargs={'pk': self.object.pk})

# Inventory Valuation Views
class InventoryValuationListView(LoginRequiredMixin, ListView):
    model = InventoryValuation
    template_name = 'inventory/valuation/list.html'
    context_object_name = 'valuations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = InventoryValuation.objects.select_related('warehouse', 'performed_by')
        
        # Warehouse filter
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Date range filter
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(valuation_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(valuation_date__lte=end_date)
            
        return queryset.order_by('-valuation_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        return context

class InventoryValuationDetailView(LoginRequiredMixin, DetailView):
    model = InventoryValuation
    template_name = 'inventory/valuation/detail.html'
    context_object_name = 'valuation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        valuation = self.get_object()
        
        context.update({
            'items': valuation.items.select_related('inventory_item__product'),
            'summary': {
                'total_items': valuation.items.count(),
                'total_quantity': valuation.total_quantity,
                'total_value': valuation.total_value,
                'average_unit_cost': valuation.total_value / valuation.total_quantity if valuation.total_quantity > 0 else Decimal('0'),
            }
        })
        
        return context

class InventoryValuationCreateView(LoginRequiredMixin, CreateView):
    model = InventoryValuation
    template_name = 'inventory/valuation/form.html'
    fields = ['warehouse', 'valuation_date', 'valuation_method']
    
    def form_valid(self, form):
        form.instance.performed_by = self.request.user
        
        # Calculate totals after saving
        valuation = form.save()
        
        # Get all inventory items for the warehouse
        inventory_items = InventoryItem.objects.filter(warehouse=valuation.warehouse)
        
        total_quantity = Decimal('0')
        total_value = Decimal('0')
        
        # Create valuation items
        for item in inventory_items:
            if item.quantity_on_hand > 0:
                unit_value = item.average_cost if valuation.valuation_method == 'weighted_average' else item.last_cost
                item_total_value = item.quantity_on_hand * unit_value
                
                InventoryValuationItem.objects.create(
                    valuation=valuation,
                    inventory_item=item,
                    quantity=item.quantity_on_hand,
                    unit_value=unit_value,
                    total_value=item_total_value
                )
                
                total_quantity += item.quantity_on_hand
                total_value += item_total_value
        
        # Update valuation totals
        valuation.total_quantity = total_quantity
        valuation.total_value = total_value
        valuation.save()
        
        messages.success(self.request, f'Inventory Valuation for "{valuation.warehouse.name}" created successfully.')
        return redirect('inventory:valuation_detail', pk=valuation.pk)
    
    def get_success_url(self):
        return reverse('inventory:valuation_detail', kwargs={'pk': self.object.pk})

# API Views for AJAX functionality
class LowStockAlertsAPIView(LoginRequiredMixin, View):
    """Get low stock alerts"""
    
    def get(self, request):
        low_stock_items = InventoryItem.objects.filter(
            quantity_on_hand__lte=F('reorder_point')
        ).select_related('product', 'warehouse')[:10]
        
        alerts = []
        for item in low_stock_items:
            alerts.append({
                'product_name': item.product.name,
                'warehouse': item.warehouse.name,
                'current_stock': float(item.quantity_on_hand),
                'reorder_point': float(item.reorder_point),
                'shortage': float(item.reorder_point - item.quantity_on_hand),
            })
        
        return JsonResponse({'alerts': alerts})

class StockLevelsAPIView(LoginRequiredMixin, View):
    """Get stock levels for a product across warehouses"""
    
    def get(self, request):
        product_id = request.GET.get('product_id')
        if not product_id:
            return JsonResponse({'error': 'Product ID required'}, status=400)
        
        items = InventoryItem.objects.filter(
            product_id=product_id
        ).select_related('warehouse')
        
        stock_levels = []
        for item in items:
            stock_levels.append({
                'warehouse': item.warehouse.name,
                'quantity_on_hand': float(item.quantity_on_hand),
                'available_quantity': float(item.available_quantity),
                'reorder_point': float(item.reorder_point),
                'bin_location': item.bin_location,
            })
        
        return JsonResponse({'stock_levels': stock_levels})

class ProductsAPIView(LoginRequiredMixin, View):
    """Get products for inventory item selection"""
    
    def get(self, request):
        from apps.products.models import Product
        
        search = request.GET.get('search', '')
        
        products = Product.objects.all()
        
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Show all products - multiple inventory items per product are now supported
        
        products = products[:20]  # Limit results
        
        results = []
        for product in products:
            results.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': product.category.name if product.category else None,
                'image': product.image.url if product.image else None,
            })
        
        return JsonResponse({'results': results})
