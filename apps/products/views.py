from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db import models
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from .models import Product, ProductCategory
from . import forms
import logging

# Set up logger
logger = logging.getLogger(__name__)

class ProductListView(ListView):
    model = Product
    template_name = 'website/products.html'
    context_object_name = 'products'
    paginate_by = 8  # Reduced for better infinite scroll experience

    def get_queryset(self):
        # Filter for customer-visible products only
        queryset = Product.objects.filter(
            status='active',
            show_to_customers=True
        ).select_related('category').prefetch_related('images')

        # Further filter by availability (in stock or allow backorders)
        queryset = queryset.filter(
            models.Q(track_quantity=False) |  # Don't track quantity = always available
            models.Q(quantity_in_stock__gt=0) |  # In stock
            models.Q(allow_backorders=True)  # Allow backorders
        )

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(brand__icontains=search)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Product type filter
        product_type = self.request.GET.get('type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = ProductCategory.objects.filter(is_active=True).prefetch_related('products')

        # Prepare category data with specifications summary
        # Define main categories - everything else goes to accessories
        main_categories = ['solar-panels', 'inverters', 'batteries', 'mounting-racking']
        
        category_specs = []
        accessories_products_count = 0
        accessories_sample_product = None

        for category in categories:
            products = category.products.filter(status='active', show_to_customers=True)

            if category.slug in main_categories and products.exists():
                category_specs.append({
                    'category': category,
                    'products_count': products.count(),
                    'sample_product': products.first(),
                    'has_products': True
                })
            elif category.slug not in main_categories and products.exists():
                # Aggregate ALL non-main categories as accessories
                accessories_products_count += products.count()
                if not accessories_sample_product:
                    accessories_sample_product = products.first()
        
        # Add aggregated accessories category if there are products
        if accessories_products_count > 0:
            # Get or create the main accessories category
            accessories_category = categories.filter(slug='accessories').first()
            if not accessories_category:
                # Fallback to any non-main category if main accessories doesn't exist
                accessories_category = categories.exclude(slug__in=main_categories).first()
            
            if accessories_category:
                category_specs.append({
                    'category': accessories_category,
                    'products_count': accessories_products_count,
                    'sample_product': accessories_sample_product,
                    'has_products': True
                })
        
        context['categories'] = categories
        context['category_specs'] = category_specs
        context['product_types'] = Product.PRODUCT_TYPES
        return context
    
    def get(self, request, *args, **kwargs):
        # Handle AJAX requests for infinite scroll
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.object_list = self.get_queryset()
            context = self.get_context_data()

            # Render only the product cards with full template context
            full_context = {
                'products': context['page_obj'].object_list,
                'request': request,
            }

            # Add context processor data for AJAX rendering
            from django.template import RequestContext
            from django.template.loader import get_template

            # Create a template object and render with request context
            try:
                template = get_template('website/partials/product_cards.html')
                request_context = RequestContext(request)
                request_context.push(full_context)

                products_html = template.render(request_context)
                request_context.pop()

                return JsonResponse({
                    'html': products_html,
                    'has_next': context['page_obj'].has_next(),
                    'next_page_number': context['page_obj'].next_page_number() if context['page_obj'].has_next() else None
                })
            except Exception as e:
                # Log the error and return a proper error response for AJAX
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"AJAX template rendering error: {e}", exc_info=True)
                return JsonResponse({
                    'error': 'Error rendering products'
                }, status=500)

        return super().get(request, *args, **kwargs)

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(
            status='active',
            show_to_customers=True
        ).prefetch_related('images', 'documents', 'reviews')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Get related products (same category, excluding current product)
        related_products = Product.objects.filter(
            category=product.category,
            status='active',
            show_to_customers=True
        ).exclude(id=product.id).prefetch_related('images')[:4]
        
        # If not enough related products in same category, get from other categories
        if related_products.count() < 4:
            additional_products = Product.objects.filter(
                status='active',
                show_to_customers=True
            ).exclude(id=product.id).exclude(
                id__in=[p.id for p in related_products]
            ).prefetch_related('images')[:4-related_products.count()]
            
            related_products = list(related_products) + list(additional_products)
        
        context['related_products'] = related_products
        return context

class ProductCategoryView(ListView):
    model = Product
    template_name = 'products/category.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        # Special handling for accessories category - include all accessory subcategories
        if self.kwargs['slug'] == 'accessories':
            # Get the main accessories category for context, but don't require it to have products
            try:
                self.category = ProductCategory.objects.get(slug='accessories', is_active=True)
            except ProductCategory.DoesNotExist:
                # If accessories category doesn't exist, use the first accessory subcategory as fallback
                self.category = ProductCategory.objects.filter(
                    slug__in=['cables', 'connectors', 'charge-controllers'], 
                    is_active=True
                ).first()
                if not self.category:
                    raise get_object_or_404(ProductCategory, slug=self.kwargs['slug'])
            
            # Define main categories to exclude from accessories
            main_categories = ['solar-panels', 'inverters', 'batteries', 'mounting-racking']
            
            # Return ALL products that are NOT in the main categories
            return Product.objects.filter(
                status='active',
                show_to_customers=True
            ).exclude(
                category__slug__in=main_categories
            ).select_related('category').prefetch_related('images')
        
        # Regular category handling
        self.category = get_object_or_404(ProductCategory, slug=self.kwargs['slug'])
        return Product.objects.filter(
            category=self.category, 
            status='active',
            show_to_customers=True
        ).select_related('category').prefetch_related('images')
    
    def get_template_names(self):
        # Use special template for accessories category
        if self.kwargs['slug'] == 'accessories':
            return ['products/accessories_category.html']
        return ['products/category.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        
        # Add all non-main categories for the accessories page
        if self.kwargs['slug'] == 'accessories':
            main_categories = ['solar-panels', 'inverters', 'batteries', 'mounting-racking']
            accessory_categories = ProductCategory.objects.filter(
                is_active=True
            ).exclude(
                slug__in=main_categories
            ).prefetch_related('products')
            
            # Prepare categories with product counts
            categories_with_products = []
            for cat in accessory_categories:
                products = cat.products.filter(status='active', show_to_customers=True)
                if products.exists():
                    categories_with_products.append({
                        'category': cat,
                        'products_count': products.count()
                    })
            
            context['accessory_categories'] = categories_with_products
        
        return context

# Management Views (for staff/admin use)
class ProductManagementListView(LoginRequiredMixin, ListView):
    """Internal product management view for staff"""
    model = Product
    template_name = 'products/management_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        # Show ALL products for management (not filtered by customer visibility)
        queryset = Product.objects.all().select_related('category').prefetch_related('images')

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(brand__icontains=search)
            )

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Visibility filter
        visibility = self.request.GET.get('visibility')
        if visibility == 'customer_visible':
            queryset = queryset.filter(show_to_customers=True)
        elif visibility == 'customer_hidden':
            queryset = queryset.filter(show_to_customers=False)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Product.STATUS_CHOICES
        context['total_products'] = Product.objects.count()
        context['customer_visible'] = Product.objects.filter(show_to_customers=True).count()
        context['customer_hidden'] = Product.objects.filter(show_to_customers=False).count()
        return context

class ProductFacebookShareView(LoginRequiredMixin, DetailView):
    """View for sharing products to Facebook"""
    model = Product
    template_name = 'products/facebook_share.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.all().prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        # Build Facebook share URL
        product_url = self.request.build_absolute_uri(product.get_absolute_url())

        # Get primary image URL
        primary_image = product.get_primary_image_url()
        if primary_image:
            image_url = self.request.build_absolute_uri(primary_image)
        else:
            image_url = None

        # Build share text
        share_text = f"Check out our {product.name}"

        if product.brand:
            share_text += f" by {product.brand}"

        share_text += "!\n\n"

        # Add key specs
        specs = []
        if product.power_rating:
            specs.append(f"Power: {product.power_rating}W")
        if product.efficiency:
            specs.append(f"Efficiency: {product.efficiency}%")
        if product.warranty_years:
            specs.append(f"Warranty: {product.warranty_years} years")

        if specs:
            share_text += "Key Features:\n" + "\n".join(f"• {spec}" for spec in specs) + "\n\n"

        # Add price if available
        if product.customer_display_price:
            if product.is_on_sale:
                share_text += f"Price: KES {product.sale_price:,.0f} (Was KES {product.selling_price:,.0f})\n"
            else:
                share_text += f"Price: KES {product.selling_price:,.0f}\n"

        share_text += f"\n🔗 Learn more: {product_url}"

        # Get Facebook App ID from settings
        from django.conf import settings
        facebook_app_id = getattr(settings, 'FACEBOOK_APP_ID', '')

        # Facebook Share Dialog URL (modern approach)
        facebook_share_url = f"https://www.facebook.com/dialog/share?"
        params = []
        if facebook_app_id:
            params.append(f"app_id={facebook_app_id}")
        params.append("display=popup")
        params.append(f"href={product_url}")
        if share_text:
            params.append(f"quote={share_text}")

        facebook_share_url += "&".join(params)

        context.update({
            'facebook_share_url': facebook_share_url,
            'share_text': share_text,
            'product_url': product_url,
            'image_url': image_url,
        })

        return context


# Staff Product Management Views
class StaffRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user has staff/management permissions for product management"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Allow super admins, managers, inventory managers
        allowed_roles = ['super_admin', 'manager', 'inventory_manager']
        if request.user.role not in allowed_roles:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to manage products.")

        return super().dispatch(request, *args, **kwargs)


class ProductCreateView(StaffRequiredMixin, CreateView):
    """View for staff to create new products"""
    model = Product
    form_class = forms.ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Product'
        context['submit_text'] = 'Create Product'

        # For create view, self.object is None for new products
        # Initialize inline formsets - always available for both GET and POST
        if self.request.method == 'POST':
            context['image_formset'] = forms.ProductImageFormSet(
                self.request.POST, self.request.FILES, prefix='images'
            )
            context['document_formset'] = forms.ProductDocumentFormSet(
                self.request.POST, self.request.FILES, prefix='documents'
            )
        else:
            context['image_formset'] = forms.ProductImageFormSet(prefix='images')
            context['document_formset'] = forms.ProductDocumentFormSet(prefix='documents')

        return context

    def form_valid(self, form):
        # Get formsets from context - they should already be validated in get_context_data
        context = self.get_context_data()
        image_formset = context['image_formset']
        document_formset = context['document_formset']

        # Double-check formset validation
        if not (image_formset.is_valid() and document_formset.is_valid()):
            # If formsets are invalid, show form again with errors instead of calling form_invalid
            from django.contrib import messages

            # Add specific error messages for formsets
            if not image_formset.is_valid():
                for error in image_formset.non_form_errors():
                    messages.error(self.request, f'Image error: {error}')
                for form_errors in image_formset.errors:
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(self.request, f'Image {field}: {error}')

            if not document_formset.is_valid():
                for error in document_formset.non_form_errors():
                    messages.error(self.request, f'Document error: {error}')
                for form_errors in document_formset.errors:
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(self.request, f'Document {field}: {error}')

            return self.render_to_response(self.get_context_data())

        # Save the main form first to create the instance
        self.object = form.save()

        # Save formsets with the new instance
        image_formset.instance = self.object
        document_formset.instance = self.object

        try:
            image_formset.save()
            document_formset.save()

            from django.contrib import messages
            messages.success(self.request, f'Product "{self.object.name}" created successfully.')
            return super().form_valid(form)

        except Exception as e:
            # If formsets fail to save, log error and return form invalid
            from django.contrib import messages
            messages.error(self.request, f'Error saving related data: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Enhanced form_invalid to handle formset errors better and preserve POST data"""
        from django.contrib import messages

        # Create formsets with POST data to preserve validation errors and uploaded files
        # For create view, instance is None
        image_formset = forms.ProductImageFormSet(
            self.request.POST, self.request.FILES, prefix='images'
        )
        document_formset = forms.ProductDocumentFormSet(
            self.request.POST, self.request.FILES, prefix='documents'
        )

        # Validate formsets to ensure error messages are available
        image_formset.is_valid()
        document_formset.is_valid()

        # Add specific error messages for formsets
        if not image_formset.is_valid():
            for error in image_formset.non_form_errors():
                messages.error(self.request, f'Image error: {error}')
            for form_errors in image_formset.errors:
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(self.request, f'Image {field}: {error}')

        if not document_formset.is_valid():
            for error in document_formset.non_form_errors():
                messages.error(self.request, f'Document error: {error}')
            for form_errors in document_formset.errors:
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(self.request, f'Document {field}: {error}')

        # Override context with properly validated formsets
        context = self.get_context_data()
        context['image_formset'] = image_formset
        context['document_formset'] = document_formset

        return self.render_to_response(context)


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    """View for staff to edit existing products"""
    model = Product
    form_class = forms.ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:manage')

    def get_context_data(self, **kwargs):
        logger.info(f"ProductUpdateView.get_context_data called for product ID: {getattr(self.object, 'id', 'None')}")
        logger.info(f"Request method: {self.request.method}")

        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Product: {self.object.name}'
        context['submit_text'] = 'Update Product'

        # Initialize inline formsets - always available for both GET and POST
        if self.request.method == 'POST':
            logger.info("Initializing formsets with POST data for product update")
            context['image_formset'] = forms.ProductImageFormSet(
                self.request.POST, self.request.FILES, instance=self.object,
                prefix='images'
            )
            context['document_formset'] = forms.ProductDocumentFormSet(
                self.request.POST, self.request.FILES, instance=self.object,
                prefix='documents'
            )
            logger.info(f"Image formset initialized with {len(context['image_formset'])} forms")
            logger.info(f"Document formset initialized with {len(context['document_formset'])} forms")
        else:
            logger.info("Initializing formsets for GET request (display form)")
            context['image_formset'] = forms.ProductImageFormSet(instance=self.object, prefix='images')
            context['document_formset'] = forms.ProductDocumentFormSet(instance=self.object, prefix='documents')

        logger.info("ProductUpdateView.get_context_data completed")
        return context

    def form_valid(self, form):
        logger.info(f"ProductUpdateView.form_valid called for product ID: {getattr(self.object, 'id', 'None')}")
        logger.info(f"Main form is valid: {form.is_valid()}")

        # Get formsets from context - they should already be validated in get_context_data
        context = self.get_context_data()
        image_formset = context['image_formset']
        document_formset = context['document_formset']

        logger.info(f"Image formset is_valid: {image_formset.is_valid()}")
        logger.info(f"Document formset is_valid: {document_formset.is_valid()}")

        # Double-check formset validation
        if not (image_formset.is_valid() and document_formset.is_valid()):
            logger.warning("Formsets validation failed in form_valid")
            # If formsets are invalid, show form again with errors instead of calling form_invalid
            from django.contrib import messages

            # Add specific error messages for formsets
            if not image_formset.is_valid():
                logger.error(f"Image formset errors: {image_formset.errors}")
                logger.error(f"Image formset non-form errors: {image_formset.non_form_errors()}")
                for error in image_formset.non_form_errors():
                    messages.error(self.request, f'Image error: {error}')
                for form_errors in image_formset.errors:
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(self.request, f'Image {field}: {error}')

            if not document_formset.is_valid():
                logger.error(f"Document formset errors: {document_formset.errors}")
                logger.error(f"Document formset non-form errors: {document_formset.non_form_errors()}")
                for error in document_formset.non_form_errors():
                    messages.error(self.request, f'Document error: {error}')
                for form_errors in document_formset.errors:
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(self.request, f'Document {field}: {error}')

            logger.info("Returning to form display with validation errors")
            return self.render_to_response(self.get_context_data())

        logger.info("Formsets validation passed, proceeding to save")

        # Save the main form first
        logger.info("Saving main product form")
        self.object = form.save()
        logger.info(f"Main form saved successfully, product ID: {self.object.id}")

        # Save formsets with the updated instance
        image_formset.instance = self.object
        document_formset.instance = self.object

        try:
            logger.info("Saving image formset")
            saved_images = image_formset.save()
            logger.info(f"Image formset saved, {len(saved_images)} images saved")

            logger.info("Saving document formset")
            saved_docs = document_formset.save()
            logger.info(f"Document formset saved, {len(saved_docs)} documents saved")

            from django.contrib import messages
            messages.success(self.request, f'Product "{self.object.name}" updated successfully.')

            logger.info(f"Product update completed successfully for product ID: {self.object.id}")
            return super().form_valid(form)

        except Exception as e:
            # If formsets fail to save, log error and return form invalid
            logger.error(f"Error saving formsets: {str(e)}", exc_info=True)
            from django.contrib import messages
            messages.error(self.request, f'Error saving related data: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Enhanced form_invalid to handle formset errors better and preserve POST data"""
        logger.info(f"ProductUpdateView.form_invalid called for product ID: {getattr(self.object, 'id', 'None')}")
        logger.info(f"Main form is invalid: form errors = {form.errors}")

        from django.contrib import messages

        # Create formsets with POST data to preserve validation errors and uploaded files
        logger.info("Creating formsets with POST data in form_invalid")
        image_formset = forms.ProductImageFormSet(
            self.request.POST, self.request.FILES, instance=self.object,
            prefix='images'
        )
        document_formset = forms.ProductDocumentFormSet(
            self.request.POST, self.request.FILES, instance=self.object,
            prefix='documents'
        )

        # Validate formsets to ensure error messages are available
        logger.info("Validating formsets in form_invalid")
        image_valid = image_formset.is_valid()
        document_valid = document_formset.is_valid()
        logger.info(f"Image formset validation result: {image_valid}")
        logger.info(f"Document formset validation result: {document_valid}")

        # Add specific error messages for formsets
        if not image_valid:
            logger.warning(f"Image formset errors in form_invalid: {image_formset.errors}")
            logger.warning(f"Image formset non-form errors: {image_formset.non_form_errors()}")
            for error in image_formset.non_form_errors():
                messages.error(self.request, f'Image error: {error}')
            for form_errors in image_formset.errors:
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(self.request, f'Image {field}: {error}')

        if not document_valid:
            logger.warning(f"Document formset errors in form_invalid: {document_formset.errors}")
            logger.warning(f"Document formset non-form errors: {document_formset.non_form_errors()}")
            for error in document_formset.non_form_errors():
                messages.error(self.request, f'Document error: {error}')
            for form_errors in document_formset.errors:
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(self.request, f'Document {field}: {error}')

        # Override context with properly validated formsets
        logger.info("Preparing context with validated formsets for re-display")
        context = self.get_context_data()
        context['image_formset'] = image_formset
        context['document_formset'] = document_formset

        logger.info("Returning to form display with validation errors from form_invalid")
        return self.render_to_response(context)
