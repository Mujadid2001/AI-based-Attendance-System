""" 
WebSocket consumer for real-time face recognition and attendance marking.
"""
import json
import base64
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from apps.ai_core.services import get_ai_manager
from apps.attendance.services import mark_attendance
from apps.attendance.models import Attendance, AttendanceSession
from apps.student.models import StudentProfile

logger = logging.getLogger(__name__)


class AttendanceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time attendance marking via facial recognition.
    
    Accepts base64-encoded images from frontend, performs face recognition,
    and marks attendance in real-time.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Accept connection for all users (authentication handled per message)
        self.session_id = None
        await self.accept()
        
        # Send connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to attendance system'
        }))
        logger.info(f"WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(f"WebSocket disconnected: {self.channel_name} (code: {close_code})")
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket."""
        try:
            # Parse incoming data
            data = json.loads(text_data)
            message_type = data.get('type', 'recognize')
            
            if message_type == 'set_session':
                await self.handle_set_session(data)
            elif message_type == 'recognize':
                await self.handle_recognition(data)
            else:
                await self.send_error('Unknown message type')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {str(e)}", exc_info=True)
            await self.send_error(f'Server error: {str(e)}')
    
    async def handle_set_session(self, data):
        """Set the attendance session for this WebSocket connection."""
        session_id = data.get('session_id')
        
        if not session_id:
            await self.send_error('session_id is required')
            return
        
        # Verify session exists
        session_exists = await self.verify_session(session_id)
        if not session_exists:
            await self.send_error('Invalid session_id')
            return
        
        self.session_id = session_id
        await self.send(text_data=json.dumps({
            'type': 'session_set',
            'message': 'Session set successfully',
            'session_id': session_id
        }))
    
    async def handle_recognition(self, data):
        """Handle face recognition and attendance marking."""
        # Check if session is set
        if not self.session_id:
            session_id = data.get('session_id')
            if session_id:
                self.session_id = session_id
            else:
                await self.send_error('No session_id provided. Set session first.')
                return
        
        # Get image data
        image_data = data.get('image')
        if not image_data:
            await self.send_error('No image data provided')
            return
        
        try:
            # Decode base64 image
            if ',' in image_data:
                format_part, imgstr = image_data.split(';base64,')
                ext = format_part.split('/')[-1] if '/' in format_part else 'jpg'
            else:
                imgstr = image_data
                ext = 'jpg'
            
            image_bytes = base64.b64decode(imgstr)
            image_file = ContentFile(image_bytes, name=f'temp.{ext}')
            
            # Perform face recognition
            ai_manager = get_ai_manager()
            result = await database_sync_to_async(ai_manager.recognize_student_face)(image_file)
            
            if result.get('success'):
                # Mark attendance
                student_id = result['student']['id']
                confidence = result.get('confidence', 0.0)
                
                attendance, created = await self.mark_attendance_async(
                    self.session_id,
                    student_id,
                    confidence
                )
                
                if created:
                    # New attendance marked
                    response = {
                        'type': 'attendance_marked',
                        'success': True,
                        'message': 'Attendance marked successfully',
                        'student': result['student'],
                        'confidence': confidence,
                        'attendance_id': attendance.id,
                        'status': attendance.status,
                        'time': str(attendance.check_in_time)
                    }
                    
                    # Trigger voice notification
                    try:
                        await database_sync_to_async(
                            ai_manager.get_voice_notifier().notify_present
                        )()
                    except Exception as e:
                        logger.warning(f"Voice notification failed: {e}")
                else:
                    # Attendance already exists
                    response = {
                        'type': 'attendance_exists',
                        'success': False,
                        'message': 'Attendance already recorded for this session',
                        'student': result['student'],
                        'confidence': confidence,
                        'attendance_id': attendance.id,
                        'existing_time': str(attendance.check_in_time)
                    }
                    
                    try:
                        await database_sync_to_async(
                            ai_manager.get_voice_notifier().notify_already_recorded
                        )()
                    except Exception as e:
                        logger.warning(f"Voice notification failed: {e}")
                
                await self.send(text_data=json.dumps(response))
            else:
                # Face not recognized
                await self.send(text_data=json.dumps({
                    'type': 'recognition_failed',
                    'success': False,
                    'message': result.get('message', 'Face not recognized'),
                    'error': result.get('error', 'unknown')
                }))
                
                try:
                    await database_sync_to_async(
                        ai_manager.get_voice_notifier().notify_face_not_recognized
                    )()
                except Exception as e:
                    logger.warning(f"Voice notification failed: {e}")
        
        except Exception as e:
            logger.error(f"Error during recognition: {str(e)}", exc_info=True)
            await self.send_error(f'Recognition error: {str(e)}')
    
    @database_sync_to_async
    def verify_session(self, session_id):
        """Verify if attendance session exists."""
        return AttendanceSession.objects.filter(id=session_id).exists()
    
    @database_sync_to_async
    def mark_attendance_async(self, session_id, student_id, confidence):
        """Mark attendance asynchronously."""
        return mark_attendance(
            session_id=session_id,
            student_id=student_id,
            status=Attendance.Status.PRESENT,
            confidence=confidence,
            liveness=False,
            user=None  # WebSocket doesn't have authenticated user in scope by default
        )
    
    async def send_error(self, message):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'success': False,
            'message': message
        }))
