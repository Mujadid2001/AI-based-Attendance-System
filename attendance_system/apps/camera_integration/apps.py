"""App configuration for Camera Integration."""
from django.apps import AppConfig


class CameraIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.camera_integration'
    verbose_name = 'Camera Integration'
