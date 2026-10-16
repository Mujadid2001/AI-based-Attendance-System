"""
Base settings for AI-based Attendance System - Backend API Only.
These settings are shared between development and production.
Frontend will be implemented separately in React.
"""
import os
from datetime import timedelta
from pathlib import Path

from decouple import config

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Must be set in .env file - no default fallback
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-dev-key-change-in-production'
)

# Single source of truth for DEBUG. Every settings module reads this one flag
# instead of hard-coding its own value.
DEBUG = config('DEBUG', default=True, cast=bool)

# Validate SECRET_KEY in production
if not DEBUG:
    if SECRET_KEY.startswith('django-insecure-') or len(SECRET_KEY) < 50:
        raise ValueError(
            'CRITICAL: Invalid SECRET_KEY for production. '
            'Generate a strong key: '
            'python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
        )
    ENCRYPTION_KEY_CHECK = config(
        'ENCRYPTION_KEY',
        default='your-32-byte-base64-encoded-encryption-key-here',
    )
    try:
        from cryptography.fernet import Fernet

        Fernet(ENCRYPTION_KEY_CHECK.encode())
    except Exception as exc:
        raise ValueError(
            'CRITICAL: ENCRYPTION_KEY is not a valid Fernet key. '
            'Generate one with: '
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        ) from exc

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third Party Apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # required by ROTATE_REFRESH_TOKENS
    'corsheaders',  # For frontend-backend communication
    'channels',  # WebSocket support

    # Custom Apps
    'apps.authentication',
    'apps.student',
    'apps.attendance',
    'apps.ai_core',
    'apps.camera_integration',
    'apps.enterprise_security',  # Enterprise-level security
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.enterprise_security.middleware.RateLimitMiddleware',  # Enterprise rate limiting
    'apps.enterprise_security.middleware.SecurityAuditMiddleware',  # Security auditing
    'apps.enterprise_security.middleware.DataProtectionMiddleware',  # Data protection
    'corsheaders.middleware.CorsMiddleware',  # Must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'silk.middleware.SilkyMiddleware',  # Optional: uncomment if silk is installed 
]

ROOT_URLCONF = 'config.urls'

# Template configuration for Django admin only
# Frontend is completely separate and doesn't use Django templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.admin_dashboard_stats',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ASGI Application for WebSocket support
ASGI_APPLICATION = 'config.asgi.application'

# ==============================================================================
# ENTERPRISE SECURITY CONFIGURATION
# ==============================================================================

# Encryption key for sensitive data (must be 32 url-safe base64-encoded bytes)
ENCRYPTION_KEY = config(
    'ENCRYPTION_KEY',
    default='your-32-byte-base64-encoded-encryption-key-here'
)

# Rate limiting settings
MAX_REQUESTS_PER_MINUTE = config('MAX_REQUESTS_PER_MINUTE', default=100, cast=int)
AUTH_RATE_LIMIT = config('AUTH_RATE_LIMIT', default=20, cast=int)
API_RATE_LIMIT = config('API_RATE_LIMIT', default=100, cast=int)
GENERAL_RATE_LIMIT = config('GENERAL_RATE_LIMIT', default=200, cast=int)

# Block suspicious requests
BLOCK_SUSPICIOUS_REQUESTS = config('BLOCK_SUSPICIOUS_REQUESTS', default=False, cast=bool)

# Session security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = config('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=True, cast=bool)

# CSRF protection
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # the JS frontends must read this cookie
CSRF_COOKIE_SAMESITE = 'Lax'

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)

# PythonAnywhere (and every other TLS-terminating proxy) forwards the original
# scheme in X-Forwarded-Proto. Without this line Django thinks every request
# arrived over plain http and SECURE_SSL_REDIRECT sends the client into an
# endless redirect loop.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# ==============================================================================
DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')


def _database_settings():
    """Build DATABASES['default'] from the environment."""
    if DB_ENGINE == 'django.db.backends.sqlite3':
        name = config('DB_NAME', default='db.sqlite3')
        path = name if os.path.isabs(name) else os.path.join(BASE_DIR, name)
        # Create the containing directory when a nested path is configured
        # (e.g. "data/db.sqlite3"). A missing directory only surfaces later as
        # "unable to open database file", which is a confusing way to find out.
        parent = os.path.dirname(path)
        if parent:
            try:
                os.makedirs(parent, exist_ok=True)
            except OSError:
                pass
        return {
            'ENGINE': DB_ENGINE,
            'NAME': path,
        }
    db = {
        'ENGINE': DB_ENGINE,
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
    if DB_ENGINE == 'django.db.backends.mysql':
        # utf8mb4 is required for emoji and other non-BMP characters in names.
        db['OPTIONS'] = {'charset': 'utf8mb4'}
    return db


DATABASES = {'default': _database_settings()}

# ==============================================================================
# REDIS / CACHE / CHANNEL LAYERS
# ==============================================================================
# PythonAnywhere has no Redis server, so USE_REDIS=False must degrade to
# in-process backends instead of pointing at a localhost Redis that never
# answers. That keeps `check`, `migrate` and every request working with zero
# external services.
USE_REDIS = config('USE_REDIS', default=False, cast=bool)
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')

if USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        }
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'attendance-system',
        }
    }
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}
    }

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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (Django admin CSS/JS)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (user uploads - face images, etc.)
MEDIA_URL = '/media/'
_configured_media_root = config('MEDIA_ROOT', default='')
MEDIA_ROOT = (
    _configured_media_root
    if _configured_media_root
    else os.path.join(BASE_DIR, 'media')
)

# Let Django serve /static/ and /media/ itself. PythonAnywhere can serve
# both from the Web tab instead, which is faster - turn these off when you
# have mapped them there. With them off you must run collectstatic first.
SERVE_STATIC_FILES = config('SERVE_STATIC_FILES', default=not DEBUG, cast=bool)
SERVE_MEDIA_FILES = config('SERVE_MEDIA_FILES', default=not DEBUG, cast=bool)

# Upload cap per request, in bytes. Keeps a single huge image from filling
# the disk and stalling every worker.
MAX_UPLOAD_SIZE_MB = config('MAX_UPLOAD_SIZE_MB', default=10, cast=int)
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Custom Authentication Backend
AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.CustomAuthenticationBackend',
]

# Email Configuration - Must be set in .env file
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@attendance-system.com')

# Base URL of the React frontend, without a trailing slash. Every link that
# gets emailed out (password reset, email verification, account approval) is
# built from this, so it must be the real deployed origin in production -
# otherwise users are sent to http://localhost:3000/reset-password.
#
# Previously this lived only in .env and was read straight from decouple in one
# place while another place hardcoded localhost, so reset emails silently
# pointed at the developer's own machine.
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000').rstrip('/')



# REST Framework configuration for API-only backend
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For Django admin
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # let each view/action set its own permission
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # removed in production
    ],
    'EXCEPTION_HANDLER': 'utils.responses.api_exception_handler',
    'NON_FIELD_ERRORS_KEY': 'error',
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Configuration for Frontend-Backend Decoupling
# SECURITY: In production, ALWAYS set CORS_ALLOWED_ORIGINS in environment variables
# DO NOT use wildcard (*) or CORS_ALLOW_ALL_ORIGINS in production
# Only list specific, trusted frontend URLs

# Development defaults - override in production with specific domains
_cors_origins_str = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://localhost:3000,https://127.0.0.1:3000,https://localhost:3001,https://127.0.0.1:3001,https://localhost:5173,https://127.0.0.1:5173',
)
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins_str.split(',') if origin.strip()]

# SECURITY: Never enable this in production - it allows ALL origins
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

# Allow credentials for JWT authentication
CORS_ALLOW_CREDENTIALS = True

# Allow all standard HTTP methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Allow all necessary headers for API communication
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ===============================================
# NETWORK CONFIGURATION FOR QR CODE GENERATION
# ===============================================

# Server Base URL for QR codes and external device integrations
# In production: Set to your public domain (e.g., https://attendance.yourdomain.com)
# In development: Leave empty for automatic local network IP detection
# In Docker: Set to host machine's LAN IP or domain
SERVER_BASE_URL = config('SERVER_BASE_URL', default=None)

# Server Port (used for dynamic IP detection when SERVER_BASE_URL is not set)
SERVER_PORT = config('SERVER_PORT', default='8000')

# Force dynamic IP detection even when SERVER_BASE_URL is set
# Useful for LAN-only production deployments where IP may change
FORCE_DYNAMIC_IP_DETECTION = config('FORCE_DYNAMIC_IP_DETECTION', default=False, cast=bool)

# ============================================================
# CELERY CONFIGURATION FOR ASYNC TASKS
# ============================================================
# PythonAnywhere gives you a web process and nothing else - no worker, no
# beat, no broker. With CELERY_TASK_ALWAYS_EAGER=True, task.delay() runs the
# task inline in the calling thread, so every feature keeps working; you just
# lose the "reply immediately, finish in the background" behaviour.
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=not USE_REDIS, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = config('CELERY_TASK_EAGER_PROPAGATES', default=False, cast=bool)

# Task settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_TASK_ACKS_LATE = True  # Task removed from queue only after successful execution
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Prevent worker from taking too many tasks at once

# Result backend settings
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour

# Timezone
CELERY_TIMEZONE = 'UTC'

# Redis & Caching settings
CELERY_ENABLE_UTC = True

# Cache timeout constants
CACHE_TIMEOUT_STUDENT_PROFILE = 3600      # 1 hour
CACHE_TIMEOUT_COURSE_DATA = 1800          # 30 minutes
CACHE_TIMEOUT_ATTENDANCE_STATS = 600      # 10 minutes
CACHE_TIMEOUT_USER_PERMISSIONS = 1800     # 30 minutes