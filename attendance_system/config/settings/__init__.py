"""
Settings package for AI-based Attendance System.

Environment-based settings loading:
- Development: Use DJANGO_SETTINGS_MODULE=config.settings.development
- Production: Use DJANGO_SETTINGS_MODULE=config.settings.production

Default is development if DJANGO_ENV is not set.
"""
import os

# Determine which settings to use based on environment
env = os.getenv('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *
