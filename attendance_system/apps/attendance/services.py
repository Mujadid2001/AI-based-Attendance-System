from apps.attendance.models import Attendance, AttendanceSession
from apps.student.models import StudentProfile
from django.utils import timezone

def mark_attendance(session_id, student_id, status, confidence, liveness, user):
    # StudentProfile's primary key is `user` (a OneToOneField with
    # primary_key=True), so there is no `id` column - filtering by `id`
    # raises FieldError and a non-numeric id raises ValueError. Both are
    # caller-supplied, so both have to be handled here.
    try:
        session = AttendanceSession.objects.get(id=session_id)
        student = StudentProfile.objects.get(user_id=student_id)
    except (AttendanceSession.DoesNotExist, StudentProfile.DoesNotExist,
            ValueError, TypeError):
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
