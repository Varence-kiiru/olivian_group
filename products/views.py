from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category


def product_list(request):
    categories = Category.objects.all()
    selected_category = request.GET.get('category')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', '-created_at')  # Default sort by newest

    products = Product.objects.all()

    if selected_category:
        products = products.filter(category__slug=selected_category)
   
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(features__icontains=search_query) |
            Q(applications__icontains=search_query)
        )
    
    # Sorting
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == '-name':
        products = products.order_by('-name')
    elif sort_by == 'price':
        products = products.order_by('regular_price', 'sale_price')
    elif sort_by == '-price':
        products = products.order_by('-regular_price', '-sale_price')
    else:
        products = products.order_by(sort_by)
   
    # Pagination
    paginator = Paginator(products, 9)  # 9 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
   
    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'sort_by': sort_by
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Get more related products (up to 6)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:6]
   
    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'products/product_detail.html', context)


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', '-created_at')  # Default sort by newest
    
    products = Product.objects.filter(category=category)
    
    # Search within category
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(features__icontains=search_query) |
            Q(applications__icontains=search_query)
        )
    
    # Sorting
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == '-name':
        products = products.order_by('-name')
    elif sort_by == 'price':
        products = products.order_by('regular_price', 'sale_price')
    elif sort_by == '-price':
        products = products.order_by('-regular_price', '-sale_price')
    else:
        products = products.order_by(sort_by)
   
    paginator = Paginator(products, 9)
    page = request.GET.get('page')
    products = paginator.get_page(page)
   
    context = {
        'category': category,
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by
    }
    return render(request, 'products/category_products.html', context)


def category_list(request):
    category_list = Category.objects.all()
   
    # Get categories with product counts and price ranges
    for category in category_list:
        products = category.products.all()
        category.product_count = products.count()
       
        # Initialize price variables
        min_prices = []
        max_prices = []
        
        # Calculate price range
        if products:
            for product in products:
                # If product has a price range, use those values
                if product.has_price_range and product.price_min is not None and product.price_max is not None:
                    min_prices.append(product.price_min)
                    max_prices.append(product.price_max)
                # If product is on sale, use sale price
                elif product.on_sale and product.sale_price is not None:
                    min_prices.append(product.sale_price)
                    max_prices.append(product.sale_price)
                # Otherwise use regular price
                elif product.regular_price is not None:
                    min_prices.append(product.regular_price)
                    max_prices.append(product.regular_price)
            
            # Set category price range if we have prices
            if min_prices and max_prices:
                category.min_price = min(min_prices)
                category.max_price = max(max_prices)
   
    paginator = Paginator(category_list, 6)  # 6 categories per page
    page = request.GET.get('page')
    categories = paginator.get_page(page)
   
    context = {
        'categories': categories,
    }
    return render(request, 'products/categories.html', context)
