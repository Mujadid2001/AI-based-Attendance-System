"""
WebSocket consumers for real-time camera streaming.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class CameraStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time camera frame streaming.
    Clients connect to receive frames pushed from mobile cameras.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.camera_id = self.scope['url_route']['kwargs']['camera_id']
        self.room_group_name = f'camera_{self.camera_id}'
        
        logger.info(f"🔌 WebSocket connection attempt for camera: {self.camera_id}")
        
        # Verify camera exists
        camera_exists = await self.check_camera_exists(self.camera_id)
        if not camera_exists:
            logger.warning(f"❌ Camera {self.camera_id} does not exist or is disabled")
            await self.close(code=4004)
            return
        
        # Join camera room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"✅ WebSocket connected for camera: {self.camera_id}, group: {self.room_group_name}")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'connected',
            'camera_id': self.camera_id
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave camera room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for camera: {self.camera_id}, code: {close_code}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client (laptop)."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to keepalive ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
    
    async def camera_frame(self, event):
        """
        Handle frame push from channel layer.
        Called when a frame is uploaded and pushed via channel layer.
        """
        await self.send(text_data=json.dumps({
            'type': 'frame',
            'frame': event['frame'],
            'timestamp': event['timestamp'],
            'camera_id': event['camera_id'],
            'camera_name': event.get('camera_name', '')
        }))
    
    async def recognition_result(self, event):
        """
        Handle recognition result broadcast from channel layer.
        Called when face recognition is performed from mobile capture.
        """
        logger.info(f"📨 Recognition result received in WebSocket consumer for camera: {event.get('camera_id')}")
        logger.info(f"📨 Success: {event.get('success')}, Student: {event.get('student', {}).get('name', 'N/A')}")
        
        result_data = {
            'type': 'recognition_result',
            'timestamp': event['timestamp'],
            'camera_id': event['camera_id'],
            'success': event['success'],
            'message': event['message'],
            'captured_image': event.get('captured_image', '')
        }
        
        if event['success']:
            result_data['student'] = event.get('student')
            result_data['confidence'] = event.get('confidence')
        else:
            result_data['error'] = event.get('error', 'Recognition failed')
        
        logger.info(f"📤 Broadcasting recognition result to WebSocket client: success={event['success']}")
        await self.send(text_data=json.dumps(result_data))
        logger.info(f"✅ Recognition result sent to WebSocket client successfully")
    
    @database_sync_to_async
    def check_camera_exists(self, camera_id):
        """Check if camera exists in database."""
        from apps.camera_integration.models import ExternalCameraSource
        try:
            ExternalCameraSource.objects.get(id=camera_id, is_enabled=True)
            return True
        except ExternalCameraSource.DoesNotExist:
            return False
