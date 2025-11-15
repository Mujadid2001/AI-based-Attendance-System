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

logger = logging.getLogger(__name__)


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance session management."""
    
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    def get_queryset(self):
        """Filter sessions based on user role."""
        if self.request.user.is_admin():
            return AttendanceSession.objects.all()
        elif self.request.user.is_teacher():
            return AttendanceSession.objects.filter(
                course__instructor=self.request.user
            )
        return AttendanceSession.objects.none()
    
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


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance records."""
    
    queryset = Attendance.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    def get_serializer_class(self):
        """Use different serializer for create."""
        if self.action in ['create', 'update', 'partial_update']:
            return AttendanceCreateSerializer
        return AttendanceSerializer
    
    def get_queryset(self):
        """Filter attendance based on user role."""
        if self.request.user.is_admin():
            return Attendance.objects.all()
        elif self.request.user.is_teacher():
            return Attendance.objects.filter(
                session__course__instructor=self.request.user
            )
        elif self.request.user.is_student():
            return Attendance.objects.filter(
                student__user=self.request.user
            )
        return Attendance.objects.none()
    
    @action(detail=False, methods=['post'])
    def mark_attendance(self, request):
        """Mark attendance for students."""
        session_id = request.data.get('session')
        student_id = request.data.get('student')
        status_val = request.data.get('status', Attendance.Status.PRESENT)
        confidence = request.data.get('confidence_score')
        liveness = request.data.get('liveness_verified', False)
        
        try:
            session = AttendanceSession.objects.get(id=session_id)
            student = StudentProfile.objects.get(id=student_id)
        except (AttendanceSession.DoesNotExist, StudentProfile.DoesNotExist):
            return Response(
                {'error': _('Invalid session or student.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already marked
        existing = Attendance.objects.filter(
            session=session,
            student=student
        ).first()
        
        if existing:
            return Response(
                {'error': _('Attendance already marked for this student.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attendance = Attendance.objects.create(
            session=session,
            student=student,
            status=status_val,
            check_in_time=timezone.now().time(),
            check_in_method='face_recognition',
            confidence_score=confidence,
            liveness_verified=liveness,
            recorded_by=request.user
        )
        
        logger.info(f"Attendance marked: {attendance}")
        serializer = AttendanceSerializer(attendance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
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
            'late': attendances.filter(status=Attendance.Status.LATE).count(),
            'absent': attendances.filter(status=Attendance.Status.ABSENT).count(),
        }
        
        return Response({
            'summary': summary,
            'attendances': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def student_attendance_history(self, request):
        """Get attendance history for a student."""
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


class AttendanceReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for attendance reports."""
    
    queryset = AttendanceReport.objects.all()
    serializer_class = AttendanceReportSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    
    def get_queryset(self):
        """Filter reports based on user role."""
        if self.request.user.is_admin():
            return AttendanceReport.objects.all()
        elif self.request.user.is_teacher():
            return AttendanceReport.objects.filter(
                course__instructor=self.request.user
            )
        return AttendanceReport.objects.none()
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate attendance report for course and date range."""
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
        
        # Get all enrolled students
        students = StudentProfile.objects.filter(
            enrollments__course=course,
            enrollments__is_active=True
        ).distinct()
        
        reports = []
        for student in students:
            sessions = AttendanceSession.objects.filter(
                course=course,
                date__range=[start, end]
            )
            
            attendances = Attendance.objects.filter(
                session__in=sessions,
                student=student
            )
            
            present = attendances.filter(status=Attendance.Status.PRESENT).count()
            late = attendances.filter(status=Attendance.Status.LATE).count()
            absent = attendances.filter(status=Attendance.Status.ABSENT).count()
            excused = attendances.filter(status=Attendance.Status.EXCUSED).count()
            total = sessions.count()
            
            percentage = ((present + late) / total * 100) if total > 0 else 0
            
            report, _ = AttendanceReport.objects.update_or_create(
                course=course,
                student=student,
                start_date=start,
                end_date=end,
                defaults={
                    'total_sessions': total,
                    'present_count': present,
                    'late_count': late,
                    'absent_count': absent,
                    'excused_count': excused,
                    'attendance_percentage': percentage,
                    'generated_by': request.user
                }
            )
            reports.append(report)
        
        logger.info(f"Attendance report generated for {course.code}")
        serializer = AttendanceReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrTeacher])
    def export(self, request):
        """Export attendance records as CSV."""
        course_id = request.data.get('course_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        # Build query
        query = Attendance.objects.all()
        
        if course_id:
            query = query.filter(session__course_id=course_id)
        
        if start_date:
            query = query.filter(session__date__gte=start_date)
        
        if end_date:
            query = query.filter(session__date__lte=end_date)
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Course', 'Student', 'Email', 'Status', 'Time Marked', 'Notes'
        ])
        
        # Write data
        for record in query:
            writer.writerow([
                record.session.date,
                record.session.course.code,
                record.student.user.get_full_name(),
                record.student.user.email,
                record.status,
                record.created_at.strftime('%H:%M:%S') if record.created_at else '',
                record.notes or ''
            ])
        
        # Return CSV file
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_{datetime.now().strftime("%Y%m%d")}.csv"'
        return response


# Helper endpoints

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_attendance_by_face(request):
    """Mark attendance using facial recognition."""
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
@permission_classes([IsAuthenticated])
def today_attendance(request):
    """Get today's attendance statistics."""
    today = timezone.now().date()
    
    records = Attendance.objects.filter(session__date=today)
    total_sessions = AttendanceSession.objects.filter(date=today).count()
    
    marked = records.filter(status__in=['present', 'late', 'absent']).count()
    present = records.filter(status='present').count()
    
    return Response({
        'date': today,
        'total': marked,
        'marked': present,
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
        
        data = []
        for record in records:
            data.append({
                'id': record.id,
                'student_name': record.student.user.get_full_name(),
                'student_email': record.student.user.email,
                'status': record.status,
                'time': record.created_at.strftime('%H:%M:%S') if record.created_at else '',
                'notes': record.notes
            })
        
        return Response(data)
    except AttendanceSession.DoesNotExist:
        return Response(
            {'detail': 'Session not found'},
            status=status.HTTP_404_NOT_FOUND
        )


