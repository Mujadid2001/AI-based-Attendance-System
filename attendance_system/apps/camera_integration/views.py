"""Views for Camera Integration."""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes as deco_permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings
from apps.authentication.permissions import IsAdminOrTeacher
from utils.network import get_server_base_url, get_accessible_ip_info
from apps.ai_core.services import get_ai_manager
from apps.student.models import StudentProfile
from apps.attendance.models import Attendance, AttendanceSession
from .models import ExternalCameraSource, CameraStreamSession
from .serializers import (
    ExternalCameraSourceSerializer,
    ExternalCameraSourceCreateSerializer,
    CameraStreamSessionSerializer,
    ExternalCameraFrameSerializer
)
import base64

logger = logging.getLogger(__name__)


class ExternalCameraViewSet(viewsets.ModelViewSet):
    """ViewSet for managing external camera sources."""
    
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    serializer_class = ExternalCameraSourceSerializer
    
    def get_queryset(self):
        """Filter camera sources by created user."""
        user = self.request.user
        if user.is_admin():
            return ExternalCameraSource.objects.all()
        return ExternalCameraSource.objects.filter(created_by=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExternalCameraSourceCreateSerializer
        return ExternalCameraSourceSerializer
    
    @action(detail=True, methods=['get'], url_path='qr-code')
    def qr_code(self, request, pk=None):
        """
        Generate QR code for mobile camera pairing.
        
        Automatically detects the best accessible URL:
        - Uses SERVER_BASE_URL if set in settings (production)
        - Auto-detects local network IP in development
        - Falls back to request-based URL if needed
        """
        camera_source = self.get_object()
        
        try:
            import qrcode
            from io import BytesIO
            from PIL import Image
            
            # Use improved network detection
            base_url = get_server_base_url(
                request=request,
                force_detect=getattr(settings, 'FORCE_DYNAMIC_IP_DETECTION', False)
            )
            
            # Generate camera URL with token
            camera_url = f"{base_url}/camera.html?id={camera_source.id}&token={camera_source.access_token}"
            
            logger.info(f"Generating QR code for camera {camera_source.id}: {camera_url}")
            
            # Generate QR code with error correction
            qr = qrcode.QRCode(
                version=1,  # Auto-size
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(camera_url)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to BytesIO
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='image/png')
            response['Content-Disposition'] = f'inline; filename="camera_qr_{camera_source.id}.png"'
            response['X-Camera-URL'] = camera_url  # Include in header for debugging
            return response
            
        except ImportError as ie:
            logger.error(f"Import error generating QR code: {ie}", exc_info=True)
            return Response(
                {'error': _('QR code library not properly installed. Install: pip install qrcode[pil]')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error generating QR code: {e}", exc_info=True)
            return Response(
                {'error': _('Failed to generate QR code.'), 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """Toggle camera source enabled/disabled status."""
        camera_source = self.get_object()
        camera_source.is_enabled = not camera_source.is_enabled
        camera_source.save()
        
        return Response({
            'message': _('Camera status updated.'),
            'is_enabled': camera_source.is_enabled
        })
    
    @action(detail=False, methods=['get'], url_path='network-info')
    def network_info(self, request):
        """
        Diagnostic endpoint to check network configuration.
        Only available in DEBUG mode for security.
        
        Returns detected IPs, network interfaces, and current settings.
        Useful for troubleshooting mobile device connectivity issues.
        """
        if not settings.DEBUG:
            return Response(
                {'error': 'This endpoint is only available in DEBUG mode'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get comprehensive network information
        info = get_accessible_ip_info()
        info['server_base_url'] = get_server_base_url(request=request)
        info['settings'] = {
            'SERVER_BASE_URL': getattr(settings, 'SERVER_BASE_URL', None),
            'SERVER_PORT': getattr(settings, 'SERVER_PORT', '8000'),
            'FORCE_DYNAMIC_IP_DETECTION': getattr(settings, 'FORCE_DYNAMIC_IP_DETECTION', False),
            'DEBUG': settings.DEBUG,
            'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,
        }
        
        return Response(info)
    
    @action(detail=False, methods=['post'], url_path='upload-frame')
    @deco_permission_classes([AllowAny])
    def upload_frame(self, request):
        """
        Receive frame from external camera source.
        Requires access_token for authentication.
        """
        access_token = request.data.get('access_token') or request.query_params.get('token')
        
        if not access_token:
            return Response(
                {'error': _('access_token is required.')},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            camera_source = ExternalCameraSource.objects.get(
                access_token=access_token,
                is_enabled=True
            )
        except ExternalCameraSource.DoesNotExist:
            return Response(
                {'error': _('Invalid or disabled camera source.')},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = ExternalCameraFrameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = serializer.validated_data['image']
        session_id = serializer.validated_data.get('session_id')
        attendance_session_id = serializer.validated_data.get('attendance_session_id')
        
        # Store latest frame in cache for live streaming to laptop (30 second TTL)
        try:
            image_file.seek(0)
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            cache_key = f'mobile_camera_frame_{camera_source.id}'
            cache.set(cache_key, image_base64, timeout=30)
            image_file.seek(0)  # Reset for face recognition
        except Exception as e:
            logger.error(f"Error caching frame: {e}")
        
        # Update camera status
        camera_source.status = ExternalCameraSource.CameraStatus.ACTIVE
        camera_source.last_connected = timezone.now()
        if request.META.get('REMOTE_ADDR'):
            camera_source.ip_address = request.META.get('REMOTE_ADDR')
        if request.META.get('HTTP_USER_AGENT'):
            camera_source.user_agent = request.META.get('HTTP_USER_AGENT')
        camera_source.save()
        
        # Get or create stream session
        stream_session = None
        if session_id:
            try:
                stream_session = CameraStreamSession.objects.get(
                    id=session_id,
                    camera_source=camera_source,
                    ended_at__isnull=True
                )
                stream_session.frames_received += 1
                stream_session.save()
            except CameraStreamSession.DoesNotExist:
                pass
        
        # Recognize face
        ai_manager = get_ai_manager()
        result = ai_manager.recognize_student_face(image_file)
        
        if stream_session:
            stream_session.faces_detected += 1
            if result['success']:
                stream_session.faces_recognized += 1
            stream_session.save()
        
        if not result['success']:
            return Response({
                'success': False,
                'error': result.get('error', 'Recognition failed'),
                'face_detected': result.get('face_detected', False)
            }, status=status.HTTP_200_OK)
        
        response_data = {
            'success': True,
            'student': result.get('student'),
            'student_id': result.get('student_id'),
            'confidence': result['confidence'],
            'face_detected': True
        }
        
        # Auto-mark attendance if enabled and attendance session provided
        if camera_source.auto_mark_attendance and attendance_session_id:
            try:
                attendance_session = AttendanceSession.objects.get(id=attendance_session_id)
                student = StudentProfile.objects.get(user_id=int(result['student_id']))
                
                # Check if already marked
                existing = Attendance.objects.filter(
                    session=attendance_session,
                    student=student
                ).first()
                
                if not existing:
                    attendance = Attendance.objects.create(
                        session=attendance_session,
                        student=student,
                        status=Attendance.Status.PRESENT,
                        check_in_time=timezone.now().time(),
                        check_in_method='external_camera',
                        confidence_score=result['confidence'],
                        liveness_verified=True,
                        recorded_by=camera_source.created_by
                    )
                    
                    if stream_session:
                        stream_session.attendance_marked += 1
                        stream_session.save()
                    
                    response_data['attendance_marked'] = True
                    response_data['attendance_id'] = attendance.id
                else:
                    response_data['attendance_marked'] = False
                    response_data['message'] = 'Attendance already recorded'
                    
            except (AttendanceSession.DoesNotExist, StudentProfile.DoesNotExist) as e:
                logger.error(f"Error marking attendance: {e}")
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='start-session')
    def start_session(self, request, pk=None):
        """Start a new streaming session for this camera."""
        camera_source = self.get_object()
        attendance_session_id = request.data.get('attendance_session_id')
        
        # End any existing active sessions
        CameraStreamSession.objects.filter(
            camera_source=camera_source,
            ended_at__isnull=True
        ).update(ended_at=timezone.now())
        
        # Create new session
        session_data = {'camera_source': camera_source}
        if attendance_session_id:
            try:
                attendance_session = AttendanceSession.objects.get(id=attendance_session_id)
                session_data['attendance_session'] = attendance_session
            except AttendanceSession.DoesNotExist:
                pass
        
        session = CameraStreamSession.objects.create(**session_data)
        
        serializer = CameraStreamSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='end-session')
    def end_session(self, request, pk=None):
        """End active streaming session for this camera."""
        camera_source = self.get_object()
        session_id = request.data.get('session_id')
        
        if session_id:
            try:
                session = CameraStreamSession.objects.get(
                    id=session_id,
                    camera_source=camera_source
                )
                session.ended_at = timezone.now()
                session.save()
                
                serializer = CameraStreamSessionSerializer(session)
                return Response(serializer.data)
            except CameraStreamSession.DoesNotExist:
                return Response(
                    {'error': _('Session not found.')},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # End all active sessions
            updated = CameraStreamSession.objects.filter(
                camera_source=camera_source,
                ended_at__isnull=True
            ).update(ended_at=timezone.now())
            
            return Response({
                'message': _('Sessions ended.'),
                'count': updated
            })
    
    @action(detail=False, methods=['get'], url_path='sessions')
    def list_sessions(self, request):
        """List all camera stream sessions."""
        user = request.user
        
        if user.is_admin():
            sessions = CameraStreamSession.objects.all()
        else:
            sessions = CameraStreamSession.objects.filter(camera_source__created_by=user)
        
        # Filter by camera_source if provided
        camera_id = request.query_params.get('camera_id')
        if camera_id:
            sessions = sessions.filter(camera_source_id=camera_id)
        
        serializer = CameraStreamSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='latest-frame')
    @deco_permission_classes([IsAuthenticated])
    def latest_frame(self, request, pk=None):
        """
        Get the latest frame from a mobile camera.
        Used by laptop browser to display live mobile camera feed.
        """
        camera_source = self.get_object()
        
        # Get latest frame from cache
        cache_key = f'mobile_camera_frame_{camera_source.id}'
        frame_data = cache.get(cache_key)
        
        if not frame_data:
            # Return placeholder image
            return HttpResponse(
                b'',
                content_type='image/jpeg',
                status=status.HTTP_204_NO_CONTENT
            )
        
        # frame_data is base64 encoded image
        try:
            image_bytes = base64.b64decode(frame_data)
            response = HttpResponse(image_bytes, content_type='image/jpeg')
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        except Exception as e:
            logger.error(f"Error decoding frame: {e}")
            return HttpResponse(b'', content_type='image/jpeg', status=status.HTTP_204_NO_CONTENT)
