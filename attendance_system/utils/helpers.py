"""
Utility functions for attendance system.
"""
import csv
from io import StringIO
from datetime import datetime
from django.http import HttpResponse
from apps.attendance.models import AttendanceReport


def export_attendance_to_csv(queryset, course_name: str = "Attendance"):
    """
    Export attendance records to CSV.
    
    Args:
        queryset: QuerySet of AttendanceReport or Attendance records
        course_name: Name for the CSV file
    
    Returns:
        HttpResponse with CSV file
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{course_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Roll Number', 'Student Name', 'Course', 'Start Date', 'End Date',
        'Total Sessions', 'Present', 'Late', 'Absent', 'Excused',
        'Attendance %'
    ])
    
    # Write data
    for report in queryset:
        writer.writerow([
            report.student.roll_number,
            report.student.user.get_full_name(),
            report.course.code,
            report.start_date,
            report.end_date,
            report.total_sessions,
            report.present_count,
            report.late_count,
            report.absent_count,
            report.excused_count,
            f"{report.attendance_percentage}%"
        ])
    
    return response


def calculate_attendance_statistics(attendance_records):
    """
    Calculate statistics from attendance records.
    
    Args:
        attendance_records: QuerySet of Attendance objects
    
    Returns:
        dict with statistics
    """
    total = attendance_records.count()
    
    if total == 0:
        return {
            'total': 0,
            'present': 0,
            'late': 0,
            'absent': 0,
            'excused': 0,
            'present_percentage': 0.0,
            'absent_percentage': 0.0,
            'late_percentage': 0.0
        }
    
    from apps.attendance.models import Attendance
    
    present = attendance_records.filter(status=Attendance.Status.PRESENT).count()
    late = attendance_records.filter(status=Attendance.Status.LATE).count()
    absent = attendance_records.filter(status=Attendance.Status.ABSENT).count()
    excused = attendance_records.filter(status=Attendance.Status.EXCUSED).count()
    
    return {
        'total': total,
        'present': present,
        'late': late,
        'absent': absent,
        'excused': excused,
        'present_percentage': round((present / total) * 100, 2),
        'absent_percentage': round((absent / total) * 100, 2),
        'late_percentage': round((late / total) * 100, 2)
    }


def get_student_attendance_by_course(student, course):
    """Get attendance statistics for student in specific course."""
    from apps.attendance.models import Attendance, AttendanceSession
    
    sessions = AttendanceSession.objects.filter(course=course)
    attendances = Attendance.objects.filter(
        student=student,
        session__in=sessions
    )
    
    return calculate_attendance_statistics(attendances)


def mark_late_attendance(session, after_minutes: int = 15):
    """
    Automatically mark attendance as late if not marked as present.
    
    Args:
        session: AttendanceSession object
        after_minutes: Minutes after session start to mark as late
    """
    from apps.attendance.models import Attendance, AttendanceSession
    from apps.student.models import Enrollment
    from datetime import timedelta
    from django.utils import timezone
    
    # Get enrolled students
    enrollments = Enrollment.objects.filter(
        course=session.course,
        is_active=True
    )
    
    for enrollment in enrollments:
        # Check if already marked
        existing = Attendance.objects.filter(
            session=session,
            student=enrollment.student
        ).first()
        
        if not existing:
            # Create absent attendance
            Attendance.objects.create(
                session=session,
                student=enrollment.student,
                status=Attendance.Status.ABSENT,
                check_in_method='auto'
            )


def verify_face_embedding_integrity():
    """Verify all face embeddings are valid."""
    from apps.student.models import StudentProfile
    import numpy as np
    
    errors = []
    students = StudentProfile.objects.filter(is_face_registered=True)
    
    for student in students:
        embedding = student.get_face_embedding()
        if embedding is None or len(embedding) != 128:
            errors.append(f"Invalid embedding for {student.roll_number}")
    
    return {
        'total_checked': students.count(),
        'errors': errors,
        'status': 'OK' if not errors else 'ERROR'
    }
