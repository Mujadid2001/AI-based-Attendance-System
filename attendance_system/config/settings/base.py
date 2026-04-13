"""
Base settings for AI-based Attendance System - Backend API Only.
These settings are shared between development and production.
Frontend will be implemented separately in React.
"""
import os
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

# Validate SECRET_KEY in production
if not config('DEBUG', default=True, cast=bool):
    if SECRET_KEY.startswith('django-insecure-') or len(SECRET_KEY) < 50:
        raise ValueError(
            'CRITICAL: Invalid SECRET_KEY for production. '
            'Generate a strong key: '
            'python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
        )

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
    'corsheaders',  # For frontend-backend communication
    'channels',  # WebSocket support
    # 'silk',  # Optional: install django-silk for profiling
    # 'drf_spectacular',  # Optional: install drf-spectacular for API docs 
    
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

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(
                config('REDIS_HOST', default='127.0.0.1'),
                config('REDIS_PORT', default=6379, cast=int)
            )],
        },
    },
}

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
SESSION_COOKIE_SECURE = not config('DEBUG', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = config('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=True, cast=bool)

# CSRF protection
CSRF_COOKIE_SECURE = not config('DEBUG', default=True, cast=bool)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='attendance_system'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='5432', cast=str),
        'OPTIONS': {
            'sslmode': 'prefer',
        },
    }
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{config('REDIS_HOST', default='127.0.0.1')}:{config('REDIS_PORT', default=6379, cast=int)}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
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

# Static files (for Django admin only)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (user uploads - face images, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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


# REST Framework configuration for API-only backend
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For Django admin
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Changed from IsAuthenticated - let actions specify permissions
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Optional: disable in production
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'NON_FIELD_ERRORS_KEY': 'error',
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
}

# JWT Configuration
from datetime import timedelta

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

# Database Configuration - Must be set in .env file
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME') if config('DB_ENGINE') != 'django.db.backends.sqlite3' else os.path.join(BASE_DIR, config('DB_NAME')),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
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
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')

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