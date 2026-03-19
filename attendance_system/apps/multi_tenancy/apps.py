from django.apps import AppConfig


class MultiTenancyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.multi_tenancy'
    verbose_name = 'Multi-Tenancy & Licensing'
    
    def ready(self):
        import apps.multi_tenancy.signals