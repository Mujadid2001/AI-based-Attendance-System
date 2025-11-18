import json
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.ai_core.services import get_ai_manager
import base64
from django.core.files.base import ContentFile

class AttendanceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        image_data = data['image']

        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]

        session_id = data.get('session_id')
        if not session_id:
            return

        image = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        ai_manager = get_ai_manager()
        result = ai_manager.recognize_student_face(image)

        if result.get('success'):
            from apps.attendance.services import mark_attendance
            from apps.attendance.models import Attendance
            from channels.db import database_sync_to_async

            student_id = result['student']['id']

            @database_sync_to_async
            def mark_attendance_async():
                return mark_attendance(
                    session_id,
                    student_id,
                    Attendance.Status.PRESENT,
                    result['confidence'],
                    False,
                    self.scope["user"]
                )

            attendance, created = await mark_attendance_async()

            if created:
                await self.send(text_data=json.dumps({
                    'result': result
                }))
