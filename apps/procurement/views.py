from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from .models import (
    Vendor, PurchaseRequisition, RFQ, PurchaseOrder, 
    PurchaseOrderItem, VendorPerformance
)


class ProcurementDashboardView(LoginRequiredMixin, ListView):
    """Procurement dashboard with key metrics"""
    template_name = 'procurement/dashboard.html'
    context_object_name = 'vendors'
    model = Vendor
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Key metrics
        context['total_vendors'] = Vendor.objects.filter(status='active').count()
        context['total_pos'] = PurchaseOrder.objects.count()
        context['pending_approvals'] = PurchaseRequisition.objects.filter(status='submitted').count()
        context['active_rfqs'] = RFQ.objects.filter(status__in=['sent', 'received']).count()
        
        # Recent activities
        context['recent_pos'] = PurchaseOrder.objects.select_related('vendor').order_by('-created_at')[:5]
        context['pending_requisitions'] = PurchaseRequisition.objects.filter(
            status='submitted'
        ).order_by('-created_at')[:5]
        
        # Charts data
        context['po_status_data'] = self.get_po_status_data()
        context['vendor_performance_data'] = self.get_vendor_performance_data()
        
        return context
    
    def get_po_status_data(self):
        """Get purchase order status distribution"""
        statuses = PurchaseOrder.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        return list(statuses)
    
    def get_vendor_performance_data(self):
        """Get vendor performance metrics"""
        performance = VendorPerformance.objects.values('vendor__company_name').annotate(
            avg_rating=Avg('delivery_rating'),
            total_orders=Count('purchase_order')
        ).order_by('-avg_rating')[:10]
        return list(performance)


class VendorListView(LoginRequiredMixin, ListView):
    """List all vendors with search and filtering"""
    model = Vendor
    template_name = 'procurement/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Vendor.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search) |
                Q(vendor_code__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by vendor type
        vendor_type = self.request.GET.get('vendor_type')
        if vendor_type:
            queryset = queryset.filter(vendor_type=vendor_type)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor_types'] = Vendor.VENDOR_TYPES
        context['status_choices'] = Vendor.STATUS_CHOICES
        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_vendor_type'] = self.request.GET.get('vendor_type', '')
        return context


class VendorDetailView(LoginRequiredMixin, DetailView):
    """Vendor detail view with performance metrics"""
    model = Vendor
    template_name = 'procurement/vendor_detail.html'
    context_object_name = 'vendor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.get_object()
        
        # Purchase orders for this vendor
        context['purchase_orders'] = vendor.purchase_orders.order_by('-created_at')[:10]
        context['total_pos'] = vendor.purchase_orders.count()
        
        # Performance metrics
        performance_records = vendor.performance_records.all()
        if performance_records:
            context['avg_delivery_rating'] = performance_records.aggregate(
                avg=Avg('delivery_rating')
            )['avg'] or 0
            context['avg_quality_rating'] = performance_records.aggregate(
                avg=Avg('quality_rating')
            )['avg'] or 0
            context['avg_service_rating'] = performance_records.aggregate(
                avg=Avg('service_rating')
            )['avg'] or 0
            context['total_orders'] = performance_records.count()
        else:
            context['avg_delivery_rating'] = 0
            context['avg_quality_rating'] = 0
            context['avg_service_rating'] = 0
            context['total_orders'] = 0
        
        return context


class VendorCreateView(LoginRequiredMixin, CreateView):
    """Create new vendor"""
    model = Vendor
    template_name = 'procurement/vendor_form.html'
    fields = [
        'company_name', 'contact_person', 'email', 'phone', 'alternative_phone',
        'address', 'city', 'postal_code', 'country', 'vendor_type',
        'tax_number', 'bank_name', 'bank_account', 'payment_terms',
        'status', 'credit_limit'
    ]
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Vendor {form.instance.company_name} created successfully!")
        return super().form_valid(form)


class VendorUpdateView(LoginRequiredMixin, UpdateView):
    """Update vendor information"""
    model = Vendor
    template_name = 'procurement/vendor_form.html'
    fields = [
        'company_name', 'contact_person', 'email', 'phone', 'alternative_phone',
        'address', 'city', 'postal_code', 'country', 'vendor_type',
        'tax_number', 'bank_name', 'bank_account', 'payment_terms',
        'status', 'credit_limit', 'rating'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, f"Vendor {form.instance.company_name} updated successfully!")
        return super().form_valid(form)


class PurchaseOrderListView(LoginRequiredMixin, ListView):
    """List all purchase orders"""
    model = PurchaseOrder
    template_name = 'procurement/po_list.html'
    context_object_name = 'purchase_orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PurchaseOrder.objects.select_related('vendor').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(po_number__icontains=search) |
                Q(title__icontains=search) |
                Q(vendor__company_name__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = PurchaseOrder.STATUS_CHOICES
        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context


class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    """Purchase order detail view"""
    model = PurchaseOrder
    template_name = 'procurement/po_detail.html'
    context_object_name = 'purchase_order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        po = self.get_object()
        context['items'] = po.items.all()
        return context


class PurchaseOrderCreateView(LoginRequiredMixin, CreateView):
    """Create new purchase order"""
    model = PurchaseOrder
    template_name = 'procurement/po_form.html'
    fields = [
        'vendor', 'title', 'description', 'priority', 'required_date',
        'payment_terms', 'delivery_terms'
    ]
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Purchase Order {form.instance.po_number} created successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = Vendor.objects.filter(status='active')
        return context


class RFQListView(LoginRequiredMixin, ListView):
    """List all RFQs"""
    model = RFQ
    template_name = 'procurement/rfq_list.html'
    context_object_name = 'rfqs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = RFQ.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(rfq_number__icontains=search) |
                Q(title__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')


class RFQDetailView(LoginRequiredMixin, DetailView):
    """RFQ detail view"""
    model = RFQ
    template_name = 'procurement/rfq_detail.html'
    context_object_name = 'rfq'


class PurchaseRequisitionListView(LoginRequiredMixin, ListView):
    """List all purchase requisitions"""
    model = PurchaseRequisition
    template_name = 'procurement/requisition_list.html'
    context_object_name = 'requisitions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PurchaseRequisition.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(requisition_number__icontains=search) |
                Q(title__icontains=search) |
                Q(department__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')


@login_required
def approve_requisition(request, pk):
    """Approve a purchase requisition"""
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            requisition.status = 'approved'
            requisition.approved_by = request.user
            requisition.approved_at = timezone.now()
            requisition.save()
            messages.success(request, f"Requisition {requisition.requisition_number} approved successfully!")
        
        elif action == 'reject':
            requisition.status = 'rejected'
            requisition.save()
            messages.warning(request, f"Requisition {requisition.requisition_number} rejected.")
        
        return redirect('procurement:requisition_list')
    
    return render(request, 'procurement/requisition_approve.html', {
        'requisition': requisition
    })


@login_required
def requisition_create_view(request):
    """Create new purchase requisition"""
    if request.method == 'POST':
        # Handle form submission
        # This would normally use a Django form
        return redirect('procurement:requisition_list')
    
    return render(request, 'procurement/requisition_form.html', {
        'form': {},  # Placeholder for form
    })


@login_required
def requisition_detail_view(request, pk):
    """View purchase requisition details"""
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    return render(request, 'procurement/requisition_detail.html', {
        'requisition': requisition,
        'today': timezone.now().date(),
    })


@login_required
def requisition_edit_view(request, pk):
    """Edit purchase requisition"""
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    
    if request.method == 'POST':
        # Handle form submission
        return redirect('procurement:requisition_detail', pk=pk)
    
    return render(request, 'procurement/requisition_form.html', {
        'form': {},  # Placeholder for form
        'requisition': requisition,
    })


@login_required
def goods_receipt_view(request, pk):
    """Goods receipt for purchase order"""
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    
    if request.method == 'POST':
        # Handle goods receipt submission
        return redirect('procurement:po_detail', pk=pk)
    
    return render(request, 'procurement/goods_receipt.html', {
        'purchase_order': purchase_order,
        'today': timezone.now().date(),
        'now': timezone.now(),
    })


@login_required
def supplier_performance_view(request):
    """Supplier performance analytics"""
    return render(request, 'procurement/supplier_performance.html', {})


@login_required
def contract_management_view(request):
    """Contract management interface"""
    return render(request, 'procurement/contract_management.html', {})


@login_required
def three_way_matching_view(request):
    """Three-way matching interface"""
    return render(request, 'procurement/three_way_matching.html', {})


@login_required
def procurement_reports_view(request):
    """Procurement reports and analytics"""
    return render(request, 'procurement/reports.html', {})


@login_required
def vendor_performance_ajax(request):
    """AJAX endpoint for vendor performance data"""
    vendor_id = request.GET.get('vendor_id')
    
    if vendor_id:
        performance = VendorPerformance.objects.filter(vendor_id=vendor_id).aggregate(
            avg_delivery=Avg('delivery_rating'),
            avg_quality=Avg('quality_rating'),
            avg_service=Avg('service_rating'),
            avg_price=Avg('price_rating'),
            total_orders=Count('id')
        )
        return JsonResponse(performance)
    
    return JsonResponse({'error': 'No vendor ID provided'}, status=400)
