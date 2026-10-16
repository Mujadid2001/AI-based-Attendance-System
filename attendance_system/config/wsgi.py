"""
WSGI config for attendance_system project.
"""
import os
from django.core.wsgi import get_wsgi_application

# Use the configured settings module, falling back to development locally.
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.development'),
)
application = get_wsgi_application()
