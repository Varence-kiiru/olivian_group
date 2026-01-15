from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.blog.models import Post
from apps.products.models import Product
from datetime import datetime
from django.utils import timezone

class StaticSitemap(Sitemap):
    """Sitemap for static pages"""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return [
            'core:home',
            'core:about',
            'core:services',
            'core:contact',
            'products:list',
            'blog:blog',
            'projects:showcase',
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        # Return current date for static pages
        return datetime.now().date()


class DynamicSitemap(Sitemap):
    """Sitemap for dynamic content"""
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        items = []

        # Add published blog posts
        blog_posts = Post.objects.filter(status='published')
        items.extend([f'blog:post_{post.slug}' for post in blog_posts])

        # Add individual products (only customer-visible ones)
        customer_products = Product.objects.filter(
            status='active',
            show_to_customers=True
        )
        items.extend([f'product:{product.slug}' for product in customer_products])

        # Add product categories
        items.extend([
            'products:category_solar_panels',
            'products:category_inverters',
            'products:category_batteries',
            'products:category_accessories',
        ])

        return items

    def location(self, item):
        if item.startswith('blog:post_'):
            slug = item.replace('blog:post_', '')
            return reverse('blog:post_detail', kwargs={'slug': slug})
        elif item.startswith('product:'):
            slug = item.replace('product:', '')
            return reverse('products:detail', kwargs={'slug': slug})
        elif item.startswith('products:category_'):
            category = item.replace('products:category_', '')
            return reverse('products:category', kwargs={'slug': category})
        return reverse(item)

    def priority(self, obj):
        # Higher priority for blog posts and featured products
        if obj.startswith('blog:post_'):
            slug = obj.replace('blog:post_', '')
            try:
                post = Post.objects.get(slug=slug)
                if post.status == 'published':
                    return 0.8
            except Post.DoesNotExist:
                pass
        elif obj.startswith('product:'):
            slug = obj.replace('product:', '')
            try:
                product = Product.objects.get(slug=slug)
                if product.featured:
                    return 0.7
            except Product.DoesNotExist:
                pass
        return 0.6

    def changefreq(self, obj):
        # Featured products and blog posts change less frequently
        if obj.startswith('blog:post_'):
            slug = obj.replace('blog:post_', '')
            try:
                post = Post.objects.get(slug=slug)
                if post.status == 'published':
                    return 'monthly'
            except Post.DoesNotExist:
                pass
        elif obj.startswith('product:'):
            slug = obj.replace('product:', '')
            try:
                product = Product.objects.get(slug=slug)
                if product.featured:
                    return 'monthly'
            except Product.DoesNotExist:
                pass
        return 'weekly'

    def lastmod(self, obj):
        if obj.startswith('blog:post_'):
            slug = obj.replace('blog:post_', '')
            try:
                post = Post.objects.get(slug=slug)
                return post.updated_at.date()
            except Post.DoesNotExist:
                pass
        elif obj.startswith('product:'):
            slug = obj.replace('product:', '')
            try:
                product = Product.objects.get(slug=slug)
                return product.updated_at.date()
            except Product.DoesNotExist:
                pass
        return datetime.now().date()
