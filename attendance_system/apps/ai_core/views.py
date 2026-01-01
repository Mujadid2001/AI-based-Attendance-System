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
    
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    @action(detail=False, methods=['post'], url_path='register-face')
    def register_face(self, request):
        """
        Register student face.
        Only admin/teacher can register faces for students.
        Accepts one image at a time. Call multiple times for multiple images (max 5).
        """
        image_file = request.FILES.get('image')
        student_id = request.data.get('student_id')
        
        if not image_file:
            return Response(
                {'error': _('Image file is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate image file size (max 7MB)
        if image_file.size > 7 * 1024 * 1024:
            return Response(
                {'error': _('Image file size must be less than 7MB.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Only admin/teacher can register faces
            if not student_id:
                return Response(
                    {'error': _('student_id (roll number) is required.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # student_id is actually the roll_number from frontend
            student = StudentProfile.objects.get(roll_number=student_id)
                
            # Check maximum images limit (5 images)
            from apps.student.models import StudentFaceImage
            existing_images = StudentFaceImage.objects.filter(student=student).count()
            if existing_images >= 5:
                return Response(
                    {'error': _('Maximum 5 face images allowed per student.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': _('Student not found. Please check the roll number.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Register face
        ai_manager = get_ai_manager()
        result = ai_manager.register_student_face(image_file, student)
        
        if result['success']:
            return Response(
                {
                    'message': result['message'],
                    'images_count': StudentFaceImage.objects.filter(student=student).count()
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': result['message']},
                status=status.HTTP_400_BAD_REQUEST
            )


class FaceRecognitionViewSet(viewsets.ViewSet):
    """ViewSet for face recognition and attendance marking."""
    
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    @action(detail=False, methods=['post'], url_path='recognize-and-mark-attendance')
    def recognize_and_mark_attendance(self, request):
        """
        Recognize student face and automatically mark attendance.
        Only admin/teacher can mark attendance.
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
    
    @action(detail=False, methods=['post'], url_path='recognize-only')
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
    
    @action(detail=False, methods=['post'], url_path='bulk-recognize-attendance')
    def bulk_recognize_attendance(self, request):
        """
        Process multiple face recognition images and mark attendance in bulk.
        Marks recognized students as present and unrecognized as absent.
        """
        session_id = request.data.get('session_id')
        images = request.FILES.getlist('images')
        
        if not session_id:
            return Response(
                {'error': _('session_id is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not images:
            return Response(
                {'error': _('At least one image is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = AttendanceSession.objects.get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'error': _('Attendance session not found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all enrolled students for this course
        from apps.student.models import Enrollment
        enrolled_students = Enrollment.objects.filter(
            course=session.course,
            is_active=True
        ).select_related('student', 'student__user')
        
        recognized_students = set()
        recognition_results = []
        ai_manager = get_ai_manager()
        
        # Process each image
        for image_file in images:
            result = ai_manager.recognize_student_face(image_file)
            
            if result['success']:
                student_id = int(result['student_id'])
                recognized_students.add(student_id)
                recognition_results.append({
                    'student_id': student_id,
                    'student_name': result.get('student'),
                    'confidence': result['confidence'],
                    'recognized': True
                })
        
        # Mark attendance for all enrolled students
        marked_present = 0
        marked_absent = 0
        already_marked = 0
        
        for enrollment in enrolled_students:
            student = enrollment.student
            student_user_id = student.user.id
            
            # Check if already marked
            existing = Attendance.objects.filter(
                session=session,
                student=student
            ).first()
            
            if existing:
                already_marked += 1
                continue
            
            # Determine status based on recognition
            if student_user_id in recognized_students:
                attendance_status = Attendance.Status.PRESENT
                marked_present += 1
            else:
                attendance_status = Attendance.Status.ABSENT
                marked_absent += 1
            
            # Create attendance record
            Attendance.objects.create(
                session=session,
                student=student,
                status=attendance_status,
                check_in_time=timezone.now().time(),
                check_in_method='face_recognition' if attendance_status == Attendance.Status.PRESENT else 'auto_absent',
                confidence_score=None if attendance_status == Attendance.Status.ABSENT else 0.85,
                liveness_verified=attendance_status == Attendance.Status.PRESENT,
                recorded_by=request.user
            )
        
        logger.info(f"Bulk attendance completed: {marked_present} present, {marked_absent} absent, {already_marked} already marked")
        
        return Response(
            {
                'message': _('Bulk attendance completed successfully.'),
                'summary': {
                    'total_enrolled': enrolled_students.count(),
                    'marked_present': marked_present,
                    'marked_absent': marked_absent,
                    'already_marked': already_marked,
                    'recognized_faces': len(recognized_students)
                },
                'recognized_students': recognition_results
            },
            status=status.HTTP_201_CREATED
        )


class AIConfigurationViewSet(viewsets.ViewSet):
    """ViewSet for AI configuration (admin only)."""
    
    permission_classes = [IsAuthenticated]
    
    def check_permissions(self, request):
        """Check admin permissions."""
        if not request.user.is_admin():
            self.permission_denied(request)
        super().check_permissions(request)
    
    @action(detail=False, methods=['post'], url_path='set-confidence-threshold')
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
    
    @action(detail=False, methods=['post'], url_path='load-training-data')
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
    
    @action(detail=False, methods=['post'], url_path='save-training-data')
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


