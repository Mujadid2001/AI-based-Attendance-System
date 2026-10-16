"""
Settings package for the AI Attendance System.

Available settings modules:

* ``config.settings.development``  - local development (DEBUG=True)
* ``config.settings.production``   - PythonAnywhere deployment (DEBUG=False)

Select one with the ``DJANGO_SETTINGS_MODULE`` environment variable, or by
setting it in the ``.env`` file at the project root:

    DJANGO_SETTINGS_MODULE=config.settings.production

This module deliberately contains no imports and no logic.

Django imports the *parent package* before the requested submodule, so
anything executed here runs for EVERY settings module. An earlier version did
``from .development import *``, which meant that asking for the production
settings silently loaded the development ones first - and, once development
settings started validating DEBUG, it aborted startup outright.
"""

# Intentionally empty. See the module docstring above.
