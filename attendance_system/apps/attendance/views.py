"""
Attendance management views.
"""
import logging
import csv
from datetime import datetime, timedelta, date
from io import StringIO
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Sum, Case, When, IntegerField
from django.utils import timezone
from django.http import HttpResponse
from apps.attendance.models import (
    AttendanceSession, Attendance, AttendanceReport
)
from apps.attendance.serializers import (
    AttendanceSessionSerializer, AttendanceSerializer,
    AttendanceCreateSerializer, AttendanceReportSerializer,
    DailyAttendanceSerializer, StudentAttendanceStatsSerializer
)
from apps.authentication.permissions import IsAdminOrTeacher, IsStudent, IsAdmin
from apps.student.models import StudentProfile, Course, Enrollment
from apps.ai_core.services import get_ai_manager
from utils.viewsets import BaseModelViewSet, ReadOnlyViewSet

logger = logging.getLogger(__name__)


class AttendanceSessionViewSet(BaseModelViewSet):
    """ViewSet for attendance session management."""
    
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Set different permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminOrTeacher()]
        return [IsAuthenticated()]
    
    def get_queryset_for_admin(self):
        """Admin can see all sessions."""
        return AttendanceSession.objects.all()
    
    def get_queryset_for_teacher(self):
        """Teachers can see sessions they created OR sessions for courses they teach."""
        return AttendanceSession.objects.filter(
            Q(created_by=self.request.user) | Q(course__instructor=self.request.user)
        ).distinct()
    
    def get_queryset_for_student(self):
        """Students can see sessions for courses they're enrolled in."""
        return AttendanceSession.objects.filter(
            course__enrollments__student__user=self.request.user,
            course__enrollments__is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Set created_by when creating a session."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_session(self, request):
        """Create new attendance session."""
        course_id = request.data.get('course')
        date_str = request.data.get('date')
        start_time_str = request.data.get('start_time')
        
        try:
            course = Course.objects.get(id=course_id)
            session_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
        except (Course.DoesNotExist, ValueError):
            return Response(
                {'error': _('Invalid course, date or time.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session, created = AttendanceSession.objects.get_or_create(
            course=course,
            date=session_date,
            defaults={
                'start_time': start_time,
                'created_by': request.user
            }
        )
        
        if not created:
            return Response(
                {'error': _('Session already exists for this date.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Attendance session created: {session}")
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def close_session(self, request, pk=None):
        """Close attendance session."""
        session = self.get_object()
        session.end_time = timezone.now().time()
        session.is_active = False
        session.save()
        
        logger.info(f"Attendance session closed: {session}")
        serializer = self.get_serializer(session)
        return Response(serializer.data)


class AttendanceViewSet(BaseModelViewSet):
    """ViewSet for attendance records."""
    
    queryset = Attendance.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    def get_permissions(self):
        """Allow students to view their own attendance."""
        if self.action in ['list', 'retrieve', 'my_attendance']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrTeacher()]
    
    def get_serializer_class(self):
        """Use different serializer for create."""
        if self.action in ['create', 'update', 'partial_update']:
            return AttendanceCreateSerializer
        return AttendanceSerializer
    
    def get_queryset_for_admin(self):
        """Admin can see all attendance."""
        return Attendance.objects.all()
    
    def get_queryset_for_teacher(self):
        """Teachers can see attendance for courses they teach OR sessions they created."""
        return Attendance.objects.filter(
            Q(session__course__instructor=self.request.user) |
            Q(session__created_by=self.request.user)
        ).distinct()
    
    def get_queryset_for_student(self):
        """Students can see their own attendance."""
        return Attendance.objects.filter(student__user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Update attendance record."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return with full serializer
        output_serializer = AttendanceSerializer(instance)
        return Response(output_serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update attendance record."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Create attendance record with proper defaults for manual marking."""
        data = request.data.copy()
        
        # Set defaults for manual attendance marking
        if 'check_in_method' not in data:
            data['check_in_method'] = 'manual'
        if 'check_in_time' not in data:
            data['check_in_time'] = timezone.now().time()
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Check if attendance already exists
        # StudentProfile uses user as primary key, so we use pk instead of id
        session_id = serializer.validated_data.get('session').id
        student = serializer.validated_data.get('student')
        student_id = student.pk  # pk works for any model, even with custom primary keys
        
        existing = Attendance.objects.filter(
            session_id=session_id,
            student_id=student_id
        ).first()
        
        if existing:
            return Response(
                {'detail': 'Attendance already exists for this student in this session.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set recorded_by
        attendance = serializer.save(recorded_by=request.user)
        
        logger.info(f"Attendance created: {attendance}")
        
        # Return with full serializer
        output_serializer = AttendanceSerializer(attendance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def mark_attendance(self, request):
        """Mark attendance for students."""
        from .services import mark_attendance
        session_id = request.data.get('session')
        student_id = request.data.get('student')
        status_val = request.data.get('status', Attendance.Status.PRESENT)
        confidence = request.data.get('confidence_score')
        liveness = request.data.get('liveness_verified', False)

        attendance, created = mark_attendance(
            session_id, student_id, status_val, confidence, liveness, request.user
        )

        if attendance:
            logger.info(f"Attendance marked: {attendance}")
            serializer = AttendanceSerializer(attendance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': _('Invalid session or student.')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['put'])
    def update_status(self, request, pk=None):
        """Update attendance status."""
        attendance = self.get_object()
        new_status = request.data.get('status')
        remarks = request.data.get('remarks', '')
        
        if new_status not in dict(Attendance.Status.choices):
            return Response(
                {'error': _('Invalid status.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attendance.status = new_status
        attendance.remarks = remarks
        attendance.recorded_by = request.user
        attendance.save()
        
        logger.info(f"Attendance updated: {attendance}")
        serializer = AttendanceSerializer(attendance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def session_attendance(self, request):
        """Get attendance for a specific session."""
        session_id = request.query_params.get('session')
        
        try:
            session = AttendanceSession.objects.get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'error': _('Session not found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        attendances = session.attendances.all()
        serializer = AttendanceSerializer(attendances, many=True)
        
        # Calculate summary
        summary = {
            'total': attendances.count(),
            'present': attendances.filter(status=Attendance.Status.PRESENT).count(),
            'leave': attendances.filter(status=Attendance.Status.LEAVE).count(),
            'absent': attendances.filter(status=Attendance.Status.ABSENT).count(),
        }
        
        return Response({
            'summary': summary,
            'attendances': serializer.data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_attendance(self, request):
        """Get attendance stats for the logged-in student."""
        if not request.user.is_student():
            return Response(
                {'error': _('This endpoint is only for students.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            student = StudentProfile.objects.get(user=request.user)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': _('Student profile not found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all attendance records
        queryset = student.attendances.all().select_related('session', 'session__course')
        
        # Calculate overall statistics
        total = queryset.count()
        present = queryset.filter(status=Attendance.Status.PRESENT).count()
        leave = queryset.filter(status=Attendance.Status.LEAVE).count()
        absent = queryset.filter(status=Attendance.Status.ABSENT).count()
        percentage = ((present + leave) / total * 100) if total > 0 else 0
        
        # Get enrolled courses with attendance stats
        enrollments = student.enrollments.filter(is_active=True).select_related('course')
        courses_stats = []
        
        for enrollment in enrollments:
            course_attendances = queryset.filter(session__course=enrollment.course)
            course_total = course_attendances.count()
            course_present = course_attendances.filter(status=Attendance.Status.PRESENT).count()
            course_leave = course_attendances.filter(status=Attendance.Status.LEAVE).count()
            course_percentage = ((course_present + course_leave) / course_total * 100) if course_total > 0 else 0
            
            courses_stats.append({
                'course_id': enrollment.course.id,
                'course_code': enrollment.course.code,
                'course_name': enrollment.course.name,
                'total_sessions': course_total,
                'present': course_present,
                'leave': course_leave,
                'absent': course_total - course_present - course_leave,
                'percentage': round(course_percentage, 2)
            })
        
        # Get recent attendance records (last 10)
        recent_records = queryset.order_by('-session__date', '-session__start_time')[:10]
        serializer = AttendanceSerializer(recent_records, many=True)
        
        return Response({
            'student': {
                'roll_number': student.roll_number,
                'name': student.user.get_full_name(),
                'department': student.department
            },
            'overall_stats': {
                'total': total,
                'present': present,
                'leave': leave,
                'absent': absent,
                'percentage': round(percentage, 2)
            },
            'courses': courses_stats,
            'recent_records': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def student_attendance_history(self, request):
        """Get attendance history for a student (Admin/Teacher only)."""
        student_id = request.query_params.get('student')
        course_id = request.query_params.get('course')
        
        try:
            student = StudentProfile.objects.get(id=student_id)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': _('Student not found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = student.attendances.all().select_related('session')
        
        if course_id:
            queryset = queryset.filter(session__course_id=course_id)
        
        serializer = AttendanceSerializer(queryset, many=True)
        
        # Calculate statistics
        total = queryset.count()
        present = queryset.filter(status=Attendance.Status.PRESENT).count()
        late = queryset.filter(status=Attendance.Status.LATE).count()
        absent = queryset.filter(status=Attendance.Status.ABSENT).count()
        percentage = ((present + late) / total * 100) if total > 0 else 0
        
        return Response({
            'student': {
                'roll_number': student.roll_number,
                'name': student.user.get_full_name()
            },
            'statistics': {
                'total': total,
                'present': present,
                'late': late,
                'absent': absent,
                'percentage': round(percentage, 2)
            },
            'records': serializer.data
        })


class AttendanceReportViewSet(ReadOnlyViewSet):
    """ViewSet for attendance reports."""
    
    queryset = AttendanceReport.objects.all()
    serializer_class = AttendanceReportSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    def get_queryset_for_admin(self):
        """Admin can see all reports."""
        return AttendanceReport.objects.all()
    
    def get_queryset_for_teacher(self):
        """Teachers can see reports for courses they teach."""
        return AttendanceReport.objects.filter(
            course__instructor=self.request.user
        )
    
    def get_queryset_for_student(self):
        """Students have no access to reports."""
        return AttendanceReport.objects.none()
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate session-based attendance report for course and date range."""
        course_id = request.data.get('course')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        try:
            course = Course.objects.get(id=course_id)
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except (Course.DoesNotExist, ValueError):
            return Response(
                {'error': _('Invalid course or date.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all attendance sessions in the date range
        sessions = AttendanceSession.objects.filter(
            course=course,
            date__range=[start, end]
        ).order_by('-date', '-start_time')
        
        # Get total enrolled students for percentage calculation
        total_students = StudentProfile.objects.filter(
            enrollments__course=course,
            enrollments__is_active=True
        ).distinct().count()
        
        # Build session-wise report
        report_data = []
        for session in sessions:
            attendances = Attendance.objects.filter(session=session)
            
            present = attendances.filter(status=Attendance.Status.PRESENT).count()
            leave = attendances.filter(status=Attendance.Status.LEAVE).count()
            absent = attendances.filter(status=Attendance.Status.ABSENT).count()
            excused = attendances.filter(status=Attendance.Status.EXCUSED).count()
            
            # Calculate percentage (present + leave as considered attended)
            attended = present + leave
            percentage = (attended / total_students * 100) if total_students > 0 else 0
            
            report_data.append({
                'id': session.id,
                'date': session.date,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'course_code': course.code,
                'course_name': course.name,
                'total_students': total_students,
                'present_count': present,
                'leave_count': leave,
                'absent_count': absent,
                'excused_count': excused,
                'attendance_percentage': round(percentage, 2)
            })
        
        logger.info(f"Session-based attendance report generated for {course.code}")
        return Response(report_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrTeacher])
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrTeacher])
    def export(self, request):
        """Export session-based attendance report as CSV."""
        course_id = request.data.get('course')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        try:
            course = Course.objects.get(id=course_id)
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except (Course.DoesNotExist, ValueError):
            return Response(
                {'error': _('Invalid course or date.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all attendance sessions in the date range
        sessions_query = AttendanceSession.objects.filter(course=course)
        
        if start and end:
            sessions_query = sessions_query.filter(date__range=[start, end])
        elif start:
            sessions_query = sessions_query.filter(date__gte=start)
        elif end:
            sessions_query = sessions_query.filter(date__lte=end)
            
        sessions = sessions_query.order_by('-date', '-start_time')
        
        # Get total enrolled students
        total_students = StudentProfile.objects.filter(
            enrollments__course=course,
            enrollments__is_active=True
        ).distinct().count()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Start Time', 'End Time', 'Course Code', 'Course Name',
            'Total Students', 'Present', 'Leave', 'Absent', 'Excused', 'Attendance %'
        ])
        
        # Write data
        for session in sessions:
            attendances = Attendance.objects.filter(session=session)
            
            present = attendances.filter(status=Attendance.Status.PRESENT).count()
            leave = attendances.filter(status=Attendance.Status.LEAVE).count()
            absent = attendances.filter(status=Attendance.Status.ABSENT).count()
            excused = attendances.filter(status=Attendance.Status.EXCUSED).count()
            
            attended = present + leave
            percentage = (attended / total_students * 100) if total_students > 0 else 0
            
            writer.writerow([
                session.date.strftime('%Y-%m-%d'),
                session.start_time.strftime('%H:%M:%S'),
                session.end_time.strftime('%H:%M:%S') if session.end_time else '',
                course.code,
                course.name,
                total_students,
                present,
                leave,
                absent,
                excused,
                f'{percentage:.2f}%'
            ])
        
        # Return CSV file
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        filename = f'attendance_report_{course.code}_{datetime.now().strftime("%Y%m%d")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# Helper endpoints

@api_view(['POST'])
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrTeacher])
def mark_attendance_by_face(request):
    """Mark attendance using facial recognition (Admin/Teacher only)."""
    image_file = request.FILES.get('image')
    session_id = request.data.get('session_id')
    
    if not image_file or not session_id:
        return Response(
            {'detail': 'Image and session_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        session = AttendanceSession.objects.get(id=session_id)
        ai_manager = get_ai_manager()
        
        # Recognize face
        result = ai_manager.recognize_and_mark_attendance(image_file, session)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    except AttendanceSession.DoesNotExist:
        return Response(
            {'detail': 'Session not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error marking attendance by face: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrTeacher])
def get_active_session(request):
    """Get the currently active attendance session for the logged-in teacher."""
    try:
        session = AttendanceSession.objects.get(
            course__instructor=request.user,
            is_active=True
        )
        serializer = AttendanceSessionSerializer(session)
        return Response(serializer.data)
    except AttendanceSession.DoesNotExist:
        return Response(
            {'detail': 'No active session found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error marking attendance by face: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_attendance(request):
    """Get today's attendance statistics."""
    today = timezone.now().date()
    
    records = Attendance.objects.filter(session__date=today)
    total_sessions = AttendanceSession.objects.filter(date=today).count()
    
    marked = records.filter(status__in=['present', 'leave', 'absent']).count()
    present = records.filter(status='present').count()
    leave = records.filter(status='leave').count()
    absent = records.filter(status='absent').count()
    
    # Calculate total expected attendance (total sessions * total enrolled students)
    # For simplicity, we'll use marked as total
    total_expected = marked
    
    return Response({
        'date': today,
        'total': total_expected,
        'marked': present + leave,
        'present': present,
        'leave': leave,
        'absent': absent,
        'sessions': total_sessions,
        'percentage': round((present / (marked or 1)) * 100, 2)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_records(request, session_id):
    """Get attendance records for a session."""
    try:
        session = AttendanceSession.objects.get(id=session_id)
        records = Attendance.objects.filter(session=session).select_related(
            'student', 'student__user'
        )
        
        # Use the serializer to return properly structured data
        serializer = AttendanceSerializer(records, many=True)
        return Response(serializer.data)
    except AttendanceSession.DoesNotExist:
        return Response(
            {'detail': 'Session not found'},
            status=status.HTTP_404_NOT_FOUND
        )


