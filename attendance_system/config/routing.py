"""
WebSocket URL routing configuration.
"""
from django.urls import path
from apps.camera_integration.consumers import CameraStreamConsumer

websocket_urlpatterns = [
    path('ws/camera/<str:camera_id>/', CameraStreamConsumer.as_asgi()),
]
