"""
Development settings for AI-based Attendance System.

Everything here is driven by the DEBUG / database / email flags in the
project-root .env file, so local development and the PythonAnywhere
deployment share exactly one configuration surface.
"""
from decouple import config

from .base import *  # noqa: F401,F403
from .app_settings import *  # noqa: F401,F403

# DEBUG comes from .env (see base.py). Nothing is hard-coded here, so
# flipping DEBUG in .env is all it takes.

if DEBUG:
    ALLOWED_HOSTS = config(
        'ALLOWED_HOSTS',
        default='localhost,127.0.0.1,0.0.0.0',
        cast=lambda v: [s.strip() for s in v.split(',') if s.strip()],
    )
else:
    # Never run the dev module with DEBUG off: production.py handles that.
    raise RuntimeError(
        'config.settings.development requires DEBUG=True in your .env file. '
        'Use DJANGO_SETTINGS_MODULE=config.settings.production instead.'
    )

# HTTPS is a pain while developing over plain http, so keep it off unless
# DEBUG was explicitly turned off for a production smoke test.
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config('CSRF_TRUSTED_ORIGINS', default='').split(',')
    if origin.strip()
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config(
        'CORS_ALLOWED_ORIGINS',
        default='http://localhost:3000,http://127.0.0.1:3000,'
                'http://localhost:5173,http://127.0.0.1:5173',
    ).split(',')
    if origin.strip()
]
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)

# dev server / Vite origins
INTERNAL_IPS = ['127.0.0.1', '::1']

# The Django admin's browsable pages and DRF's browsable API are useful while
# developing, and never enabled in production.
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
