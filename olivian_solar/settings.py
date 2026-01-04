"""
Django settings for Olivian Group project.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'csp',
    'channels',
    'widget_tweaks',
    'ckeditor',
    'django_ckeditor_5',
    'ckeditor_uploader',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    'import_export',
    'mptt',
    'taggit',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.products',
    'apps.inventory',
    'apps.quotations',
    'apps.projects',
    'apps.budget',
    'apps.ecommerce',
    'apps.core',
    'apps.core.templatetags',  # Add this line
    'apps.crm',
    'apps.pos',
    'apps.procurement',
    'apps.financial',
    'apps.blog',
    'apps.chat'
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Cache Configuration
if DEBUG:
    # Disable all caching in development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
else:
    # Production cache configuration
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'apps.accounts.middleware.PasswordChangeMiddleware',
    'apps.core.middleware.DevelopmentCacheControlMiddleware',
    'apps.core.middleware.CacheControlMiddleware',  # Added for better cache control
]

# Removed aggressive page caching - let service worker handle offline caching
# CACHE_MIDDLEWARE_SECONDS, UpdateCacheMiddleware, and FetchFromCacheMiddleware have been removed

ROOT_URLCONF = 'olivian_solar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'apps.core.context_processors.company_info',
                'apps.core.context_processors.currency_info',
                'apps.core.context_processors.cart_info',
                'apps.core.context_processors.active_discounts',
                'apps.core.context_processors.google_maps_api_key',
                'csp.context_processors.nonce',
            ],
        },
    },
]

WSGI_APPLICATION = 'olivian_solar.wsgi.application'
ASGI_APPLICATION = 'olivian_solar.asgi.application'

# Database
# Use SQLite for development (MySQL can be configured via environment variables in production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Production MySQL configuration (use environment variables to enable)
if config('USE_MYSQL', default=False, cast=bool):
    try:
        import MySQLdb
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': config('DB_NAME', default='olivian_solar'),
                'USER': config('DB_USER', default='root'),
                'PASSWORD': config('DB_PASSWORD', default=''),
                'HOST': config('DB_HOST', default='localhost'),
                'PORT': config('DB_PORT', default='3306'),
                'OPTIONS': {
                    'charset': 'utf8mb4',
                    'init_command': (
                        "SET sql_mode='STRICT_TRANS_TABLES';"
                        "SET character_set_connection=utf8mb4;"
                        "SET character_set_database=utf8mb4;"
                        "SET character_set_results=utf8mb4;"
                        "SET character_set_server=utf8mb4;"
                        "SET collation_connection=utf8mb4_unicode_ci;"
                        "SET collation_database=utf8mb4_unicode_ci;"
                        "SET collation_server=utf8mb4_unicode_ci;"
                    ),
                },
            }
        }
    except ImportError:
        pass  # Keep SQLite if MySQL is not available

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailOrUsernameModelBackend',  # Custom backend for email/username login
    'django.contrib.auth.backends.ModelBackend',  # Default backend (fallback)
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#CKEditor_5 Settings
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "link", "underline", "strikethrough", "|",
            "bulletedList", "numberedList", "blockQuote", "|",
            "imageUpload", "mediaEmbed", "|",
            "undo", "redo"
        ],
        "height": 400,
        "width": "100%",
    }
}

# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = config('TIMEZONE', default='Africa/Nairobi')
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'Africa/Nairobi'  # Or your appropriate timezone


LANGUAGES = [
    ('en', 'English'),
    ('sw', 'Swahili'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Shared hosting configuration
if not DEBUG:
    # For shared hosting, media files should be served by web server
    # Place media files in public_html/media or similar public directory
    MEDIA_URL = config('MEDIA_URL', default='/media/')
    MEDIA_ROOT = config('MEDIA_ROOT', default=str(BASE_DIR.parent / 'public_html' / 'media'))

# WhiteNoise configuration for shared hosting
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email Configuration
# Choose email provider: 'sendgrid', 'mailgun', 'smtp', 'console'
EMAIL_PROVIDER = config('EMAIL_PROVIDER', default='console' if DEBUG else 'smtp')

if EMAIL_PROVIDER == 'sendgrid':
    # SendGrid Configuration
    INSTALLED_APPS.append('sendgrid-django')
    EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
    SENDGRID_API_KEY = config('SENDGRID_API_KEY', default='')
    SENDGRID_SANDBOX_MODE_IN_DEBUG = DEBUG

elif EMAIL_PROVIDER == 'mailgun':
    # Mailgun Configuration
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.mailgun.org'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = config('MAILGUN_SMTP_LOGIN', default='')
    EMAIL_HOST_PASSWORD = config('MAILGUN_SMTP_PASSWORD', default='')
    MAILGUN_API_KEY = config('MAILGUN_API_KEY', default='')

elif EMAIL_PROVIDER == 'smtp':
    # Custom SMTP Configuration
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='mail.olivian.co.ke')
    EMAIL_PORT = config('EMAIL_PORT', default=465, cast=int)
    EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=True, cast=bool)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

else:
    # Console backend for development/debugging
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Common Email Settings
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@olivian.co.ke')
EMAIL_SUBJECT_PREFIX = config('EMAIL_SUBJECT_PREFIX', default='[Olivian Solar] ')
SERVER_EMAIL = config('SERVER_EMAIL', default='server@olivian.co.ke')

# Email Templates Directory
EMAIL_TEMPLATES_DIR = BASE_DIR / 'templates' / 'emails'

# CRM Email Settings
CRM_EMAIL_FROM = config('CRM_EMAIL_FROM', default=DEFAULT_FROM_EMAIL)
CRM_EMAIL_SIGNATURE = config('CRM_EMAIL_SIGNATURE', default='Best regards,\nThe Olivian Group Team\nPhone: +254-719-728-666\nEmail: info@olivian.co.ke\nWebsite: https://olivian.co.ke')

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# CKEditor Configuration
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    },
}

# Company Settings
COMPANY_NAME = config('COMPANY_NAME', default='The Olivian Group Limited')
COMPANY_ADDRESS = config('COMPANY_ADDRESS', default='Kahawa Sukari Road, Nairobi, Kenya')
COMPANY_PHONE = config('COMPANY_PHONE', default='+254-719-728-666')
COMPANY_EMAIL = config('COMPANY_EMAIL', default='info@olivian.co.ke')
COMPANY_WEBSITE = config('COMPANY_WEBSITE', default='https://olivian.co.ke')

# Currency and Tax Settings
DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='KES')
VAT_RATE = config('VAT_RATE', default=16.0, cast=float)

# Site Configuration
SITE_URL = config('SITE_URL', default='https://olivian.co.ke')

# M-Pesa Configuration
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
MPESA_ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox')

# Social Media Configuration
FACEBOOK_APP_ID = config('FACEBOOK_APP_ID', default='544914051459824')

# Google Maps API Configuration
GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')
GOOGLE_MAPS_GEOCODING_API_KEY = config('GOOGLE_MAPS_GEOCODING_API_KEY', default=GOOGLE_MAPS_API_KEY)
GOOGLE_MAPS_EMBED_API_KEY = config('GOOGLE_MAPS_EMBED_API_KEY', default=GOOGLE_MAPS_API_KEY)

# Security Settings for Production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/dashboard/'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps.core.email_utils': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.core.views': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Content Security Policy (CSP) Configuration - django-csp 4.0 format
# Moderate CSP that allows necessary scripts while maintaining security
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'none'",),
        'script-src': (
            "'self'",
            "'unsafe-inline'",  # Allow inline scripts with nonce
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://static.cloudflareinsights.com",
            "https://fonts.googleapis.com",
            "https://embed.tawk.to",  # Allow Tawk.to chat widget script
            "https://olivian.co.ke/",  # Allow all scripts from own domain including Cloudflare CDN
            "https://maps.googleapis.com",  # Google Maps API
            "https://maps.gstatic.com",  # Google Maps static resources
        ),
        'style-src': (
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://fonts.googleapis.com",
            "https://fonts.gstatic.com",
            "https://embed.tawk.to",  # Allow Tawk.to widget styles
        ),
        'font-src': (
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdnjs.cloudflare.com",  # Font Awesome fonts
            "https://embed.tawk.to",  # Allow Tawk.to widget fonts
        ),
        'img-src': (
            "'self'",
            "data:",
            "https:",
        ),
        'connect-src': (
            "'self'",
            "https://olivian.co.ke",
            "https://embed.tawk.to",
            "wss://*.tawk.to",
            "https://*.tawk.to",
            "https://maps.googleapis.com",  # Google Maps API calls
            "https://maps.gstatic.com",  # Google Maps resources
            "https://cdn.jsdelivr.net",  # Bootstrap source maps
        ),
        'manifest-src': (
            "'self'",  # Allow PWA manifest loading
        ),
        'media-src': ("'self'", "https://embed.tawk.to"),
        'frame-src': (
            "https://www.google.com",
            "https://maps.google.com",
            "https://www.google.com/maps",
            "https://maps.googleapis.com",
        ),
        'object-src': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
    },
    'UPGRADE_INSECURE_REQUESTS': False,  # Set to True in production if using HTTPS
    'REPORT_ONLY': False,  # Set to True initially to monitor violations
}

# Backup Configuration
BACKUP_ROOT = BASE_DIR / 'backups'
BACKUP_RETENTION_DAYS = 30  # Keep backups for 30 days
MAX_BACKUP_SIZE = 100 * 1024 * 1024  # 100MB size limit for backup files
