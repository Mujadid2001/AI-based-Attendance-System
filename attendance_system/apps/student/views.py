"""
Views for student management.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from apps.student.models import (
    StudentProfile, Course, Enrollment, StudentFaceImage
)
from apps.student.serializers import (
    StudentProfileSerializer,
    CourseSerializer, EnrollmentSerializer, StudentFaceImageSerializer,
    StudentStatsSerializer, StudentUserRegistrationSerializer, StudentProfileUpdateSerializer
)
from apps.authentication.permissions import IsAdmin, IsAdminOrTeacher

logger = logging.getLogger(__name__)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for course management."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'  # Changed from 'code' to 'pk' to use ID

    def get_queryset(self):
        """Filter courses based on user role."""
        if self.request.user.is_admin():
            return Course.objects.all()
        elif self.request.user.is_teacher():
            return Course.objects.filter(
                instructor=self.request.user
            ) | Course.objects.filter(is_active=True)
        else:  # Student
            return Course.objects.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        """Create course (admin/teacher only)."""
        if not request.user.is_admin() and not request.user.is_teacher():
            return Response(
                {'error': _('Permission denied.')},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get enrolled students for a course."""
        course = self.get_object()
        enrollments = course.enrollments.filter(is_active=True)
        from apps.student.serializers import EnrollmentWithStudentSerializer
        serializer = EnrollmentWithStudentSerializer(enrollments, many=True)
        return Response(serializer.data)


class StudentProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for student profile management."""

    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_serializer_class(self):
        """Use different serializer for update."""
        if self.action in ['update', 'partial_update']:
            return StudentProfileUpdateSerializer
        return StudentProfileSerializer

    def get_queryset(self):
        """Filter students based on user role and optional course filter."""
        # Base queryset based on role
        if self.request.user.is_admin():
            queryset = StudentProfile.objects.all()
        elif self.request.user.is_teacher():
            # Teachers can see all students
            queryset = StudentProfile.objects.all()
        else:  # Student
            # Students can only see themselves
            queryset = StudentProfile.objects.filter(user=self.request.user)
        
        # Apply course filter if provided (for admin/teacher)
        course_id = self.request.query_params.get('course')
        if course_id and (self.request.user.is_admin() or self.request.user.is_teacher()):
            # Filter students enrolled in the specified course
            queryset = queryset.filter(
                enrollments__course_id=course_id,
                enrollments__is_active=True
            ).distinct()
        
        return queryset

    def destroy(self, request, *args, **kwargs):
        """Delete student (admin only)."""
        if not request.user.is_admin():
            return Response(
                {'error': _('Permission denied.')},
                status=status.HTTP_403_FORBIDDEN
            )

        student = self.get_object()
        roll = student.roll_number
        response = super().destroy(request, *args, **kwargs)
        logger.info(f"Student deleted: {roll}")
        return response

    @action(detail=True, methods=['get'])
    def enrollments(self, request, roll_number=None):
        """Get student enrollments."""
        student = self.get_object()
        enrollments = student.enrollments.filter(is_active=True)
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def face_images(self, request, roll_number=None):
        """Get student face images."""
        student = self.get_object()

        # Check permissions
        if (request.user != student.user and
            not request.user.is_admin() and
            not request.user.is_teacher()):
            return Response(
                {'error': _('Permission denied.')},
                status=status.HTTP_403_FORBIDDEN
            )

        images = student.face_images.all().order_by('-created_at')
        serializer = StudentFaceImageSerializer(images, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrTeacher])
    def register_student(self, request):
        """Register a new student, creating user and profile."""
        serializer = StudentUserRegistrationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            student_profile = StudentProfile.objects.get(user=user)
            logger.info(f"Student registered: {student_profile.roll_number} by {request.user.email}")
            return Response(
                StudentProfileSerializer(student_profile).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrTeacher])
    def statistics(self, request):
        """Get student statistics."""
        total = StudentProfile.objects.count()
        active = StudentProfile.objects.filter(is_active=True).count()
        face_registered = StudentProfile.objects.filter(
            is_face_registered=True
        ).count()
        courses = Course.objects.count()

        data = {
            'total_students': total,
            'active_students': active,
            'face_registered': face_registered,
            'courses_count': courses,
        }
        serializer = StudentStatsSerializer(data)
        return Response(serializer.data)


class EnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet for enrollment management."""

    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter enrollments by student if provided."""
        queryset = Enrollment.objects.all()
        
        # Students can only see their own enrollments
        if self.request.user.is_student():
            queryset = queryset.filter(student__user=self.request.user)
        
        # Filter by student_id if provided (for admin/teacher)
        student_id = self.request.query_params.get('student')
        if student_id and (self.request.user.is_admin() or self.request.user.is_teacher()):
            queryset = queryset.filter(student__user_id=student_id)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """Enroll student in course (admin/teacher only)."""
        if not request.user.is_admin() and not request.user.is_teacher():
            return Response(
                {'error': _('Permission denied.')},
                status=status.HTTP_403_FORBIDDEN
            )
        """Enroll student in course."""
        student_id = request.data.get('student')
        course_id = request.data.get('course')

        try:
            student = StudentProfile.objects.get(user_id=student_id)
            course = Course.objects.get(id=course_id)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': _('Student not found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        except Course.DoesNotExist:
            return Response(
                {'error': _('Course not found.')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already enrolled
        if Enrollment.objects.filter(
            student=student,
            course=course,
            is_active=True
        ).exists():
            return Response(
                {'error': _('Student already enrolled in this course.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if student email is verified
        if not student.user.is_verified:
            return Response(
                {'error': _('Cannot enroll student with unverified email. Student must verify their email first.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check course capacity
        if course.is_full():
            return Response(
                {'error': _('Course is at maximum capacity.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment = Enrollment.objects.create(
            student=student,
            course=course
        )
        logger.info(f"Student enrolled: {student.roll_number} in {course.code}")

        serializer = self.get_serializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
