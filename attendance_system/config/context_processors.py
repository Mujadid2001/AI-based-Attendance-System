"""
Admin context processors for dashboard statistics.
"""
from datetime import date
from apps.student.models import StudentProfile, Course
from apps.attendance.models import AttendanceSession, Attendance


def admin_dashboard_stats(request):
    """Add dashboard statistics to admin context."""
    if not request.path.startswith('/admin'):
        return {}
    
    try:
        total_students = StudentProfile.objects.filter(is_active=True).count()
        total_courses = Course.objects.filter(is_active=True).count()
        
        today = date.today()
        today_sessions = AttendanceSession.objects.filter(date=today).count()
        today_attendance = Attendance.objects.filter(
            session__date=today,
            status='present'
        ).count()
        
        return {
            'total_students': total_students,
            'total_courses': total_courses,
            'today_sessions': today_sessions,
            'today_attendance': today_attendance,
        }
    except Exception:
        return {
            'total_students': 0,
            'total_courses': 0,
            'today_sessions': 0,
            'today_attendance': 0,
        }
