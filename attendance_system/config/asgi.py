"""
ASGI config for attendance_system project.
"""
import os
from django.core.asgi import get_asgi_application

# Use environment variable to switch between dev and prod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_asgi_application()
