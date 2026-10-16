from django.conf import settings
from django.http import JsonResponse
from django.middleware.csrf import get_token


def get_csrf_token(request):
    """Get CSRF token for frontend."""
    return JsonResponse({'csrfToken': get_token(request)})


def get_frontend_url():
    """
    Base URL of the React frontend, without a trailing slash.

    Reads settings.FRONTEND_URL, which is populated from FRONTEND_URL in .env
    by config/settings/base.py. Callers use this to build the links inside
    password-reset, verification and approval emails, so it must resolve to the
    real deployed origin in production.
    """
    return settings.FRONTEND_URL.rstrip('/')
