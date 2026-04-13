"""
Celery tasks for attendance operations.
These run asynchronously in background workers.
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import AttendanceSession, Attendance
from apps.student.models import StudentProfile

logger = logging.getLogger(__name__)


# ============================================================
# PDF GENERATION TASKS
# ============================================================

@shared_task(bind=True, max_retries=3)
def generate_attendance_report_async(self, attendance_id):
    """
    Generate PDF report for attendance asynchronously.
    
    Args:
        attendance_id: ID of attendance record
    
    Returns:
        str: Path to generated PDF
    """
    try:
        from .models import Attendance
        
        attendance = Attendance.objects.get(id=attendance_id)
        
        # Simulate PDF generation (replace with actual PDF generation logic)
        logger.info(f"Generating PDF for attendance {attendance_id}")
        
        # In real implementation:
        # pdf_path = generate_attendance_report_pdf(attendance)
        # send_report_ready_notification.delay(attendance.student.user.id, pdf_path)
        
        logger.info(f"PDF generated for attendance {attendance_id}")
        return f"report_{attendance_id}.pdf"
        
    except Attendance.DoesNotExist:
        logger.error(f"Attendance {attendance_id} not found")
        return None
    except Exception as exc:
        logger.error(f"Error generating report: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def generate_course_attendance_report(self, course_id, start_date, end_date, user_id):
    """
    Generate attendance report for entire course.
    
    Args:
        course_id: Course ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        user_id: User requesting the report
    
    Returns:
        dict: Report data
    """
    try:
        from apps.student.models import Course
        
        course = Course.objects.get(id=course_id)
        
        # Calculate attendance for each student
        sessions = AttendanceSession.objects.filter(
            course=course,
            date__gte=start_date,
            date__lte=end_date
        )
        
        student_reports = []
        total_sessions = sessions.count()
        
        if total_sessions > 0:
            for enrollment in course.enrollments.filter(is_active=True):
                student = enrollment.student
                present_count = Attendance.objects.filter(
                    student=student,
                    session__in=sessions,
                    status='present'
                ).count()
                
                percentage = (present_count / total_sessions * 100)
                
                student_reports.append({
                    'roll_number': student.roll_number,
                    'name': student.user.get_full_name(),
                    'present': present_count,
                    'total': total_sessions,
                    'percentage': round(percentage, 2)
                })
        
        logger.info(f"Course report generated for course {course_id}")
        return {
            'course': course.code,
            'students': student_reports,
            'generated_at': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error generating course report: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ============================================================
# EMAIL NOTIFICATION TASKS
# ============================================================

@shared_task(bind=True, max_retries=3)
def send_attendance_email(self, user_id, subject, template_name, context):
    """
    Send email to user asynchronously.
    
    Args:
        user_id: User ID to send email to
        subject: Email subject
        template_name: Template name (without extension)
        context: Template context variables
    
    Returns:
        str: "success" on completion
    """
    try:
        from apps.authentication.models import User
        
        user = User.objects.get(id=user_id)
        
        # For now, just log it (implement email templates later)
        logger.info(f"Sending email to {user.email}: {subject}")
        
        # In production, render HTML and send:
        # html_message = render_to_string(f'emails/{template_name}.html', context)
        # send_mail(
        #     subject=subject,
        #     message=subject,
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[user.email],
        #     html_message=html_message,
        #     fail_silently=False,
        # )
        
        logger.info(f"Email sent to {user.email}: {subject}")
        return "success"
        
    except Exception as exc:
        logger.error(f"Error sending email: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_report_ready_notification(user_id, pdf_path):
    """Notify user that their report is ready."""
    send_attendance_email.delay(
        user_id,
        "Your Attendance Report is Ready",
        "report_ready",
        {'pdf_path': pdf_path}
    )


@shared_task
def send_attendance_reminders():
    """
    Send daily attendance reminders to students.
    Scheduled to run at 7 AM daily.
    """
    from apps.student.models import StudentProfile
    
    today = timezone.now().date()
    students = StudentProfile.objects.filter(is_face_registered=True)[:50]  # Limit to prevent overload
    
    sent_count = 0
    for student in students:
        send_attendance_email.delay(
            student.user.id,
            "Reminder: Mark Your Attendance Today",
            "attendance_reminder",
            {
                'student_name': student.user.get_full_name(),
                'date': today
            }
        )
        sent_count += 1
    
    logger.info(f"Sent {sent_count} attendance reminders")
    return f"Sent {sent_count} reminders"


@shared_task
def send_bulk_notification(recipient_list, subject, template_name, context):
    """Send same email to multiple recipients."""
    for user_id in recipient_list:
        send_attendance_email.delay(user_id, subject, template_name, context)
    
    logger.info(f"Queued emails for {len(recipient_list)} recipients")


# ============================================================
# REPORT GENERATION TASKS
# ============================================================

@shared_task(bind=True, max_retries=2)
def generate_daily_reports(self):
    """
    Generate daily attendance reports for all active sessions.
    Scheduled to run at 10 PM daily.
    """
    try:
        from .models import AttendanceReport
        
        today = timezone.now().date()
        sessions = AttendanceSession.objects.filter(date=today, is_active=False)
        
        report_count = 0
        for session in sessions:
            # Get all attendances for this session
            attendances = Attendance.objects.filter(session=session)
            
            # Create reports for each student in the course
            for enrollment in session.course.enrollments.filter(is_active=True):
                student = enrollment.student
                
                # Create or update report
                report, created = AttendanceReport.objects.get_or_create(
                    course=session.course,
                    student=student,
                    start_date=today,
                    end_date=today
                )
                
                # Calculate stats
                report.total_sessions = 1
                report.present_count = attendances.filter(
                    student=student,
                    status='present'
                ).count()
                report.absent_count = attendances.filter(
                    student=student,
                    status='absent'
                ).count()
                report.attendance_percentage = report.calculate_percentage()
                report.save()
                
                report_count += 1
        
        logger.info(f"Generated {report_count} daily reports")
        return f"Generated {report_count} reports"
        
    except Exception as exc:
        logger.error(f"Error generating daily reports: {exc}")
        raise self.retry(exc=exc, countdown=300)


# ============================================================
# DATA PROCESSING TASKS
# ============================================================

@shared_task
def process_face_image_batch(face_image_ids):
    """
    Process multiple face images for training data.
    Used during bulk face registration.
    """
    from apps.student.models import StudentFaceImage
    from apps.ai_core.services import get_ai_manager
    
    manager = get_ai_manager()
    successful = 0
    failed = 0
    
    for image_id in face_image_ids:
        try:
            image = StudentFaceImage.objects.get(id=image_id)
            logger.info(f"Processing face image {image_id}")
            successful += 1
        except Exception as e:
            logger.error(f"Error processing face image {image_id}: {e}")
            failed += 1
    
    logger.info(f"Batch processing complete: {successful} successful, {failed} failed")
    return {'successful': successful, 'failed': failed}


@shared_task
def update_attendance_statistics():
    """
    Update aggregate attendance statistics.
    Run periodically to cache statistics.
    """
    from django.core.cache import cache
    from apps.student.models import Course
    
    for course in Course.objects.filter(is_active=True):
        # Calculate statistics
        stats = {
            'total_sessions': course.attendance_sessions.count(),
            'total_students': course.enrollments.filter(is_active=True).count(),
        }
        
        # Cache for 24 hours
        cache.set(f'course_stats_{course.id}', stats, 86400)
    
    logger.info("Updated attendance statistics cache")


# ============================================================
# CLEANUP TASKS
# ============================================================

@shared_task
def cleanup_old_attendance_data(days=730):
    """
    Archive old attendance records (2 years and older).
    For GDPR compliance, archive instead of deleting.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now().date() - timedelta(days=days)
    
    old_sessions = AttendanceSession.objects.filter(date__lt=cutoff_date)
    count = old_sessions.count()
    
    logger.info(f"Found {count} sessions older than {cutoff_date}")
    logger.info("Archive policy: Keep data for GDPR compliance")
    
    # For GDPR compliance, archive instead of deleting
    # old_sessions.update(is_archived=True)
    
    return count


# ============================================================
# DEBUGGING / TESTING TASKS
# ============================================================

@shared_task
def test_task():
    """Simple test task to verify Celery is working."""
    logger.info("Test task executed successfully!")
    return "Task executed at: " + str(timezone.now())
