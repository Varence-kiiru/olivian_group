from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, FileResponse
from django.views.generic import TemplateView
from .sitemaps import StaticSitemap, DynamicSitemap
from apps.ecommerce import views
import os

def service_worker_view(request):
    """Serve the service worker from static/js directory with proper headers"""
    sw_path = os.path.join(settings.STATIC_ROOT or os.path.join(settings.BASE_DIR, 'static'), 'js', 'sw.js')
    if os.path.exists(sw_path):
        response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
        # Allow service worker to control the entire domain
        response['Service-Worker-Allowed'] = '/'
        return response
    else:
        return HttpResponse('Service worker not found', status=404)

def sitemap_xml_view(request):
    """Custom sitemap view that generates XML directly"""
    from xml.dom import minidom

    # Create XML document
    doc = minidom.Document()

    # Root element
    urlset = doc.createElement('urlset')
    urlset.setAttribute('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    doc.appendChild(urlset)

    # Add static URLs
    static_sitemap = StaticSitemap()
    for item in static_sitemap.items():
        url_element = doc.createElement('url')
        urlset.appendChild(url_element)

        loc = doc.createElement('loc')
        loc.appendChild(doc.createTextNode(request.build_absolute_uri(static_sitemap.location(item))))
        url_element.appendChild(loc)

        lastmod = doc.createElement('lastmod')
        lastmod.appendChild(doc.createTextNode(static_sitemap.lastmod(item).isoformat()))
        url_element.appendChild(lastmod)

        changefreq = doc.createElement('changefreq')
        changefreq.appendChild(doc.createTextNode(static_sitemap.changefreq))
        url_element.appendChild(changefreq)

        priority = doc.createElement('priority')
        priority.appendChild(doc.createTextNode(str(static_sitemap.priority)))
        url_element.appendChild(priority)

    # Add dynamic URLs
    dynamic_sitemap = DynamicSitemap()
    for item in dynamic_sitemap.items():
        url_element = doc.createElement('url')
        urlset.appendChild(url_element)

        loc = doc.createElement('loc')
        loc.appendChild(doc.createTextNode(request.build_absolute_uri(dynamic_sitemap.location(item))))
        url_element.appendChild(loc)

        # Only add lastmod if the item has a valid date
        try:
            lastmod_date = dynamic_sitemap.lastmod(item)
            if lastmod_date:
                lastmod = doc.createElement('lastmod')
                lastmod.appendChild(doc.createTextNode(lastmod_date.isoformat()))
                url_element.appendChild(lastmod)
        except:
            pass

        changefreq = doc.createElement('changefreq')
        changefreq.appendChild(doc.createTextNode(dynamic_sitemap.changefreq(item)))
        url_element.appendChild(changefreq)

        priority = doc.createElement('priority')
        priority.appendChild(doc.createTextNode(str(dynamic_sitemap.priority(item))))
        url_element.appendChild(priority)

    # Return XML response
    return HttpResponse(doc.toxml(), content_type='application/xml')

urlpatterns = [
    # PWA Service Worker
    path('sw.js', service_worker_view, name='service_worker'),

    path('admin/', admin.site.urls),

    # Sitemap
    path('sitemap.xml', sitemap_xml_view, name='sitemap'),

    # Robots.txt
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    # Offline page for PWA
    path('offline.html', TemplateView.as_view(template_name='offline.html', content_type='text/html')),

    path('accounts/', include('apps.accounts.urls')),
    path('', include('apps.core.urls')),
    path('products/', include('apps.products.urls')),
    path('quotations/', include('apps.quotations.urls')),
    path('projects/', include('apps.projects.urls')),
    path('budget/', include('apps.budget.urls')),
    path('shop/', include('apps.ecommerce.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('crm/', include('apps.crm.urls')),
    path('pos/', include('apps.pos.urls')),
    path('procurement/', include('apps.procurement.urls')),
    path('financial/', include('apps.financial.urls')),
    path('api/', include('apps.core.api_urls')),
    path('blog/', include('apps.blog.urls')),
    path('chat/', include('apps.chat.urls')),
    
    # Customer-facing solar calculator
    path('solar-calculator/', include('apps.quotations.customer_urls')),
    
    # CKEditor
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),

    # Public receipt download (by receipt ID)
    path('receipts/<int:receipt_id>/download/', views.ReceiptDownloadView.as_view(), name='receipt_download'),

    # Public order tracking (no login required)
    path('track/', views.OrderTrackingView.as_view(), name='public_order_track'),
    path('track/<str:order_number>/', views.OrderTrackingView.as_view(), name='public_order_track_detail'),
    path('api/track/<str:order_number>/', views.OrderTrackingAPIView.as_view(), name='public_api_track_order'),
]

# Serve media and static files
# In development, Django serves them; in production, web server should handle them
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # For local development with DEBUG=False, still serve media files via Django
    # In production, web server should handle them
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Static files served directly by web server via symlinks
    pass

# Admin site customization
admin.site.site_header = "Olivian Group Administration"
admin.site.site_title = "Olivian Group Admin"
admin.site.index_title = "Welcome to Olivian Group Administration"
