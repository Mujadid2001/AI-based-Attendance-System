from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.conf import settings

def get_csrf_token(request):
    """Get CSRF token for frontend."""
    return JsonResponse({'csrfToken': get_token(request)})


def get_frontend_url():
    """Get frontend base URL from settings or environment."""
    # Try to get from settings first, fallback to environment variable
    frontend_url = getattr(settings, 'FRONTEND_URL', None)
    if not frontend_url:
        from decouple import config
        frontend_url = config('FRONTEND_URL', default='http://localhost:3000')
    return frontend_url.rstrip('/')

