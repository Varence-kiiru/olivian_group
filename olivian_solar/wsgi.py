"""
WSGI config for olivian_solar project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import django
from django.apps import apps

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olivian_solar.settings')

# Check if Django apps are already populated (e.g., by ASGI application)
if not apps.ready:
    django.setup()

application = get_wsgi_application()
