"""
Example of refactored ViewSets using the new base classes for reduced redundancy and better decoupling.
This demonstrates how to convert existing ViewSets to use the optimized base classes.
"""
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _
from apps.student.models import Course, StudentProfile, Enrollment
from apps.student.serializers import (
    CourseSerializer, StudentProfileSerializer, EnrollmentSerializer,
    EnrollmentWithStudentSerializer
)
from utils.viewsets import (
    BaseModelViewSet, TeacherAdminMixin, RoleBasedQuerysetMixin,
    BulkOperationsMixin, ExportMixin
)
from utils.responses import APIResponse
import logging

logger = logging.getLogger(__name__)


class OptimizedCourseViewSet(TeacherAdminMixin, BulkOperationsMixin, ExportMixin, BaseModelViewSet):
    """
    Optimized CourseViewSet using base classes.
    
    Demonstrates:
    - Automatic role-based permissions (TeacherAdminMixin)
    - Standardized responses (BaseModelViewSet)
    - Built-in bulk operations (BulkOperationsMixin)
    - Export capabilities (ExportMixin)
    - Role-based queryset filtering (RoleBasedQuerysetMixin)
    """
    
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'pk'
    
    # Role-based queryset methods (automatic filtering)
    def get_queryset_for_admin(self):
        """Admins see all courses."""
        return Course.objects.all()
    
    def get_queryset_for_teacher(self):
        """Teachers see courses they teach + active courses."""
        return Course.objects.filter(
            models.Q(instructor=self.request.user) | 
            models.Q(status='active')  # Using StatusMixin
        )
    
    def get_queryset_for_student(self):
        """Students see only active courses."""
        return Course.objects.filter(status='active')
    
    # Custom actions with standardized responses
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get enrolled students for a course."""
        try:
            course = self.get_object()
            enrollments = course.enrollments.filter(is_active=True)
            serializer = EnrollmentWithStudentSerializer(enrollments, many=True)
            
            return self.success_response(
                data=serializer.data,
                message=_('Students retrieved successfully.')
            )
        except Exception as e:
            logger.error(f"Error retrieving students for course {pk}: {e}")
            return self.error_response(
                message=_('Failed to retrieve students.'),
                status_code=500
            )
    
    @action(detail=True, methods=['post'])
    def enroll_student(self, request, pk=None):
        """Enroll a student in the course."""
        try:
            course = self.get_object()
            student_id = request.data.get('student_id')
            
            if not student_id:
                return self.validation_error_response(
                    errors={'student_id': _('Student ID is required.')},
                    message=_('Invalid enrollment data.')
                )
            
            student = StudentProfile.objects.get(id=student_id)
            enrollment, created = Enrollment.objects.get_or_create(
                course=course,
                student=student,
                defaults={'is_active': True, 'created_by': request.user}
            )
            
            if created:
                return self.success_response(
                    data=EnrollmentSerializer(enrollment).data,
                    message=_('Student enrolled successfully.'),
                    status_code=201
                )
            else:
                return self.error_response(
                    message=_('Student is already enrolled in this course.'),
                    status_code=400
                )
        except StudentProfile.DoesNotExist:
            return self.not_found_response(resource=_('Student'))
        except Exception as e:
            logger.error(f"Error enrolling student in course {pk}: {e}")
            return self.error_response(
                message=_('Failed to enroll student.'),
                status_code=500
            )
    
    @action(detail=False, methods=['get'])
    def active_courses(self, request):
        """Get all active courses."""
        active_courses = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(active_courses, many=True)
        
        return self.success_response(
            data=serializer.data,
            message=_('Active courses retrieved successfully.')
        )


class OptimizedStudentProfileViewSet(BaseModelViewSet):
    """
    Optimized StudentProfileViewSet demonstrating advanced filtering and responses.
    """
    
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    
    def get_queryset_for_admin(self):
        """Admins see all students."""
        return StudentProfile.objects.all()
    
    def get_queryset_for_teacher(self):
        """Teachers see students in their courses."""
        teacher_courses = Course.objects.filter(instructor=self.request.user)
        return StudentProfile.objects.filter(
            enrollments__course__in=teacher_courses,
            enrollments__is_active=True
        ).distinct()
    
    def get_queryset_for_student(self):
        """Students see only their own profile."""
        return StudentProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get student statistics."""
        try:
            queryset = self.get_queryset()
            total_students = queryset.count()
            active_students = queryset.filter(status='active').count()
            face_registered = queryset.filter(is_face_registered=True).count()
            
            stats = {
                'total_students': total_students,
                'active_students': active_students,
                'face_registered': face_registered,
                'face_registration_percentage': round(
                    (face_registered / total_students * 100) if total_students > 0 else 0, 2
                )
            }
            
            return self.success_response(
                data=stats,
                message=_('Student statistics retrieved successfully.')
            )
        except Exception as e:
            logger.error(f"Error retrieving student statistics: {e}")
            return self.error_response(
                message=_('Failed to retrieve statistics.'),
                status_code=500
            )


class OptimizedAIViewSet(BaseViewSet):
    """
    Example of AI-related ViewSet using the new decoupled AI services.
    Demonstrates separation of concerns and improved error handling.
    """
    
    @action(detail=False, methods=['post'], url_path='register-face')
    def register_face(self, request):
        """Register student face using improved AI service."""
        try:
            # Use the new decoupled AI service
            from utils.ai_services import get_ai_manager
            
            ai_service = get_ai_manager()
            face_service = ai_service.get_face_recognition_service()
            
            if not face_service or not face_service.is_available():
                return self.error_response(
                    message=_('Face recognition service is not available.'),
                    status_code=503,
                    error_code='SERVICE_UNAVAILABLE'
                )
            
            image_file = request.FILES.get('image')
            student_id = request.data.get('student_id')
            
            if not image_file or not student_id:
                return self.validation_error_response(
                    errors={
                        'image': _('Image file is required.') if not image_file else None,
                        'student_id': _('Student ID is required.') if not student_id else None
                    },
                    message=_('Invalid registration data.')
                )
            
            # Get student
            try:
                from apps.student.models import StudentProfile
                student = StudentProfile.objects.get(id=student_id)
            except StudentProfile.DoesNotExist:
                return self.not_found_response(resource=_('Student'))
            
            # Register face
            result = face_service.register_face(image_file, student)
            
            if result['success']:
                return self.success_response(
                    data={
                        'student_id': student.id,
                        'roll_number': student.roll_number,
                        'attempts_made': result.get('attempts_made', 1),
                        'processing_method': result.get('processing_method', 'unknown')
                    },
                    message=result.get('message', _('Face registered successfully.')),
                    status_code=201
                )
            else:
                return self.error_response(
                    message=result.get('message', _('Face registration failed.')),
                    status_code=400,
                    error_code='REGISTRATION_FAILED'
                )
                
        except Exception as e:
            logger.error(f"Error in face registration: {e}")
            return self.error_response(
                message=_('An error occurred during face registration.'),
                status_code=500
            )
    
    @action(detail=False, methods=['get'], url_path='service-status')
    def service_status(self, request):
        """Get AI service status."""
        try:
            from utils.ai_services import get_ai_manager
            
            ai_service = get_ai_manager()
            status_info = ai_service.get_service_status()
            
            return self.success_response(
                data=status_info,
                message=_('Service status retrieved successfully.')
            )
        except Exception as e:
            logger.error(f"Error retrieving service status: {e}")
            return self.error_response(
                message=_('Failed to retrieve service status.'),
                status_code=500
            )