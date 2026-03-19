from django.apps import AppConfig


class EnterpriseSecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.enterprise_security'
    verbose_name = 'Enterprise Security'
    
    def ready(self):
        import apps.enterprise_security.signals