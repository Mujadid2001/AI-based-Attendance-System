"""
Apps configuration for AI core.
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AICoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_core'
    verbose_name = 'AI Core - Facial Recognition'

    def ready(self):
        """
        Initialize AI services eagerly when Django starts.
        This ensures the first request is fast since models are pre-loaded.
        """
        # Skip initialization during migrations
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        try:
            logger.info("Starting eager initialization of AI services...")
            
            # Import and initialize AI manager
            from apps.ai_core.services import get_ai_manager
            ai_manager = get_ai_manager()
            
            # Force initialization of pipeline
            ai_manager.initialize_all_services()
            
            logger.info("AI services initialized successfully and ready for use")
        except Exception as e:
            logger.error(f"Failed to initialize AI services: {str(e)}")
            logger.info("AI services will fall back to lazy initialization")
