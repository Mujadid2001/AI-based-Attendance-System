"""
Celery configuration for AI-based Attendance System.

This module sets up Celery for background task processing.
Tasks run asynchronously in worker processes, preventing request blocking.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Respect the deployment's configured settings module and keep development as
# the local fallback.
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.development'),
)

# Create Celery app
app = Celery('attendance_system')

# Load configuration from Django settings using namespace
# All Celery configuration must use 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
# This looks for 'tasks.py' in each app
app.autodiscover_tasks()

# ============================================================
# PERIODIC TASKS (Scheduled tasks)
# ============================================================
app.conf.beat_schedule = {
    'generate-daily-reports': {
        'task': 'apps.attendance.tasks.generate_daily_reports',
        'schedule': crontab(hour=22, minute=0),  # 10 PM daily
        'options': {'queue': 'default'}
    },
    'send-attendance-reminders': {
        'task': 'apps.attendance.tasks.send_attendance_reminders',
        'schedule': crontab(hour=7, minute=0),  # 7 AM daily
        'options': {'queue': 'default'}
    },
    'cleanup-old-attendance-data': {
        'task': 'apps.attendance.tasks.cleanup_old_attendance_data',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2 AM
        'options': {'queue': 'default'}
    },
}


@app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')
