"""
ASGI config for attendance_system project.
Exposes ASGI callable as module-level variable named ``application``.
Supports both HTTP and WebSocket protocols.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Use environment variable to switch between dev and prod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Initialize Django ASGI application early to ensure apps are loaded
django_asgi_app = get_asgi_application()

# Import routing after Django is initialized
from config.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
