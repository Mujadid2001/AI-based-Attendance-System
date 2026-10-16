"""
Production settings - tuned for a PythonAnywhere web app.

PythonAnywhere gives you exactly three things: a web process, a MySQL/MariaDB
server and a place on disk. There is no Docker, no nginx, no systemd, no Redis
and no long-running worker. Everything below assumes that, and every external
dependency is optional and read from .env.
"""
import os
import sys

from decouple import config

from .base import *  # noqa: F401,F403
from .app_settings import *  # noqa: F401,F403

# base.py already resolved DEBUG from .env and refused to boot without a real
# SECRET_KEY / ENCRYPTION_KEY when DEBUG is off. Keep the local name so the
# rest of the file reads naturally.
DEBUG = False

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()],
)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()],
)

# ----------------------------------------------------------------------------
# HTTPS
# ----------------------------------------------------------------------------
# PythonAnywhere terminates TLS and forwards X-Forwarded-Proto. base.py sets
# SECURE_PROXY_SSL_HEADER, so SECURE_SSL_REDIRECT=True redirects to https
# exactly once instead of looping forever.
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)

# A stock HSTS preload (31536000 + subdomains + preload) is effectively
# irreversible in a browser cache. Start at 0 and only turn it on once the
# domain is definitely https-only everywhere.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# ----------------------------------------------------------------------------
# CORS
# ----------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config('CORS_ALLOWED_ORIGINS', default='').split(',')
    if origin.strip()
]
if CORS_ALLOW_ALL_ORIGINS:
    raise ValueError(
        'CRITICAL: CORS_ALLOW_ALL_ORIGINS must be False in production. '
        'List your frontend origins in CORS_ALLOWED_ORIGINS instead.'
    )
if not CORS_ALLOWED_ORIGINS:
    raise ValueError(
        'CRITICAL: CORS_ALLOWED_ORIGINS is empty. The React frontend will be '
        'blocked by the browser. Set it to your frontend origin(s), '
        'comma separated.'
    )

# ----------------------------------------------------------------------------
# DATABASE
# ----------------------------------------------------------------------------
# base.py already built DATABASES from DB_ENGINE / DB_* in .env.
_engine = DATABASES['default']['ENGINE']  # noqa: F405

if _engine == 'django.db.backends.mysql':
    DATABASES['default']['CONN_MAX_AGE'] = 600  # reuse connections between requests
    DATABASES['default']['OPTIONS'] = {
        'charset': 'utf8mb4',
        'connect_timeout': 10,
    }

elif _engine == 'django.db.backends.postgresql':
    DATABASES['default']['CONN_MAX_AGE'] = 600
    DATABASES['default']['OPTIONS'] = {'connect_timeout': 10}

elif _engine == 'django.db.backends.sqlite3':
    # SQLite works on PythonAnywhere as long as the file lives inside
    # /home/<username>/, which base.py guarantees.
    #
    # Two settings matter:
    #   timeout          - wait up to 20s for a write lock instead of failing
    #                      instantly with "database is locked", which is what
    #      CONN_MAX_AGE=0  you get when two web workers write at the same moment.
    #                      Persistent connections are deliberately NOT used:
    #                      holding a SQLite handle open across requests is how
    #                      "database is locked" turns into a hang.
    import warnings

    DATABASES['default']['OPTIONS'] = {'timeout': 20}
    DATABASES['default']['CONN_MAX_AGE'] = 0

    warnings.warn(
        'Running production settings on SQLite. This works for a small '
        'deployment on a single web worker, but the whole database is locked '
        'during every write, so concurrent requests will queue or time out. '
        'Switch DB_ENGINE to django.db.backends.mysql (free on PythonAnywhere) '
        'when traffic grows.',
        RuntimeWarning,
        stacklevel=2,
    )

# ----------------------------------------------------------------------------
# STATIC FILES (Django admin CSS/JS)
# ----------------------------------------------------------------------------
# Primary path: PythonAnywhere serves /static/ straight from STATIC_ROOT once
# you map it in the Web tab. WhiteNoise is the safety net that keeps the admin
# looking right even before collectstatic has been run or if the mapping is
# missing.
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:  # noqa: F405
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # noqa: F405

_MANIFEST_BACKEND = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
_PLAIN_BACKEND = 'whitenoise.storage.CompressedStaticFilesStorage'
_manifest_path = os.path.join(STATIC_ROOT, 'staticfiles.json')  # noqa: F405
_manifest_exists = os.path.isfile(_manifest_path)
# While collectstatic is running, always use the manifest backend - otherwise
# it would collect with the plain backend and never produce a manifest, and
# the next request would then be served unhashed forever.
_is_collecting = 'collectstatic' in sys.argv

if _is_collecting or _manifest_exists:
    _staticfiles_backend = _MANIFEST_BACKEND
else:
    _staticfiles_backend = _PLAIN_BACKEND
    import logging

    logging.getLogger(__name__).warning(
        '%s is missing, so hashed static filenames are disabled and a forgotten '
        '"collectstatic" would otherwise raise "Missing staticfiles manifest '
        'entry" and return a 500 on the Django admin. Run: '
        'python attendance_system/manage.py collectstatic --noinput',
        _manifest_path,
    )

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        # Hashed filenames plus long-lived cache headers, once collectstatic
        # has produced a manifest.
        'BACKEND': _staticfiles_backend,
    },
}

# ----------------------------------------------------------------------------
# MEDIA FILES (face images, profile pictures, generated reports)
# ----------------------------------------------------------------------------
# PythonAnywhere will not serve MEDIA_ROOT unless you map it in the Web tab
# (`/media/ -> /home/<username>/<project>/attendance_system/media`). If you do
# not, set SERVE_MEDIA_FILES=True in .env and Django serves them itself - not
# fast, but nothing 404s.

# ----------------------------------------------------------------------------
# SESSIONS
# ----------------------------------------------------------------------------
# Django admin signs users in with a session, so the session engine has to be
# something that works across the web workers. `db` is the only one guaranteed
# to be shared, so keep it.
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)

CSRF_COOKIE_HTTPONLY = False  # React must read the token to send it back
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS  # keep lint quiet; set above

# ----------------------------------------------------------------------------
# EMAIL
# ----------------------------------------------------------------------------
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@attendance.local')

# ----------------------------------------------------------------------------
# CACHES / CHANNEL LAYERS / CELERY
# ----------------------------------------------------------------------------
# All three are set up in base.py and degrade to in-process backends whenever
# USE_REDIS=False (the PythonAnywhere default). Celery runs eagerly, so
# `task.delay()` executes inline instead of waiting for a worker that will
# never be started.

# ----------------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------------
# PythonAnywhere shows stdout/stderr in the web app's error log, so the
# console handler is the one that matters. Files are written too, but only
# when a writable logs/ directory exists - some PaaS filesystems are read-only
# outside your home directory and a logging failure would take the whole app
# down on the first request.
_LOG_DIR = os.path.join(BASE_DIR, 'logs')  # noqa: F405
_file_handlers = {}
if os.path.isdir(_LOG_DIR) and os.access(_LOG_DIR, os.W_OK):
    _file_handlers = {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(_LOG_DIR, 'production.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 3,
            'formatter': 'verbose',
            'delay': True,
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(_LOG_DIR, 'errors.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 3,
            'formatter': 'verbose',
            'delay': True,
        },
    }

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
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        **_file_handlers,
    },
    'root': {
        'handlers': ['console', *_file_handlers],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', *_file_handlers],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', *_file_handlers],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ----------------------------------------------------------------------------
# REST FRAMEWORK
# ----------------------------------------------------------------------------
# No browsable API in production: it is dead weight and a needless information
# leak. Switch to drf-spectacular for real docs if you want them later.
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
]
