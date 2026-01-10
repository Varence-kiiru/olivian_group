"""
Development settings using SQLite
"""

from .settings import *

# Override database to use SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Debug mode
DEBUG = True

# Simple caches for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Static files storage for development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Don't require HTTPS for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

print("Using SQLite database for development")

# For development, auto-join only the 'general' room by default.
# Set to empty list [] to opt-out, or set env var CHAT_AUTO_JOIN_GENERAL_ROOMS to a comma-separated list.
from decouple import config as _config
_env_rooms = _config('CHAT_AUTO_JOIN_GENERAL_ROOMS', default='general')
CHAT_AUTO_JOIN_GENERAL_ROOMS = [r.strip() for r in _env_rooms.split(',')] if _env_rooms else None
