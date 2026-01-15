from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.db import models
from .models import ShoppingCart, Order, CartItem, Payment, Receipt, MPesaTransaction, OrderStatusHistory
from apps.products.models import Product
from apps.quotations.models import Customer
from apps.core.models import CompanySettings
from .mpesa import MPesaSTKPush, MPesaCallback
import json
from decimal import Decimal

class CartView(LoginRequiredMixin, TemplateView):
    template_name = 'ecommerce/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add discount information for cart template
        from apps.core.context_processors import active_discounts
        discount_context = active_discounts(self.request)
        context.update(discount_context)
        cart, created = ShoppingCart.objects.get_or_create(user=self.request.user)
        context['cart'] = cart
        return context

class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        # Add logging for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"AddToCartView called for product_id: {product_id}, user: {request.user}")

        try:
            product = get_object_or_404(Product, id=product_id)
            logger.info(f"Product found: {product.name} (ID: {product.id})")
            cart, created = ShoppingCart.objects.get_or_create(user=request.user)

            # Handle both JSON and form data
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                    quantity = int(data.get('quantity', 1))
                except (json.JSONDecodeError, ValueError):
                    quantity = 1
            else:
                quantity = int(request.POST.get('quantity', 1))

            # Validate quantity
            if quantity <= 0:
                quantity = 1

            # Optimized: Add item to cart (stock checking handled in add_item method)
            cart_item = cart.add_item(product, quantity, check_stock=True)

            # Show success message and return response - skip Django messages to reduce session writes
            success_message = f'{product.name} added to cart'

            # Always return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'cart_count': cart.total_items,
                    'message': success_message
                })

            # For non-AJAX requests, add django message and redirect
            messages.success(request, success_message)
            return redirect('products:detail', slug=product.slug)

        except ValueError as ve:
            # Handle stock validation errors specifically
            error_message = str(ve)
            if 'Insufficient stock' in error_message:
                return JsonResponse({
                    'success': False,
                    'message': error_message,
                    'available_stock': product.quantity_in_stock
                }, status=400)

            return JsonResponse({
                'success': False,
                'message': error_message
            }, status=400)

        except Exception as e:
            # Return JSON error for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred while adding the item to your cart. Please try again.'
                }, status=500)

            messages.error(request, f'Error adding product to cart: {str(e)}')
            return redirect('products:detail', slug=product.slug)

class CartCountView(LoginRequiredMixin, View):
    def get(self, request):
        cart = ShoppingCart.objects.filter(user=request.user).first()
        count = cart.total_items if cart else 0
        return JsonResponse({'count': count})

class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'ecommerce/checkout.html'

    def dispatch(self, request, *args, **kwargs):
        # Ensure user is authenticated
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        # Check if cart has items before rendering checkout
        cart, created = ShoppingCart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty. Please add items before checkout.')
            return redirect('ecommerce:cart')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add discount information for checkout template
        from apps.core.context_processors import active_discounts
        discount_context = active_discounts(self.request)
        context.update(discount_context)

        if self.request.user.is_authenticated:
            cart, created = ShoppingCart.objects.get_or_create(user=self.request.user)
            context['cart'] = cart

            # Calculate discounted cart values for JavaScript
            discount_percentage = discount_context.get('discount_percentage', 0)
            if discount_percentage and discount_percentage > 0:
                from decimal import Decimal
                context['discounted_cart_subtotal'] = cart.total_with_vat * (1 - discount_percentage / 100)
                context['discounted_cart_subtotal_ex_vat'] = cart.subtotal_ex_vat * (1 - discount_percentage / 100)
                context['discounted_cart_vat'] = (cart.subtotal_ex_vat * (1 - discount_percentage / 100)) * Decimal('0.16')
        return context

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    context_object_name = 'orders'
    paginate_by = 20

    def get_template_names(self):
        if self.request.user.role == 'customer':
            return ['ecommerce/orders_customer.html']
        return ['ecommerce/orders_management.html']

    def get_queryset(self):
        if self.request.user.role == 'customer':
            return Order.objects.filter(user=self.request.user)
        return Order.objects.all()

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_template_names(self):
        if not hasattr(self.request.user, 'role') or self.request.user.role not in ['super_admin', 'manager', 'director', 'sales_manager', 'cashier']:
            return ['ecommerce/order_detail.html']
        return ['ecommerce/order_detail_management.html']

class UpdateCartItemView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        try:
            cart = get_object_or_404(ShoppingCart, user=request.user)
            cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))

            if quantity <= 0:
                cart_item.delete()
                action = 'removed'
                new_quantity = 0
                item_total = 0
            else:
                cart_item.quantity = quantity
                cart_item.save()
                action = 'updated'
                new_quantity = cart_item.quantity
                item_total = float(cart_item.total_price)

            return JsonResponse({
                'success': True,
                'action': action,
                'new_quantity': new_quantity,
                'item_total': item_total,
                'cart_total': cart.total_items,
                'cart_count': cart.total_items,
                'cart_subtotal': float(cart.subtotal_ex_vat),
                'cart_total_with_vat': float(cart.total_with_vat)
            })

        except ValueError as e:
            # Handle stock validation errors from CartItem.save()
            error_message = str(e)
            if 'Insufficient stock' in error_message:
                return JsonResponse({
                    'success': False,
                    'message': f'Sorry, we only have {cart_item.product.quantity_in_stock} units of {cart_item.product.name} in stock. Please reduce your quantity.',
                    'available_stock': cart_item.product.quantity_in_stock
                }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while updating your cart. Please try again.'
            }, status=500)

class RemoveFromCartView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        cart = get_object_or_404(ShoppingCart, user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()

        return JsonResponse({
            'success': True,
            'cart_total': cart.total_items,
            'cart_subtotal': float(cart.subtotal_ex_vat),
            'cart_total_with_vat': float(cart.total_with_vat)
        })

class ClearCartView(LoginRequiredMixin, View):
    def post(self, request):
        cart = get_object_or_404(ShoppingCart, user=request.user)
        cart.clear()

        return JsonResponse({'success': True})

@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request):
        try:
            data = json.loads(request.body)

            # Get or create customer
            customer_data = data.get('customer', {})
            full_name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}".strip()

            customer, created = Customer.objects.get_or_create(
                email=customer_data.get('email'),
                defaults={
                    'name': full_name or customer_data.get('email', ''),
                    'phone': customer_data.get('phone', ''),
                    'email': customer_data.get('email', ''),
                    'address': data.get('billing_address', ''),
                    'city': customer_data.get('city', ''),
                    'postal_code': customer_data.get('postal_code', ''),
                }
            )

            # Update customer with latest information if it already existed
            if not created and full_name:
                customer.name = full_name
                customer.phone = customer_data.get('phone', '') or customer.phone
                customer.address = data.get('billing_address', '') or customer.address
                customer.save()

            # Get cart
            cart = get_object_or_404(ShoppingCart, user=request.user)
            if not cart.items.exists():
                return JsonResponse({'success': False, 'message': 'Cart is empty'})

            # Calculate totals
            from apps.core.models import CompanySettings
            company_settings = CompanySettings.get_settings()

            # Check for active holiday discounts
            from apps.core.context_processors import active_discounts
            discount_context = active_discounts(request)
            discount_percentage = discount_context.get('discount_percentage', 0) if discount_context.get('discount_percentage') else 0

            # Calculate cart totals with discounts applied
            vat_inclusive_subtotal = sum(
                (item.unit_price * item.quantity) * (1 - discount_percentage / 100) if discount_percentage and discount_percentage > 0
                else item.unit_price * item.quantity
                for item in cart.items.all()
            )

            vat_rate = Decimal(str(company_settings.vat_rate))
            vat_multiplier = Decimal('1') + (vat_rate / Decimal('100'))
            subtotal_ex_vat = vat_inclusive_subtotal / vat_multiplier
            vat_from_products = vat_inclusive_subtotal - subtotal_ex_vat

            # Installation fee: 10% of subtotal (ex VAT), max 25,000
            if data.get('installation_required', False):
                installation_cost = min(subtotal_ex_vat * Decimal('0.10'), Decimal('25000'))
                installation_vat = installation_cost * (vat_rate / Decimal('100'))
            else:
                installation_cost = Decimal('0')
                installation_vat = Decimal('0')

            tax_amount = vat_from_products + installation_vat
            shipping_cost = Decimal('0')  # Free shipping
            total_amount = vat_inclusive_subtotal + installation_cost + installation_vat + shipping_cost

            # Create order
            order = Order.objects.create(
                customer=customer,
                user=request.user,
                order_type='online',
                subtotal=subtotal_ex_vat,
                discount_percentage=discount_percentage if discount_percentage > 0 else 0,
                discount_amount=vat_inclusive_subtotal - (vat_inclusive_subtotal / (1 + discount_percentage / 100)) if discount_percentage > 0 else 0,
                tax_amount=tax_amount,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                billing_address=data.get('delivery', {}).get('address', ''),
                shipping_address=data.get('delivery', {}).get('address', ''),
                payment_method=data.get('payment_method', 'mpesa'),
                delivery_notes=data.get('notes', ''),
                status='pending'
            )

            # Create order items with discount applied
            for cart_item in cart.items.all():
                original_unit_price = cart_item.unit_price
                # Apply holiday discount if available
                if discount_percentage and discount_percentage > 0:
                    discounted_unit_price = original_unit_price * (1 - discount_percentage / 100)
                else:
                    discounted_unit_price = original_unit_price

                order.items.create(
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.product.sku or '',
                    quantity=cart_item.quantity,
                    unit_price=discounted_unit_price,
                    total_price=discounted_unit_price * cart_item.quantity
                )

            # Clear cart
            cart.clear()

            return JsonResponse({
                'success': True,
                'order_number': order.order_number,
                'message': 'Order created successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

class ProcessPaymentView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, order_number):
        try:
            order = get_object_or_404(Order, order_number=order_number, user=request.user)
            data = json.loads(request.body)

            payment_method = data.get('payment_method')

            # Create payment record
            payment = Payment.objects.create(
                order=order,
                amount=order.total_amount,
                payment_method=payment_method,
                reference_number=f"PAY-{order.order_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            )

            if payment_method == 'mpesa':
                # Process M-Pesa payment (don't mark as completed until callback)
                result = self.process_mpesa_payment(order, payment, data)

                if result['success']:
                    # STK push initiated successfully - keep order pending until M-Pesa callback
                    payment.gateway_response = result.get('response', {})
                    payment.mpesa_phone_number = data.get('phone_number', '')
                    payment.status = 'pending'  # Changed from 'completed' to 'pending'
                    payment.save()

                    # Order stays pending - will be marked paid by callback
                    order.payment_status = 'pending'  # Changed from 'paid' to 'pending'

                    # Set order status to pending_payment if it exists
                    if hasattr(order, 'status'):
                        order.status = 'pending_payment'

                    order.save()

                else:
                    payment.status = 'failed'
                    payment.gateway_response = result.get('response', {})
                    payment.save()

                return JsonResponse(result)

            elif payment_method == 'bank_transfer':
                # Bank transfer - mark as awaiting payment
                order.payment_status = 'pending'
                order.status = 'pending'
                order.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Order created. Please make bank transfer and notify us.',
                    'order_number': order.order_number
                })

            elif payment_method == 'cash':
                # Cash on delivery
                order.payment_status = 'pending'
                order.status = 'processing'
                order.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Order created for cash on delivery.',
                    'order_number': order.order_number
                })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    def process_mpesa_payment(self, order, payment, data):
        """Process M-Pesa payment using STK Push"""
        try:
            phone_number = data.get('phone_number', '')
            if not phone_number:
                return {
                    'success': False,
                    'message': 'Phone number is required for M-Pesa payment'
                }

            # Create M-Pesa transaction record
            mpesa_transaction = MPesaTransaction.objects.create(
                order=order,
                phone_number=phone_number,
                amount=order.total_amount,
                account_reference=order.order_number,
                transaction_desc=f"Payment for Order {order.order_number}",
                status='initiated'
            )

            # Initialize STK Push
            mpesa = MPesaSTKPush()
            result = mpesa.initiate_stk_push(
                phone_number=phone_number,
                amount=order.total_amount,
                account_reference=order.order_number,
                transaction_desc=f"Payment for Order {order.order_number}"
            )

            # Store initiation response
            mpesa_transaction.initiation_response = result

            if result.get('success'):
                mpesa_transaction.checkout_request_id = result.get('checkout_request_id')
                mpesa_transaction.merchant_request_id = result.get('merchant_request_id')
                mpesa_transaction.status = 'pending'
                mpesa_transaction.save()

                return {
                    'success': True,
                    'message': result.get('customer_message', 'STK Push sent to your phone'),
                    'checkout_request_id': result.get('checkout_request_id'),
                    'transaction_id': mpesa_transaction.id,
                    'response': result
                }
            else:
                mpesa_transaction.status = 'failed'
                mpesa_transaction.error_message = result.get('message', 'STK Push failed')
                mpesa_transaction.save()

                return {
                    'success': False,
                    'message': result.get('message', 'Failed to initiate M-Pesa payment'),
                    'response': result
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Payment processing error: {str(e)}'
            }

class MPesaCallbackView(View):
    """Handle M-Pesa STK Push callback"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            # Parse callback data
            callback_data = json.loads(request.body.decode('utf-8'))

            # Parse the callback using our helper
            transaction_data = MPesaCallback.parse_callback_data(callback_data)

            if not transaction_data.get('success'):
                # Log failed callback parsing
                print(f"Failed to parse M-Pesa callback: {transaction_data}")
                return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed to parse callback'})

            # Find the transaction
            checkout_request_id = transaction_data.get('checkout_request_id')
            if not checkout_request_id:
                return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Missing checkout request ID'})

            try:
                mpesa_transaction = MPesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )
            except MPesaTransaction.DoesNotExist:
                print(f"M-Pesa transaction not found: {checkout_request_id}")
                return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Transaction not found'})

            # Store callback response
            mpesa_transaction.callback_response = callback_data

            # Process the callback based on result code
            result_code = transaction_data.get('result_code')
            result_description = transaction_data.get('result_description', 'Unknown result')

            if result_code == 0:
                # Successful payment
                mpesa_transaction.mark_completed(
                    receipt_number=transaction_data.get('mpesa_receipt_number'),
                    transaction_date=timezone.now()
                )

                # Update order status
                order = mpesa_transaction.order
                order.payment_status = 'paid'
                order.status = 'paid'
                order.save()

                print(f"M-Pesa payment completed: {transaction_data.get('mpesa_receipt_number')}")
                print(f"Order {order.order_number} payment completed")

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

                # Update order status to cancelled for cancelled transactions
                if mpesa_transaction.order:
                    order = mpesa_transaction.order
                    if result_code in [17, 1, 26]:  # User cancelled or transaction cancelled
                        order.status = 'cancelled'
                        order.status_notes = f"M-Pesa payment cancelled: {error_message}"
                    else:
                        order.status = 'failed'  # Keep pending for retryable failures
                        order.status_notes = f"M-Pesa payment failed: {error_message}"
                    order.save()

                print(f"M-Pesa payment failed (Result Code: {result_code}): {error_message}")

            # Return success response to M-Pesa
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Callback processed successfully'
            })

        except Exception as e:
            print(f"Error processing M-Pesa callback: {str(e)}")
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': f'Error: {str(e)}'
            })

class CheckTransactionStatusView(LoginRequiredMixin, View):
    """Check M-Pesa transaction status"""

    def get(self, request, transaction_id):
        try:
            mpesa_transaction = get_object_or_404(
                MPesaTransaction, 
                id=transaction_id, 
                order__user=request.user
            )

            return JsonResponse({
                'success': True,
                'status': mpesa_transaction.status,
                'mpesa_receipt_number': mpesa_transaction.mpesa_receipt_number,
                'transaction_date': mpesa_transaction.transaction_date.isoformat() if mpesa_transaction.transaction_date else None,
                'error_message': mpesa_transaction.error_message,
                'is_successful': mpesa_transaction.is_successful
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

class GenerateReceiptView(LoginRequiredMixin, View):
    def get(self, request, order_number):
        # Allow management users to access receipts for all orders,
        # while customers can only access receipts for their own orders
        if hasattr(request.user, 'role') and request.user.role in ['super_admin', 'manager', 'director', 'sales_manager', 'cashier']:
            # Management users can see all receipts
            order = get_object_or_404(Order, order_number=order_number)
        else:
            # Customers can only see their own receipts
            order = get_object_or_404(Order, order_number=order_number, user=request.user)

        # Get or create receipt
        receipt, created = Receipt.objects.get_or_create(
            order=order,
            defaults={'issued_by': request.user}
        )

        # Generate PDF if not exists or file doesn't exist on disk
        if not receipt.receipt_file or created:
            receipt.generate_receipt_pdf()

        # Check if file actually exists
        if not receipt.receipt_file or not receipt.receipt_file.path:
            # Generate again if file path is missing
            receipt.generate_receipt_pdf()

        if not receipt.receipt_file or not receipt.receipt_file.path:
            from django.http import Http404
            raise Http404("Receipt file could not be generated")

        # Return the PDF file for download
        from django.http import FileResponse
        import os
        import mimetypes

        file_path = receipt.receipt_file.path

        # Check if file exists on disk
        if not os.path.exists(file_path):
            # Regenerate the PDF
            receipt.generate_receipt_pdf()
            file_path = receipt.receipt_file.path

            if not os.path.exists(file_path):
                from django.http import Http404
                raise Http404("Receipt file could not be generated")

        try:
            # Open and return the file
            file = open(file_path, 'rb')
            response = FileResponse(file, content_type='application/pdf')

            # Set headers for download
            response['Content-Disposition'] = f'attachment; filename="{receipt.receipt_number}.pdf"'
            response['Content-Length'] = os.path.getsize(file_path)

            return response

        except Exception as e:
            # If file reading fails, return error JSON (fallback for debugging)
            return JsonResponse({
                'success': False,
                'error': f'Error serving receipt file: {str(e)}'
            }, status=500)

class UpdateOrderStatusView(LoginRequiredMixin, View):
    """Update order status - Management only"""

    def post(self, request, order_number):
        # Check if user has management permissions
        if not hasattr(request.user, 'role') or request.user.role not in ['super_admin', 'manager', 'director', 'sales_manager', 'cashier']:
            return JsonResponse({
                'success': False,
                'message': 'Permission denied. Management access required.'
            }, status=403)

        try:
            order = get_object_or_404(Order, order_number=order_number)

            data = json.loads(request.body)
            new_status = data.get('status')
            notes = data.get('notes', '')

            if not new_status:
                return JsonResponse({
                    'success': False,
                    'message': 'Status is required'
                }, status=400)

            # Validate status choice
            valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
            if new_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid status'
                }, status=400)

            # Check if status transition is allowed
            next_options = order.get_next_status_options()
            if next_options and new_status not in next_options:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot change from {order.get_status_display()} to {dict(Order.STATUS_CHOICES)[new_status]}'
                }, status=400)

            # Store previous status for history
            previous_status = order.status

            # Update order status
            order.status = new_status
            order.status_updated_by = request.user
            order.status_notes = notes

            # Handle payment status for pay-on-delivery orders
            if previous_status == 'delivered' and new_status == 'paid':
                order.payment_status = 'paid'
            elif new_status == 'pay_on_delivery':
                order.payment_status = 'pending'

            order.save()

            # Create status history record
            OrderStatusHistory.objects.create(
                order=order,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=request.user,
                notes=notes
            )



            return JsonResponse({
                'success': True,
                'message': f'Order status updated to {order.get_status_display()}',
                'order': {
                    'order_number': order.order_number,
                    'status': order.status,
                    'status_display': order.get_status_display(),
                    'next_options': order.get_next_status_options(),
                    'updated_at': order.status_updated_at.isoformat(),
                    'updated_by': order.status_updated_by.get_full_name() if order.status_updated_by else None
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

class ReceiptDownloadView(View):
    """Public receipt download view by receipt ID"""

    def get(self, request, receipt_id):
        try:
            # Get the receipt
            receipt = get_object_or_404(Receipt, id=receipt_id)

            # Check permissions
            if not self._has_access(request, receipt):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("You don't have permission to access this receipt.")

            # Generate PDF if not exists or file doesn't exist on disk
            if not receipt.receipt_file or not receipt.receipt_file.path:
                receipt.generate_receipt_pdf()

            # Check if file actually exists
            if not receipt.receipt_file or not receipt.receipt_file.path:
                from django.http import Http404
                raise Http404("Receipt file could not be generated")

            import os
            file_path = receipt.receipt_file.path

            # Check if file exists on disk
            if not os.path.exists(file_path):
                # Regenerate the PDF
                receipt.generate_receipt_pdf()
                file_path = receipt.receipt_file.path

                if not os.path.exists(file_path):
                    from django.http import Http404
                    raise Http404("Receipt file could not be generated")

            # Serve the PDF file
            from django.http import FileResponse
            import mimetypes

            try:
                # Open and return the file
                file = open(file_path, 'rb')
                response = FileResponse(file, content_type='application/pdf')

                # Set headers for download
                response['Content-Disposition'] = f'attachment; filename="{receipt.receipt_number}.pdf"'
                response['Content-Length'] = os.path.getsize(file_path)

                return response

            except Exception as e:
                # If file reading fails, return error
                return JsonResponse({
                    'success': False,
                    'error': f'Error serving receipt file: {str(e)}'
                }, status=500)

        except Exception as e:
            from django.http import Http404
            raise Http404(f"Receipt not found or access denied: {str(e)}")

    def _has_access(self, request, receipt):
        """Check if user has access to this receipt"""
        # Allow access if user is staff/admin
        if request.user.is_authenticated and (request.user.is_staff or request.user.role in ['super_admin', 'manager', 'director', 'sales_manager', 'cashier']):
            return True

        # Allow access if user is the customer and is authenticated
        if request.user.is_authenticated and receipt.order.customer.email == request.user.email:
            return True

        # For unauthenticated access, we could add email verification
        # For now, deny access to prevent unauthorized downloads
        return False

class OrderStatusHistoryView(LoginRequiredMixin, View):
    """Get order status history"""

    def get(self, request, order_number):
        # Check if user has access to this order
        try:
            if request.user.role == 'customer':
                order = get_object_or_404(Order, order_number=order_number, user=request.user)
            else:
                order = get_object_or_404(Order, order_number=order_number)

            history = order.status_history.all()

            return JsonResponse({
                'success': True,
                'history': [{
                    'id': h.id,
                    'previous_status': h.previous_status,
                    'previous_status_display': dict(Order.STATUS_CHOICES).get(h.previous_status, '') if h.previous_status else '',
                    'new_status': h.new_status,
                    'new_status_display': dict(Order.STATUS_CHOICES)[h.new_status],
                    'changed_by': h.changed_by.get_full_name() if h.changed_by else 'System',
                    'notes': h.notes,
                    'created_at': h.created_at.isoformat()
                } for h in history]
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


class OrderTrackingView(View):
    """Public order tracking view - no login required"""

    def get(self, request, order_number=None):
        # Handle direct URL parameters and PRG redirects
        context = {'order_number': order_number}

        # Check for direct URL parameters (from order detail page)
        direct_order_number = request.GET.get('order_number', '').strip()
        direct_email = request.GET.get('email', '').strip().lower()

        # Check for result display parameters from form submission (PRG redirect)
        show_order = request.GET.get('show_order', '').strip()
        email = request.GET.get('email', '').strip().lower()

        # Prioritize direct URL parameters over PRG parameters
        if direct_order_number:
            show_order = direct_order_number
            email = direct_email

        if show_order:
            # Display order results
            try:
                order = Order.objects.get(order_number=show_order.upper())

                # Verify email matches (security check)
                if email and order.customer.email.lower() != email:
                    context['error'] = 'Order not found or email does not match'
                    context['order_number'] = show_order
                    context['email'] = email
                else:
                    # Build full order context for results display
                    status_history = order.status_history.all().order_by('created_at')
                    status_order = ['received', 'pending_payment', 'pay_on_delivery', 'paid', 'processing', 'packed_ready', 'shipped', 'out_for_delivery', 'delivered', 'completed']
                    current_status_index = status_order.index(order.status) if order.status in status_order else 0
                    progress_percentage = int((current_status_index / (len(status_order) - 1)) * 100)

                    estimated_delivery = None
                    if order.delivery_date:
                        estimated_delivery = order.delivery_date
                    elif order.status in ['shipped', 'out_for_delivery']:
                        from datetime import datetime, timedelta
                        estimated_delivery = datetime.now().date() + timedelta(days=3)

                    context.update({
                        'order': order,
                        'status_history': status_history,
                        'progress_percentage': progress_percentage,
                        'estimated_delivery': estimated_delivery,
                        'is_tracking_result': True
                    })

            except Order.DoesNotExist:
                context['error'] = 'Order not found. Please check your order number and try again.'
                context['order_number'] = show_order
                context['email'] = email
            except ValueError:
                context['error'] = 'Invalid order number format.'
                context['order_number'] = show_order
                context['email'] = email
        else:
            # Handle error parameters
            error_type = request.GET.get('error')
            if error_type:
                if error_type == 'no_order_number':
                    context['error'] = 'Please enter an order number'
                elif error_type == 'email_mismatch':
                    context['error'] = 'Order not found or email does not match'
                elif error_type == 'order_not_found':
                    context['error'] = 'Order not found. Please check your order number and try again.'
                elif error_type == 'invalid_format':
                    context['error'] = 'Invalid order number format.'
                else:
                    context['error'] = 'An error occurred while processing your request.'

                context['order_number'] = request.GET.get('order_number', '')
                context['email'] = email

        return render(request, 'ecommerce/order_tracking.html', context)

    def post(self, request, order_number=None):
        # Handle form submission - use PRG (Post/Redirect/Get) pattern to avoid form resubmission warnings

        submitted_order_number = request.POST.get('order_number', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()

        if not submitted_order_number:
            # Redirect back to form with error parameters
            return redirect(f"{reverse('ecommerce:track_order')}?error=no_order_number&email={email}")

        try:
            # Find order by order number
            order = Order.objects.get(order_number=submitted_order_number)

            # Verify email matches (security check)
            if email and order.customer.email.lower() != email:
                return redirect(f"{reverse('ecommerce:track_order')}?error=email_mismatch&order_number={submitted_order_number}&email={email}")

            # Success - redirect to GET URL with result parameters
            redirect_url = reverse('ecommerce:track_order')
            return redirect(f"{redirect_url}?show_order={submitted_order_number}&email={email}")

        except Order.DoesNotExist:
            return redirect(f"{reverse('ecommerce:track_order')}?error=order_not_found&order_number={submitted_order_number}&email={email}")
        except ValueError as e:
            return redirect(f"{reverse('ecommerce:track_order')}?error=invalid_format&order_number={submitted_order_number}&email={email}")


class OrderTrackingAPIView(View):
    """API endpoint for order tracking"""

    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number.upper())

            # Basic order info (no sensitive data)
            data = {
                'order_number': order.order_number,
                'status': order.status,
                'status_display': order.get_status_display(),
                'created_at': order.created_at.isoformat(),
                'last_updated': order.status_updated_at.isoformat() if order.status_updated_at else order.updated_at.isoformat(),
                'tracking_number': order.tracking_number,
                'estimated_delivery': order.delivery_date.isoformat() if order.delivery_date else None,
            }

            # Status history
            status_history = []
            for history in order.status_history.all().order_by('created_at'):
                status_history.append({
                    'status': history.new_status,
                    'status_display': dict(Order.STATUS_CHOICES)[history.new_status],
                    'timestamp': history.created_at.isoformat(),
                    'notes': history.notes
                })

            data['status_history'] = status_history

            return JsonResponse({
                'success': True,
                'data': data
            })

        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Order not found'
            }, status=404)


class OrderManagementAPIView(LoginRequiredMixin, View):
    """API for order management operations"""

    def get(self, request):
        # Check management permissions
        print(f"DEBUG: User: {request.user}, Role: {getattr(request.user, 'role', 'NO ROLE')}")
        if not hasattr(request.user, 'role') or request.user.role not in ['super_admin', 'manager', 'director', 'sales_manager', 'cashier']:
            return JsonResponse({
                'success': False,
                'message': f'Permission denied. User role: {getattr(request.user, "role", "NO ROLE")}'
            }, status=403)

        try:
            # Get filtering parameters
            status = request.GET.get('status', '')
            date_range = request.GET.get('date_range', '')
            search = request.GET.get('search', '')
            page = int(request.GET.get('page', 1))
            per_page = 20

            # Build queryset
            orders = Order.objects.all()
            print(f"DEBUG: Total orders in database: {orders.count()}")

            if status:
                orders = orders.filter(status=status)
                print(f"DEBUG: Orders after status filter '{status}': {orders.count()}")

            if search:
                orders = orders.filter(
                    models.Q(order_number__icontains=search) |
                    models.Q(customer__email__icontains=search) |
                    models.Q(customer__name__icontains=search)
                )

            if date_range:
                from datetime import datetime, timedelta
                today = timezone.now().date()

                if date_range == 'today':
                    orders = orders.filter(created_at__date=today)
                elif date_range == 'week':
                    week_start = today - timedelta(days=today.weekday())
                    orders = orders.filter(created_at__date__gte=week_start)
                elif date_range == 'month':
                    orders = orders.filter(created_at__year=today.year, created_at__month=today.month)
                elif date_range == 'quarter':
                    quarter = (today.month - 1) // 3 + 1
                    quarter_start = datetime(today.year, (quarter - 1) * 3 + 1, 1).date()
                    orders = orders.filter(created_at__date__gte=quarter_start)
                elif date_range == 'year':
                    orders = orders.filter(created_at__year=today.year)

            # Apply pagination
            total_count = orders.count()
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            orders = orders[offset:offset + per_page]

            # Serialize orders
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer.name if order.customer.name and order.customer.name != order.customer.email else order.customer.email,
                    'customer_email': order.customer.email,
                    'status': order.status,
                    'status_display': order.get_status_display(),
                    'payment_status': order.payment_status,
                    'payment_status_display': dict(order._meta.get_field('payment_status').choices)[order.payment_status],
                    'total_amount': str(order.total_amount),
                    'created_at': order.created_at.isoformat(),
                    'next_status_options': order.get_next_status_options(),
                    'can_be_cancelled': order.can_be_cancelled(),
                    'can_be_shipped': order.can_be_shipped(),
                    'can_be_returned': order.can_be_returned(),
                })

            return JsonResponse({
                'success': True,
                'orders': orders_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'per_page': per_page
                }
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
