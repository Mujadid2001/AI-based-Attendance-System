from apps.attendance.models import Attendance, AttendanceSession
from apps.student.models import StudentProfile
from django.utils import timezone

def mark_attendance(session_id, student_id, status, confidence, liveness, user):
    try:
        session = AttendanceSession.objects.get(id=session_id)
        student = StudentProfile.objects.get(id=student_id)
    except (AttendanceSession.DoesNotExist, StudentProfile.DoesNotExist):
        return None, False

    attendance, created = Attendance.objects.get_or_create(
        session=session,
        student=student,
        defaults={
            'status': status,
            'check_in_time': timezone.now().time(),
            'check_in_method': 'face_recognition',
            'confidence_score': confidence,
            'liveness_verified': liveness,
            'recorded_by': user
        }
    )

    return attendance, created
