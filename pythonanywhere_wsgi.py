"""
WSGI entry point for a PythonAnywhere web app.

PythonAnywhere -> Web tab -> "WSGI configuration file":

    /home/<username>/AI-based-Attendance-System/pythonanywhere_wsgi.py

Every setting comes from the .env file next to this script. Copy this file
plus .env to the server, fill in the CHANGE_ME lines in .env, and nothing else
needs editing here.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PROJECT_ROOT / "attendance_system"

# PythonAnywhere runs the WSGI file with the project directory as CWD, but do
# not rely on that.
os.chdir(PROJECT_ROOT)

# The app package lives in attendance_system/ and is imported as `config` and
# `apps`, so that directory has to be first on the path.
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# An explicit DJANGO_SETTINGS_MODULE in the PythonAnywhere "Environment
# variables" box wins; otherwise use production settings. This file is only
# ever the production entry point, so there is no development fallback here.
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.production",
)

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
