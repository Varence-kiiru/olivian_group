from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, 
    TemplateView, View, FormView
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg, Max
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    Store, Terminal, CashierSession, Sale, SaleItem, 
    Payment, Discount, CashMovement, POSSettings
)
from apps.quotations.models import Customer
from .forms import (
    SessionStartForm, CustomerForm, SaleForm, PaymentForm, 
    CashMovementForm, DiscountForm
)
from apps.products.models import Product
from apps.inventory.models import InventoryItem
from apps.ecommerce.models import MPesaTransaction
from apps.ecommerce.mpesa import MPesaCallback
from apps.core.models import CompanySettings


class POSMainView(LoginRequiredMixin, TemplateView):
    """Main POS dashboard"""
    template_name = 'pos/main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's store and available terminals
        try:
            # Assuming cashier is assigned to a specific store
            store = Store.objects.filter(
                Q(manager=user) | Q(terminals__current_cashier=user)
            ).first()
            
            if store:
                context['store'] = store
                context['terminals'] = store.terminals.filter(is_active=True)
                
                # Get current session if any
                current_session = CashierSession.objects.filter(
                    cashier=user,
                    status='active'
                ).first()
                
                context['current_session'] = current_session
                
                # Quick stats for today
                today = timezone.now().date()
                context.update({
                    'today_sales': Sale.objects.filter(
                        session__terminal__store=store,
                        transaction_time__date=today,
                        status='completed'
                    ).aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00'),
                    
                    'today_transactions': Sale.objects.filter(
                        session__terminal__store=store,
                        transaction_time__date=today,
                        status='completed'
                    ).count(),
                    
                    'active_sessions': CashierSession.objects.filter(
                        terminal__store=store,
                        status='active'
                    ).count(),
                })
            
        except Exception as e:
            messages.warning(self.request, "Unable to load store information.")
        
        return context


class POSTerminalView(LoginRequiredMixin, TemplateView):
    """POS terminal interface"""
    template_name = 'pos/terminal.html'
    
    def get(self, request, *args, **kwargs):
        terminal_id = kwargs.get('terminal_id')
        
        try:
            terminal = get_object_or_404(Terminal, id=terminal_id, is_active=True)
            
            # Check if user has active session on this terminal
            session = CashierSession.objects.filter(
                cashier=request.user,
                terminal=terminal,
                status='active'
            ).first()
            
            if not session:
                messages.warning(request, "No active session. Please start a session first.")
                return redirect('pos:start_session')
                
        except Exception as e:
            messages.error(request, f"Error loading terminal: {str(e)}")
            return redirect('pos:main')
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        terminal_id = kwargs.get('terminal_id')
        
        terminal = get_object_or_404(Terminal, id=terminal_id, is_active=True)
        context['terminal'] = terminal
        
        # Get active session (we know it exists from get() method)
        session = CashierSession.objects.filter(
            cashier=self.request.user,
            terminal=terminal,
            status='active'
        ).first()
        
        context['session'] = session
        
        # Get recent sales for this session
        context['recent_sales'] = Sale.objects.filter(
            session=session
        ).order_by('-transaction_time')[:10] if session else []
        
        # Get products for POS - all active products for now
        context['products'] = Product.objects.filter(
            status='active'
        ).select_related('category').prefetch_related('images')
        
        # Get product categories
        from apps.products.models import ProductCategory
        context['categories'] = ProductCategory.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Get recent customers
        context['customers'] = Customer.objects.all().order_by('-created_at')[:20]
        
        # Get current cart (if any) - stored in session
        cart = self.request.session.get('pos_cart', [])
        context['cart_items'] = cart
        context['cart_total'] = sum(
            Decimal(str(item['quantity'])) * Decimal(str(item['price'])) 
            for item in cart
        )
        
        return context


class StartSessionView(LoginRequiredMixin, FormView):
    """Start cashier session"""
    template_name = 'pos/start_session.html'
    form_class = SessionStartForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get available terminals/registers for selection
        context['registers'] = Terminal.objects.filter(is_active=True)
        # Get active sessions to show on the page
        context['active_sessions'] = CashierSession.objects.filter(
            status='active'
        ).select_related('cashier', 'terminal')
        context['today'] = timezone.now().date()
        context['now'] = timezone.now()
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        terminal = form.cleaned_data['terminal']
        opening_cash = form.cleaned_data['opening_cash']
        opening_notes = form.cleaned_data.get('opening_notes', '')
        
        # Check if terminal is already in use
        if terminal.current_cashier:
            messages.error(self.request, f"Terminal {terminal.name} is already in use.")
            return self.form_invalid(form)
        
        # Check if user already has an active session
        existing_session = CashierSession.objects.filter(
            cashier=self.request.user,
            status='active'
        ).first()
        
        if existing_session:
            messages.warning(self.request, f"You already have an active session. Continue with session {existing_session.session_number}?")
            return redirect('pos:terminal', terminal_id=existing_session.terminal.id)
        
        try:
            # Create new session
            session = CashierSession.objects.create(
                cashier=self.request.user,
                terminal=terminal,
                opening_cash=opening_cash,
                opening_notes=opening_notes
            )
            
            # Update terminal status
            terminal.current_cashier = self.request.user
            terminal.session_start = timezone.now()
            terminal.save()
            
            messages.success(self.request, f"Session {session.session_number} started successfully on {terminal.name}")
            return redirect('pos:terminal', terminal_id=terminal.id)
            
        except Exception as e:
            messages.error(self.request, f"Error starting session: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class CloseSessionView(LoginRequiredMixin, FormView):
    """Close cashier session"""
    template_name = 'pos/close_session.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = kwargs.get('session_id')
        session = get_object_or_404(CashierSession, id=session_id, cashier=self.request.user)
        
        # Calculate session summary
        sales_summary = Sale.objects.filter(session=session, status='completed').aggregate(
            total_sales=Sum('grand_total'),
            total_transactions=Count('id'),
            cash_sales=Sum('grand_total', filter=Q(payment_method='cash')),
            card_sales=Sum('grand_total', filter=Q(payment_method='card')),
            mpesa_sales=Sum('grand_total', filter=Q(payment_method='mpesa')),
        )
        
        context['session'] = session
        context['sales_summary'] = sales_summary
        return context
    
    def post(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        session = get_object_or_404(CashierSession, id=session_id, cashier=request.user)
        
        closing_cash = Decimal(request.POST.get('closing_cash', '0'))
        closing_notes = request.POST.get('closing_notes', '')
        
        # Close the session
        session.status = 'closed'
        session.end_time = timezone.now()
        session.closing_cash = closing_cash
        session.closing_notes = closing_notes
        session.save()
        
        # Update terminal status
        terminal = session.terminal
        terminal.current_cashier = None
        terminal.session_start = None
        terminal.save()
        
        messages.success(request, "Session closed successfully")
        return redirect('pos:main')


class NewSaleView(LoginRequiredMixin, TemplateView):
    """Create new sale interface"""
    template_name = 'pos/new_sale.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current session
        session = CashierSession.objects.filter(
            cashier=self.request.user,
            status='active'
        ).first()
        
        if not session:
            messages.warning(self.request, "No active session found.")
            return redirect('pos:main')
        
        context['session'] = session
        
        # Get available products
        context['products'] = Product.objects.filter(
            status='active',
            is_pos_enabled=True
        ).select_related('category')[:20]  # Limit for performance
        
        # Get recent customers
        context['recent_customers'] = Customer.objects.all()[:10]
        
        return context


class SaleListView(LoginRequiredMixin, ListView):
    """List sales"""
    model = Sale
    template_name = 'pos/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Sale.objects.select_related('cashier', 'customer', 'session').order_by('-transaction_time')
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(transaction_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_time__date__lte=end_date)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by payment method
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        return queryset


class SaleDetailView(LoginRequiredMixin, DetailView):
    """Sale detail view"""
    model = Sale
    template_name = 'pos/sale_detail.html'
    context_object_name = 'sale'
    pk_url_kwarg = 'sale_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sale = self.get_object()
        
        context['sale_items'] = sale.items.all().select_related('product')
        context['payments'] = sale.payments.all().order_by('processed_at')
        
        return context


class CustomerListView(LoginRequiredMixin, ListView):
    """List customers"""
    model = Customer
    template_name = 'pos/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 25
    
    def get_queryset(self):
        from django.db.models import Sum, Count, Max
        
        # Add POS sales statistics (excluding fields that already exist in the model)
        queryset = Customer.objects.annotate(
            total_purchases=Count('pos_purchases', distinct=True, filter=Q(pos_purchases__status='completed')),
        ).order_by('-created_at')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(company_name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add calculated fields to each customer
        for customer in context['customers']:
            # Use model fields for total_spent and loyalty_points
            if not hasattr(customer, 'total_spent') or customer.total_spent is None:
                customer.total_spent = 0
            
            # Get last purchase amount manually if needed
            if customer.last_purchase_date:
                try:
                    last_sale = customer.pos_purchases.filter(
                        transaction_time=customer.last_purchase_date,
                        status='completed'
                    ).first()
                    customer.last_purchase_amount = last_sale.grand_total if last_sale else 0
                except:
                    customer.last_purchase_amount = 0
            else:
                customer.last_purchase_amount = 0
        
        # Add overall statistics
        context.update({
            'total_customers': Customer.objects.count(),
            'active_customers': Customer.objects.filter(pos_purchases__status='completed').distinct().count(),
            'vip_customers': Customer.objects.filter(loyalty_points__gte=5000).count(),  # Gold and Platinum tiers
            'new_today': Customer.objects.filter(created_at__date=timezone.now().date()).count(),
        })
        
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    """Create customer"""
    model = Customer
    form_class = CustomerForm
    template_name = 'pos/customer_form.html'
    success_url = reverse_lazy('pos:customer_list')


class CustomerCreateAPIView(LoginRequiredMixin, View):
    """API endpoint for creating customers via AJAX for project clients"""
    
    def dispatch(self, request, *args, **kwargs):
        print(f"CustomerCreateAPIView called - Method: {request.method}")
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"Request path: {request.path}")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        return JsonResponse({'message': 'GET method not allowed', 'method': 'POST required'}, status=405)
    
    def post(self, request):
        print("POST method called in CustomerCreateAPIView")
        try:
            # Import the correct Customer model from quotations
            from apps.quotations.models import Customer as QuotationCustomer
            
            print(f"POST data: {dict(request.POST)}")
            print(f"Content type: {request.content_type}")
            
            # Extract data from request
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            company = request.POST.get('company', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            country = request.POST.get('country', 'Kenya').strip()
            business_type = request.POST.get('business_type', 'individual').strip()
            tax_number = request.POST.get('tax_number', '').strip()
            monthly_consumption = request.POST.get('monthly_consumption', '0')
            average_monthly_bill = request.POST.get('average_monthly_bill', '0')
            property_type = request.POST.get('property_type', 'residential').strip()
            roof_area = request.POST.get('roof_area', '0')
            roof_type = request.POST.get('roof_type', 'iron_sheets').strip()
            
            print(f"Extracted data - First: {first_name}, Last: {last_name}, Email: {email}, Phone: {phone}")
            
            # Validate required fields with specific messages
            missing_fields = []
            if not first_name:
                missing_fields.append('First name')
            if not last_name:
                missing_fields.append('Last name')  
            if not email:
                missing_fields.append('Email')
            if not phone:
                missing_fields.append('Phone')
                
            if missing_fields:
                return JsonResponse({
                    'success': False,
                    'message': f'The following fields are required: {", ".join(missing_fields)}',
                    'missing_fields': missing_fields
                }, status=400)
            
            # Check if customer with this email already exists
            if email and QuotationCustomer.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'A customer with this email already exists.'
                }, status=400)
            
            # Create full name and parse numeric fields
            full_name = f"{first_name} {last_name}".strip()
            
            # Convert numeric fields with fallbacks
            try:
                monthly_consumption = float(monthly_consumption) if monthly_consumption else 0
            except (ValueError, TypeError):
                monthly_consumption = 0
                
            try:
                average_monthly_bill = float(average_monthly_bill) if average_monthly_bill else 0
            except (ValueError, TypeError):
                average_monthly_bill = 0
                
            try:
                roof_area = float(roof_area) if roof_area else 0
            except (ValueError, TypeError):
                roof_area = 0
            
            # Create quotation customer (which is what projects expect)
            customer = QuotationCustomer.objects.create(
                name=full_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                country=country,
                company_name=company,
                business_type=business_type,
                tax_number=tax_number,
                monthly_consumption=monthly_consumption,
                average_monthly_bill=average_monthly_bill,
                property_type=property_type,
                roof_area=roof_area,
                roof_type=roof_type
            )
            
            # Display name for dropdown
            display_name = company if company else full_name
            if email:
                display_name += f" ({email})"
            
            return JsonResponse({
                'success': True,
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'display_name': display_name
            })
            
        except Exception as e:
            import traceback
            return JsonResponse({
                'success': False,
                'message': f'Error creating customer: {str(e)}',
                'debug': traceback.format_exc() if hasattr(request, 'user') and request.user.is_superuser else None
            }, status=500)


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """Customer detail view"""
    model = Customer
    template_name = 'pos/customer_detail.html'
    context_object_name = 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        
        # Get customer POS purchase history
        purchases = Sale.objects.filter(
            customer=customer,
            status='completed'
        ).order_by('-transaction_time')[:10]
        
        context['purchases'] = purchases
        
        # Calculate customer statistics from POS sales
        pos_stats = Sale.objects.filter(
            customer=customer,
            status='completed'
        ).aggregate(
            total_spent=Sum('grand_total'),
            total_purchases=Count('id'),
            last_purchase_date=Max('transaction_time')
        )
        
        # Add calculated stats to customer object
        customer.total_spent = pos_stats['total_spent'] or 0
        customer.total_purchases = pos_stats['total_purchases'] or 0
        customer.last_purchase_date = pos_stats['last_purchase_date']
        
        return context


class ReportsView(LoginRequiredMixin, TemplateView):
    """POS reports dashboard"""
    template_name = 'pos/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date range for reports
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Sales summary
        context['today_sales'] = Sale.objects.filter(
            transaction_time__date=today,
            status='completed'
        ).aggregate(
            total=Sum('grand_total'),
            count=Count('id')
        )
        
        context['week_sales'] = Sale.objects.filter(
            transaction_time__date__gte=week_ago,
            status='completed'
        ).aggregate(
            total=Sum('grand_total'),
            count=Count('id')
        )
        
        context['month_sales'] = Sale.objects.filter(
            transaction_time__date__gte=month_ago,
            status='completed'
        ).aggregate(
            total=Sum('grand_total'),
            count=Count('id')
        )
        
        return context


# API Views for AJAX functionality
class AddToCartAPIView(LoginRequiredMixin, View):
    """Add item to cart"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = Decimal(str(data.get('quantity', 1)))
            
            product = get_object_or_404(Product, id=product_id, status='active')
            
            # Get or create cart in session
            cart = request.session.get('pos_cart', [])
            
            # Check if product already in cart
            for item in cart:
                if item['product_id'] == product_id:
                    item['quantity'] = float(quantity)
                    break
            else:
                # Add new item to cart
                cart.append({
                    'product_id': product_id,
                    'name': product.name,
                    'price': float(product.price),
                    'quantity': float(quantity),
                    'line_total': float(product.price * quantity)
                })
            
            request.session['pos_cart'] = cart
            
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'message': f'{product.name} added to cart'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class RemoveFromCartAPIView(LoginRequiredMixin, View):
    """Remove item from cart"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            
            cart = request.session.get('pos_cart', [])
            cart = [item for item in cart if item['product_id'] != product_id]
            
            request.session['pos_cart'] = cart
            
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'message': 'Item removed from cart'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class ProductSearchView(LoginRequiredMixin, View):
    """Search products for POS"""
    
    def get(self, request):
        query = request.GET.get('q', '')
        
        if len(query) < 2:
            return JsonResponse({'products': []})
        
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(model_number__icontains=query),
            status='active'
        ).values('id', 'name', 'sku', 'selling_price', 'quantity_in_stock')[:20]
        
        # Rename selling_price to price for frontend compatibility
        products_list = []
        for product in products:
            product_dict = dict(product)
            product_dict['price'] = product_dict.pop('selling_price')
            products_list.append(product_dict)
        
        return JsonResponse({'products': products_list})


class ProcessPaymentAPIView(LoginRequiredMixin, View):
    """Process payment for sale"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Get current session
            session = CashierSession.objects.filter(
                cashier=request.user,
                status='active'
            ).first()
            
            if not session:
                return JsonResponse({
                    'success': False,
                    'error': 'No active session'
                }, status=400)
            
            # Get cart from payload or session
            cart = data.get('items', [])
            if not cart:
                # Fallback to session cart
                cart = request.session.get('pos_cart', [])
                if not cart:
                    return JsonResponse({
                        'success': False,
                        'error': 'Cart is empty'
                    }, status=400)
            
            # Calculate totals using VAT-inclusive approach (same as ecommerce)
            vat_inclusive_subtotal = Decimal('0')
            for item in cart:
                # Handle both payload and session cart structures
                if 'line_total' in item:
                    line_total = Decimal(str(item['line_total']))
                else:
                    # Calculate from quantity and price if line_total not available
                    quantity = Decimal(str(item.get('quantity', 1)))
                    price = Decimal(str(item.get('price', 0)))
                    line_total = quantity * price  # This is VAT-inclusive
                    item['line_total'] = float(line_total)  # Add for later use
                    
                vat_inclusive_subtotal += line_total
            
            # Calculate VAT backwards from inclusive prices (same as ecommerce)
            from apps.core.models import CompanySettings
            company_settings = CompanySettings.get_settings()
            vat_rate = Decimal(str(company_settings.vat_rate))
            vat_multiplier = Decimal('1') + (vat_rate / Decimal('100'))
            
            # Extract VAT amount and ex-VAT subtotal
            subtotal = vat_inclusive_subtotal / vat_multiplier  # Ex-VAT subtotal
            tax_amount = vat_inclusive_subtotal - subtotal      # VAT amount
            grand_total = vat_inclusive_subtotal                # Total is VAT-inclusive
            
            # Get payment details
            payment_method = data.get('payment_method', 'cash')
            amount_paid = Decimal(str(data.get('amount_paid', 0)))
            customer_id = data.get('customer')
            
            # Get customer if specified
            customer = None
            if customer_id:
                try:
                    customer = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    pass
            
            # Create sale
            sale = Sale.objects.create(
                session=session,
                cashier=request.user,
                customer=customer,
                subtotal=subtotal,
                tax_amount=tax_amount,
                grand_total=grand_total,
                payment_method=payment_method,
                amount_paid=amount_paid,
                change_amount=max(Decimal('0'), amount_paid - grand_total),
                status='pending'  # Will be updated based on payment processing
            )
            
            # Create sale items
            for item in cart:
                # Handle different field names for product ID
                product_id = item.get('product_id') or item.get('id') or item.get('product')
                product = Product.objects.get(id=product_id)
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    product_name=item.get('name', product.name),
                    product_sku=item.get('sku', product.sku),
                    quantity=Decimal(str(item['quantity'])),
                    unit_price=Decimal(str(item['price'])),
                    line_total=Decimal(str(item['line_total']))
                )
                
                # Update inventory if tracking is enabled
                if product.track_quantity:
                    product.quantity_in_stock -= Decimal(str(item['quantity']))
                    product.save()
            
            # Process payment based on method
            payment_result = self.process_payment(sale, payment_method, data)
            
            # Handle M-Pesa payments differently - don't complete sale immediately
            if payment_method == 'mpesa':
                if payment_result['success']:
                    # For M-Pesa, return the checkout request ID for polling
                    # Don't complete the sale yet - it will be completed via callback
                    sale.status = 'pending_payment'  # Keep sale pending until M-Pesa confirms
                    sale.save()
                    
                    # Clear cart since payment is initiated
                    request.session['pos_cart'] = []
                    
                    return JsonResponse({
                        'success': True,
                        'sale_id': sale.id,
                        'checkout_request_id': payment_result.get('checkout_request_id'),
                        'merchant_request_id': payment_result.get('merchant_request_id'),
                        'transaction_id': payment_result.get('transaction_id'),
                        'message': payment_result.get('message', 'STK Push sent to your phone'),
                        'total': float(grand_total)
                    })
                else:
                    # M-Pesa initiation failed
                    sale.status = 'cancelled'
                    sale.save()
                    
                    # Restore inventory
                    for item in cart:
                        product_id = item.get('product_id') or item.get('id') or item.get('product')
                        product = Product.objects.get(id=product_id)
                        if product.track_quantity:
                            product.quantity_in_stock += Decimal(str(item['quantity']))
                            product.save()
                    
                    return JsonResponse({
                        'success': False,
                        'error': payment_result.get('error', 'M-Pesa payment failed')
                    })
            
            # Handle other payment methods (cash, card, bank transfer) - complete immediately
            if payment_result['success']:
                sale.status = 'completed'
                sale.save()
                
                # Update customer stats and loyalty points if customer selected
                if customer:
                    # Use the model's method to update purchase stats and loyalty points
                    points_earned = customer.update_purchase_stats(grand_total, sale.transaction_time)
                    
                    # Add points earned info to the response
                    payment_result['points_earned'] = points_earned
                
                # Clear cart
                request.session['pos_cart'] = []
                
                # Create payment record
                Payment.objects.create(
                    sale=sale,
                    payment_type=payment_method,
                    amount=amount_paid,
                    status='completed',
                    transaction_id=payment_result.get('transaction_id', ''),
                    mpesa_receipt_number=payment_result.get('mpesa_receipt', ''),
                    mpesa_phone_number=data.get('mpesa_phone', ''),
                    reference_number=payment_result.get('reference_number', '')
                )
            else:
                sale.status = 'cancelled'
                sale.save()
                
                # Restore inventory
                for item in cart:
                    product_id = item.get('product_id') or item.get('id') or item.get('product')
                    product = Product.objects.get(id=product_id)
                    if product.track_quantity:
                        product.quantity_in_stock += Decimal(str(item['quantity']))
                        product.save()
            
            return JsonResponse({
                'success': payment_result['success'],
                'sale_id': sale.id,
                'receipt_number': sale.receipt_number,
                'total': float(grand_total),
                'message': payment_result.get('message', 'Payment processed'),
                'error': payment_result.get('error') if not payment_result['success'] else None
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def process_payment(self, sale, payment_method, data):
        """Process payment based on method"""
        try:
            if payment_method == 'cash':
                return self.process_cash_payment(sale, data)
            elif payment_method == 'mpesa':
                return self.process_mpesa_payment(sale, data)
            elif payment_method == 'card':
                return self.process_card_payment(sale, data)
            elif payment_method == 'bank_transfer':
                return self.process_bank_transfer_payment(sale, data)
            else:
                return {'success': False, 'error': 'Invalid payment method'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_cash_payment(self, sale, data):
        """Process cash payment"""
        amount_paid = Decimal(str(data.get('amount_paid', 0)))
        
        if amount_paid < sale.grand_total:
            return {'success': False, 'error': 'Insufficient payment amount'}
        
        return {
            'success': True,
            'reference_number': f'CASH-{sale.sale_number}',
            'message': 'Cash payment processed successfully'
        }
    
    def process_mpesa_payment(self, sale, data):
        """Process M-Pesa payment using STK Push - matches ecommerce checkout process"""
        from apps.ecommerce.mpesa import MPesaSTKPush
        from apps.ecommerce.models import MPesaTransaction
        
        try:
            phone_number = data.get('mpesa_phone', '')
            if not phone_number:
                print("ERROR: M-Pesa phone number not provided")
                return {'success': False, 'error': 'M-Pesa phone number required'}
            
            print(f"Processing M-Pesa payment for phone: {phone_number}, amount: {sale.grand_total}")
            
            # Create M-Pesa transaction record for POS (same as ecommerce)
            mpesa_transaction = MPesaTransaction.objects.create(
                pos_sale=sale,  # Link to POS sale instead of order
                phone_number=phone_number,
                amount=sale.grand_total,
                account_reference=f"POS-{sale.id}",
                transaction_desc=f"POS Payment for Sale {sale.id}",
                status='initiated'
            )
            
            print(f"Created M-Pesa transaction record: {mpesa_transaction.id}")
            
            # Initialize STK Push (same as ecommerce)
            mpesa = MPesaSTKPush()
            result = mpesa.initiate_stk_push(
                phone_number=phone_number,
                amount=sale.grand_total,
                account_reference=f"POS-{sale.id}",
                transaction_desc=f"POS Payment for Sale {sale.id}"
            )
            
            print(f"STK Push result: {result}")
            
            # Store initiation response (same as ecommerce)
            mpesa_transaction.initiation_response = result
            
            if result.get('success'):
                # Use consistent field names from ecommerce
                mpesa_transaction.checkout_request_id = result.get('checkout_request_id')
                mpesa_transaction.merchant_request_id = result.get('merchant_request_id')
                mpesa_transaction.status = 'pending'
                mpesa_transaction.save()
                
                print(f"SUCCESS: M-Pesa transaction updated with checkout_request_id: {result.get('checkout_request_id')}")
                
                return {
                    'success': True,
                    'message': result.get('customer_message', 'STK Push sent to your phone'),
                    'checkout_request_id': result.get('checkout_request_id'),
                    'merchant_request_id': result.get('merchant_request_id'),
                    'transaction_id': mpesa_transaction.id,
                    'response': result
                }
            else:
                # Handle failure (same as ecommerce)
                error_message = result.get('message', 'STK Push failed')
                print(f"ERROR: STK Push failed: {error_message}")
                mpesa_transaction.status = 'failed'
                mpesa_transaction.error_message = error_message
                mpesa_transaction.save()
                
                return {
                    'success': False,
                    'error': error_message,
                    'response': result
                }
                
        except Exception as e:
            print(f"EXCEPTION in process_mpesa_payment: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {'success': False, 'error': f'M-Pesa payment error: {str(e)}'}
    
    def process_card_payment(self, sale, data):
        """Process card payment"""
        try:
            # TODO: Implement actual card payment gateway integration
            # For now, simulate processing
            import random
            import time
            
            time.sleep(1)
            
            if random.random() < 0.90:
                reference = f"CARD-{random.randint(100000, 999999)}"
                return {
                    'success': True,
                    'transaction_id': reference,
                    'card_reference': reference,
                    'message': 'Card payment successful'
                }
            else:
                return {'success': False, 'error': 'Card payment declined'}
                
        except Exception as e:
            return {'success': False, 'error': f'Card payment error: {str(e)}'}
    
    def process_bank_transfer_payment(self, sale, data):
        """Process bank transfer payment"""
        try:
            # Bank transfer payments are typically processed offline
            # Mark as pending and require manual confirmation
            reference = f"BT-{sale.sale_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            return {
                'success': True,
                'transaction_id': reference,
                'reference_number': reference,
                'message': 'Bank transfer recorded. Payment pending confirmation.'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Bank transfer error: {str(e)}'}


# Placeholder views for remaining functionality
class SessionListView(LoginRequiredMixin, ListView):
    model = CashierSession
    template_name = 'pos/session_list.html'
    paginate_by = 25


class SessionDetailView(LoginRequiredMixin, DetailView):
    model = CashierSession
    template_name = 'pos/session_detail.html'


class SuspendSessionView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        # Implementation for suspending session
        pass


class ProcessPaymentView(LoginRequiredMixin, View):
    def post(self, request, sale_id):
        # Implementation for processing payment
        pass


class PrintReceiptView(LoginRequiredMixin, View):
    def get(self, request, sale_id):
        """Generate and return receipt for a sale"""
        try:
            sale = get_object_or_404(Sale, id=sale_id)
            
            # Check if user has permission to view this sale
            if not request.user.is_superuser and sale.cashier != request.user:
                messages.error(request, "You don't have permission to view this receipt.")
                return redirect('pos:sale_list')
            
            context = {
                'sale': sale,
                'sale_items': sale.items.all(),
                'payments': sale.payments.all(),
                'company_settings': CompanySettings.get_settings() if hasattr(request, 'company_settings') else None,
            }
            
            return render(request, 'pos/receipt.html', context)
            
        except Sale.DoesNotExist:
            messages.error(request, "Sale not found.")
            return redirect('pos:sale_list')
        except Exception as e:
            messages.error(request, f"Error generating receipt: {str(e)}")
            return redirect('pos:sale_list')


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'pos/customer_form.html'
    
    def post(self, request, *args, **kwargs):
        """Handle AJAX updates"""
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                customer = self.get_object()
                
                # Update customer fields
                customer.name = request.POST.get('name', customer.name)
                customer.email = request.POST.get('email', customer.email)
                customer.phone = request.POST.get('phone', customer.phone)
                customer.city = request.POST.get('city', customer.city)
                customer.address = request.POST.get('address', customer.address)
                customer.company_name = request.POST.get('company_name', customer.company_name)
                customer.business_type = request.POST.get('business_type', customer.business_type)
                
                customer.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Customer updated successfully'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=400)
        
        return super().post(request, *args, **kwargs)


class ProductDetailsView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'pos/product_details.html'
    pk_url_kwarg = 'product_id'


class InventoryCheckView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/inventory_check.html'


class CashMovementListView(LoginRequiredMixin, ListView):
    model = CashMovement
    template_name = 'pos/cash_movement_list.html'


class CashMovementCreateView(LoginRequiredMixin, CreateView):
    model = CashMovement
    form_class = CashMovementForm
    template_name = 'pos/cash_movement_form.html'


class CashDropView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/cash_drop.html'


class CashPayoutView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/cash_payout.html'


class DiscountListView(LoginRequiredMixin, ListView):
    model = Discount
    template_name = 'pos/discount_list.html'


class ApplyDiscountView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/apply_discount.html'


class DailySalesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/daily_sales_report.html'


class CashierPerformanceReportView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/cashier_performance.html'


class ProductSalesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/product_sales.html'


class POSSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/settings.html'


class TerminalManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/terminal_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get user's store
        user = self.request.user
        
        # Get store that user manages or works at
        store = Store.objects.filter(
            Q(manager=user) | Q(terminals__current_cashier=user)
        ).distinct().first()
        
        if store:
            context['store'] = store
            context['terminals'] = Terminal.objects.filter(store=store).order_by('name')
        else:
            context['terminals'] = Terminal.objects.none()
            
        return context


class StoreManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'pos/store_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get stores the user manages or has access to
        context['stores'] = Store.objects.filter(
            Q(manager=user) | Q(terminals__current_cashier=user)
        ).distinct().order_by('name')
        
        return context


class AddStoreView(LoginRequiredMixin, CreateView):
    """Add new store"""
    model = Store
    fields = ['name', 'code', 'address_line_1', 'address_line_2', 'city', 'county', 
              'postal_code', 'phone', 'email', 'timezone', 'currency', 'opening_time', 'closing_time']
    template_name = 'pos/add_store.html'
    success_url = reverse_lazy('pos:store_management')
    
    def form_valid(self, form):
        # Set current user as manager
        form.instance.manager = self.request.user
        messages.success(self.request, f"Store '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class EditStoreView(LoginRequiredMixin, UpdateView):
    """Edit store"""
    model = Store
    fields = ['name', 'code', 'address_line_1', 'address_line_2', 'city', 'county', 
              'postal_code', 'phone', 'email', 'manager', 'is_active', 'timezone', 
              'currency', 'opening_time', 'closing_time']
    template_name = 'pos/edit_store.html'
    success_url = reverse_lazy('pos:store_management')
    
    def get_queryset(self):
        # Only allow editing stores the user manages
        return Store.objects.filter(manager=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f"Store '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class DeleteStoreView(LoginRequiredMixin, DeleteView):
    """Delete store"""
    model = Store
    template_name = 'pos/delete_store.html'
    success_url = reverse_lazy('pos:store_management')
    
    def get_queryset(self):
        # Only allow deleting stores the user manages
        return Store.objects.filter(manager=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        store = self.get_object()
        if store.terminals.exists():
            messages.error(request, f"Cannot delete store '{store.name}' - it has terminals. Remove terminals first.")
            return redirect('pos:store_management')
        
        messages.success(request, f"Store '{store.name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


class AddTerminalView(LoginRequiredMixin, CreateView):
    """Add new terminal"""
    model = Terminal
    fields = ['name', 'code', 'device_id', 'ip_address', 'mac_address', 
              'cash_drawer_enabled', 'receipt_printer_enabled', 'barcode_scanner_enabled']
    template_name = 'pos/add_terminal.html'
    success_url = reverse_lazy('pos:terminal_management')
    
    def form_valid(self, form):
        # Get user's store
        user = self.request.user
        store = Store.objects.filter(
            Q(manager=user) | Q(terminals__current_cashier=user)
        ).distinct().first()
        
        if not store:
            messages.error(self.request, "You don't have permission to add terminals.")
            return redirect('pos:terminal_management')
            
        form.instance.store = store
        messages.success(self.request, f"Terminal '{form.instance.name}' added successfully.")
        return super().form_valid(form)


class EditTerminalView(LoginRequiredMixin, UpdateView):
    """Edit terminal"""
    model = Terminal
    fields = ['name', 'code', 'device_id', 'ip_address', 'mac_address', 
              'is_active', 'cash_drawer_enabled', 'receipt_printer_enabled', 
              'barcode_scanner_enabled', 'requires_manager_approval']
    template_name = 'pos/edit_terminal.html'
    success_url = reverse_lazy('pos:terminal_management')
    
    def get_queryset(self):
        # Only allow editing terminals from user's store
        user = self.request.user
        return Terminal.objects.filter(
            store__in=Store.objects.filter(
                Q(manager=user) | Q(terminals__current_cashier=user)
            )
        )
    
    def form_valid(self, form):
        messages.success(self.request, f"Terminal '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class DeleteTerminalView(LoginRequiredMixin, DeleteView):
    """Delete terminal"""
    model = Terminal
    template_name = 'pos/delete_terminal.html'
    success_url = reverse_lazy('pos:terminal_management')
    
    def get_queryset(self):
        # Only allow deleting terminals from user's store
        user = self.request.user
        return Terminal.objects.filter(
            store__in=Store.objects.filter(
                Q(manager=user) | Q(terminals__current_cashier=user)
            )
        )
    
    def delete(self, request, *args, **kwargs):
        terminal = self.get_object()
        if terminal.current_cashier:
            messages.error(request, f"Cannot delete terminal '{terminal.name}' - it has an active session.")
            return redirect('pos:terminal_management')
        
        messages.success(request, f"Terminal '{terminal.name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


class UpdateCartQuantityAPIView(LoginRequiredMixin, View):
    def post(self, request):
        # Implementation for updating cart quantity
        pass


class ApplyDiscountAPIView(LoginRequiredMixin, View):
    def post(self, request):
        # Implementation for applying discount
        pass


class CustomerSearchAPIView(LoginRequiredMixin, View):
    def get(self, request):
        # Implementation for customer search
        pass


class ProductBarcodeAPIView(LoginRequiredMixin, View):
    def get(self, request):
        # Implementation for barcode lookup
        pass


class PrintReceiptAPIView(LoginRequiredMixin, View):
    def post(self, request):
        # Implementation for receipt printing
        pass


class SyncSalesAPIView(LoginRequiredMixin, View):
    def post(self, request):
        # Implementation for offline sales sync
        pass


class SyncInventoryAPIView(LoginRequiredMixin, View):
    def get(self, request):
        # Implementation for inventory sync
        pass


class GetActiveTerminalAPIView(LoginRequiredMixin, View):
    """Get the active terminal for the current user"""
    
    def get(self, request):
        try:
            # Get active session for current user
            session = CashierSession.objects.filter(
                cashier=request.user,
                status='active'
            ).first()
            
            if session:
                return JsonResponse({
                    'success': True,
                    'terminal_id': session.terminal.id,
                    'terminal_name': session.terminal.name,
                    'session_id': session.id,
                    'session_number': session.session_number
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No active session found'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class POSMPesaStatusAPIView(LoginRequiredMixin, View):
    """Check M-Pesa payment status for POS transactions"""
    
    def get(self, request):
        """Handle GET requests with checkout_request_id as query parameter"""
        try:
            checkout_request_id = request.GET.get('checkout_request_id')
            
            if not checkout_request_id:
                return JsonResponse({
                    'status': 'failed',
                    'error': 'Checkout request ID is required'
                }, status=400)
            
            # Find the M-Pesa transaction
            try:
                mpesa_transaction = MPesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )
                
                # Return current status
                if mpesa_transaction.status == 'completed':
                    return JsonResponse({
                        'status': 'completed',
                        'mpesa_receipt_number': mpesa_transaction.mpesa_receipt_number,
                        'transaction_date': mpesa_transaction.transaction_date.isoformat() if mpesa_transaction.transaction_date else None,
                        'amount': float(mpesa_transaction.amount)
                    })
                elif mpesa_transaction.status == 'failed':
                    return JsonResponse({
                        'status': 'failed',
                        'error': mpesa_transaction.error_message or 'Payment failed'
                    })
                else:
                    # Still pending
                    return JsonResponse({
                        'status': 'pending',
                        'message': 'Payment is still being processed'
                    })
                    
            except MPesaTransaction.DoesNotExist:
                return JsonResponse({
                    'status': 'failed',
                    'error': 'Transaction not found'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': str(e)
            }, status=400)
    
    def post(self, request):
        """Handle POST requests with checkout_request_id in request body"""
        try:
            data = json.loads(request.body)
            checkout_request_id = data.get('checkout_request_id')
            
            if not checkout_request_id:
                return JsonResponse({
                    'status': 'failed',
                    'error': 'Checkout request ID is required'
                }, status=400)
            
            # Find the M-Pesa transaction
            try:
                mpesa_transaction = MPesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )
                
                # Return current status
                if mpesa_transaction.status == 'completed':
                    return JsonResponse({
                        'status': 'completed',
                        'mpesa_receipt_number': mpesa_transaction.mpesa_receipt_number,
                        'transaction_date': mpesa_transaction.transaction_date.isoformat() if mpesa_transaction.transaction_date else None,
                        'amount': float(mpesa_transaction.amount)
                    })
                elif mpesa_transaction.status == 'failed':
                    return JsonResponse({
                        'status': 'failed',
                        'error': mpesa_transaction.error_message or 'Payment failed'
                    })
                else:
                    # Still pending
                    return JsonResponse({
                        'status': 'pending',
                        'message': 'Payment is still being processed'
                    })
                    
            except MPesaTransaction.DoesNotExist:
                return JsonResponse({
                    'status': 'failed',
                    'error': 'Transaction not found'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': str(e)
            }, status=400)


class POSMPesaCallbackView(View):
    """Handle M-Pesa payment callbacks for POS transactions"""

    def post(self, request):
        import json

        # Validate callback authenticity
        if not self._validate_callback_source(request):
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Unauthorized access'}, status=403)

        try:
            callback_data = json.loads(request.body)

            # Parse callback using same logic as ecommerce
            transaction_data = MPesaCallback.parse_callback_data(callback_data)

            if transaction_data.get('success'):
                # Find the transaction by checkout_request_id
                checkout_request_id = transaction_data.get('checkout_request_id')
                try:
                    mpesa_transaction = MPesaTransaction.objects.get(
                        checkout_request_id=checkout_request_id
                    )

                    # Process callback based on result code
                    result_code = transaction_data.get('result_code')
                    result_description = transaction_data.get('result_description', 'Unknown result')

                    if result_code == 0:
                        # Successful payment
                        mpesa_transaction.mark_completed(
                            receipt_number=transaction_data.get('mpesa_receipt_number'),
                            transaction_date=timezone.now()
                        )

                        # Handle both ecommerce orders and POS sales
                        if mpesa_transaction.pos_sale:
                            # Handle POS sale
                            sale = mpesa_transaction.pos_sale

                            # Create or update payment record for POS
                            payment, created = Payment.objects.get_or_create(
                                sale=sale,
                                payment_type='mpesa',
                                defaults={
                                    'amount': mpesa_transaction.amount,
                                    'transaction_id': mpesa_transaction.mpesa_receipt_number,
                                    'mpesa_receipt_number': mpesa_transaction.mpesa_receipt_number,
                                    'mpesa_phone_number': mpesa_transaction.phone_number,
                                    'status': 'completed'
                                }
                            )

                            if not created:
                                payment.status = 'completed'
                                payment.transaction_id = mpesa_transaction.mpesa_receipt_number
                                payment.mpesa_receipt_number = mpesa_transaction.mpesa_receipt_number
                                payment.save()

                            # Update sale status to completed
                            sale.status = 'completed'
                            sale.mpesa_transaction_id = mpesa_transaction.mpesa_receipt_number
                            sale.save()

                            # Update customer loyalty points if customer exists
                            if hasattr(sale.customer, 'update_purchase_stats'):
                                sale.customer.update_purchase_stats(sale.grand_total, sale.transaction_time)

                        elif mpesa_transaction.order:
                            # Handle ecommerce order
                            order = mpesa_transaction.order

                            # Create or update payment record for ecommerce
                            from apps.ecommerce.models import Payment as EcommercePayment
                            payment, created = EcommercePayment.objects.get_or_create(
                                order=order,
                                payment_method='mpesa',
                                defaults={
                                    'amount': mpesa_transaction.amount,
                                    'reference_number': mpesa_transaction.mpesa_receipt_number,
                                    'mpesa_receipt_number': mpesa_transaction.mpesa_receipt_number,
                                    'mpesa_phone_number': mpesa_transaction.phone_number,
                                    'transaction_date': mpesa_transaction.transaction_date,
                                    'status': 'completed'
                                }
                            )

                            if not created:
                                payment.status = 'completed'
                                payment.mpesa_receipt_number = mpesa_transaction.mpesa_receipt_number
                                payment.transaction_date = mpesa_transaction.transaction_date
                                payment.save()

                            # Update order status
                            order.payment_status = 'paid'
                            order.status = 'paid'
                            order.mpesa_transaction_id = mpesa_transaction.mpesa_receipt_number
                            order.save()

                        print(f"M-Pesa payment completed: {transaction_data.get('mpesa_receipt_number')}")

                    else:
                        # Failed/Cancelled payment - handle different error codes
                        error_message = f"Payment failed ({result_code}): {result_description}"

                        # Specific handling for common failure/cancellation codes
                        if result_code in [1, 17, 26]:  # User cancelled, transaction cancelled, or insufficient balance
                            error_message = "Payment was cancelled by user or failed"
                        elif result_code in [2, 3, 4]:  # Wrong PIN, transaction declined, or wrong expiry date
                            error_message = f"Payment declined: {result_description}"
                        elif result_code == 1032:  # Timeout
                            error_message = "Payment timed out"
                        elif result_code in [2001, 2018]:  # Insufficient balance or system busy
                            error_message = f"Payment failed: {result_description}"
                        else:
                            error_message = f"Payment failed: {result_description}"

                        mpesa_transaction.mark_failed(error_message)
                        mpesa_transaction.save()

                        # Update related order/sale status for cancelled transactions
                        if mpesa_transaction.pos_sale:
                            sale = mpesa_transaction.pos_sale
                            if result_code in [17, 1, 26]:  # User cancelled or transaction cancelled
                                sale.status = 'cancelled'
                                sale.status_notes = f"M-Pesa payment cancelled: {error_message}"
                            else:
                                sale.status = 'failed'  # Keep pending for retryable failures
                                sale.status_notes = f"M-Pesa payment failed: {error_message}"
                            sale.save()

                        elif mpesa_transaction.order:
                            order = mpesa_transaction.order
                            if result_code in [17, 1, 26]:  # User cancelled or transaction cancelled
                                order.status = 'cancelled'
                                order.status_notes = f"M-Pesa payment cancelled: {error_message}"
                            else:
                                order.status = 'failed'  # Keep pending for retryable failures
                                order.status_notes = f"M-Pesa payment failed: {error_message}"
                            order.save()

                        print(f"M-Pesa payment failed (Result Code: {result_code}): {error_message}")

                except MPesaTransaction.DoesNotExist:
                    # Log unknown transaction for security monitoring
                    print(f"Warning: Unknown transaction callback received for CheckoutRequestID {checkout_request_id}")

            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})

        except Exception as e:
            print(f"M-Pesa callback error: {str(e)}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': f'Error: {str(e)}'}, status=400)

    def _validate_callback_source(self, request):
        """Validate callback source for security"""
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0]
        else:
            client_ip = request.META.get('REMOTE_ADDR')

        # In production, validate that callback comes from Safaricom IPs
        # For now, just log the source for monitoring
        print(f"M-Pesa callback received from IP: {client_ip}")

        # TODO: Add IP whitelist validation for Safaricom accounts
        # Safaricom typically uses these IP ranges:
        # 196.201.214.0/24, 197.156.0.0/14, etc.
        # For now, accept all (but log for monitoring)
        return True
