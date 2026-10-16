"""WSGI entry point for a PythonAnywhere web app.

Set the PythonAnywhere WSGI configuration file to this file and keep the
environment values in a private ``.env`` file in the project root.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PROJECT_ROOT / "attendance_system"

os.chdir(PROJECT_ROOT)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.production",
)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
