"""
API views for facial recognition and AI operations.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from apps.ai_core.services import get_ai_manager
from apps.authentication.permissions import IsAdminOrTeacher, IsStudent
from apps.student.models import StudentProfile
from apps.attendance.models import Attendance, AttendanceSession
from django.utils import timezone

logger = logging.getLogger(__name__)


class FaceRegistrationViewSet(viewsets.ViewSet):
    """ViewSet for face registration operations."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def register_face(self, request):
        """
        Register student face.
        Student can register their own face, admin/teacher can register for others.
        """
        image_file = request.FILES.get('image')
        student_id = request.data.get('student_id')
        
        if not image_file:
            return Response(
                {'error': _('Image file is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Determine which student to register
            if request.user.is_student():
                student = StudentProfile.objects.get(user=request.user)
            else:
                if not student_id:
                    return Response(
                        {'error': _('student_id is required for admin/teacher.')},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                student = StudentProfile.objects.get(id=student_id)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': _('Student not found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Register face
        ai_manager = get_ai_manager()
        result = ai_manager.register_student_face(image_file, student)
        
        if result['success']:
            return Response(
                {'message': result['message']},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': result['message']},
                status=status.HTTP_400_BAD_REQUEST
            )


class FaceRecognitionViewSet(viewsets.ViewSet):
    """ViewSet for face recognition and attendance marking."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def recognize_and_mark_attendance(self, request):
        """
        Recognize student face and automatically mark attendance.
        """
        image_file = request.FILES.get('image')
        session_id = request.data.get('session_id')
        
        if not image_file:
            return Response(
                {'error': _('Image file is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not session_id:
            return Response(
                {'error': _('session_id is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = AttendanceSession.objects.get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'error': _('Attendance session not found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Recognize face
        ai_manager = get_ai_manager()
        recognition_result = ai_manager.recognize_student_face(image_file)
        
        if not recognition_result['success']:
            ai_manager.get_voice_notifier().notify_face_not_recognized()
            return Response(
                {
                    'error': recognition_result.get('error', 'Recognition failed'),
                    'face_detected': recognition_result.get('face_detected', False)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        student = StudentProfile.objects.get(
            user_id=int(recognition_result['student_id'])
        )
        confidence = recognition_result['confidence']
        
        # Check if already marked
        existing = Attendance.objects.filter(
            session=session,
            student=student
        ).first()
        
        if existing:
            ai_manager.get_voice_notifier().notify_already_recorded()
            return Response(
                {
                    'message': _('Attendance already recorded.'),
                    'student': recognition_result['student'],
                    'confidence': confidence
                },
                status=status.HTTP_200_OK
            )
        
        # Mark attendance
        attendance = Attendance.objects.create(
            session=session,
            student=student,
            status=Attendance.Status.PRESENT,
            check_in_time=timezone.now().time(),
            check_in_method='face_recognition',
            confidence_score=confidence,
            liveness_verified=True,
            recorded_by=request.user
        )
        
        # Voice notification
        ai_manager.get_voice_notifier().notify_present()
        
        logger.info(f"Attendance marked: {attendance}")
        
        return Response(
            {
                'message': _('Attendance marked successfully.'),
                'student': recognition_result['student'],
                'confidence': confidence,
                'attendance_id': attendance.id
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'])
    def recognize_only(self, request):
        """
        Only recognize face without marking attendance.
        """
        image_file = request.FILES.get('image')
        
        if not image_file:
            return Response(
                {'error': _('Image file is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Recognize face
        ai_manager = get_ai_manager()
        result = ai_manager.recognize_student_face(image_file)
        
        if result['success']:
            return Response(
                {
                    'message': _('Face recognized successfully.'),
                    'student': result.get('student'),
                    'confidence': result['confidence']
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': result.get('error', 'Recognition failed')},
                status=status.HTTP_400_BAD_REQUEST
            )


class AIConfigurationViewSet(viewsets.ViewSet):
    """ViewSet for AI configuration (admin only)."""
    
    permission_classes = [IsAuthenticated]
    
    def check_permissions(self, request):
        """Check admin permissions."""
        if not request.user.is_admin():
            self.permission_denied(request)
        super().check_permissions(request)
    
    @action(detail=False, methods=['post'])
    def set_confidence_threshold(self, request):
        """Set face recognition confidence threshold."""
        threshold = request.data.get('threshold')
        
        try:
            threshold = float(threshold)
            if not (0 <= threshold <= 1):
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': _('Threshold must be between 0 and 1.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ai_manager = get_ai_manager()
        if ai_manager.set_confidence_threshold(threshold):
            return Response(
                {'message': _('Confidence threshold updated.'),
                 'threshold': threshold},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': _('Failed to update threshold.')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def load_training_data(self, request):
        """Load all student faces into recognition pipeline."""
        ai_manager = get_ai_manager()
        if ai_manager.load_all_student_faces():
            return Response(
                {'message': _('Training data loaded successfully.')},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': _('Failed to load training data.')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def save_training_data(self, request):
        """Save current training data to disk."""
        ai_manager = get_ai_manager()
        if ai_manager.save_training_data():
            return Response(
                {'message': _('Training data saved successfully.')},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': _('Failed to save training data.')},
                status=status.HTTP_400_BAD_REQUEST
            )
