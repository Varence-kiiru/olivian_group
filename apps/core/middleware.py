"""
Additional core middleware for development and production optimizations
"""

from django.conf import settings
from django.http import HttpResponse


class DevelopmentCacheControlMiddleware:
    """
    Middleware to prevent browser caching in development environment
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only apply no-cache headers in development
        if settings.DEBUG:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response


class CacheControlMiddleware:
    """
    Middleware to set appropriate cache control headers for production
    Prioritizes live serving over caching for HTML content
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip for admin interface and API endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/api/'):
            return response

        # For HTML pages (no extension in path or ends with .html)
        if ('/' in request.path or request.path.endswith('.html')) and not request.path.startswith('/static/'):
            # Prevent browser caching of HTML pages - network-first approach
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        # For static assets, allow browser caching with service worker control
        elif request.path.startswith('/static/') or request.path.startswith('/media/'):
            # Let service worker handle caching of static assets
            if not settings.DEBUG:
                response['Cache-Control'] = 'public, max-age=86400'  # 24 hours for static files
            else:
                # In development, still allow some caching but shorter
                response['Cache-Control'] = 'public, max-age=300'  # 5 minutes in dev

        return response
