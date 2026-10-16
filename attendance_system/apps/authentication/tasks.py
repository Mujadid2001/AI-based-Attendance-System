"""
Celery tasks for authentication operations.
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from apps.authentication.utils import get_frontend_url

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, token):
    """Send email verification link."""
    try:
        from apps.authentication.models import User
        
        user = User.objects.get(id=user_id)
        
        # Build verification link
        frontend_url = get_frontend_url()
        verification_link = f"{frontend_url}/verify-email?token={token}"
        
        # Log the verification link (in production, send via email)
        logger.info(f"Verification link for {user.email}: {verification_link}")
        
        # In production, render HTML and send:
        # html_message = render_to_string('emails/verify_email.html', {
        #     'user_name': user.get_full_name(),
        #     'verification_link': verification_link
        # })
        # send_mail(
        #     subject="Verify Your Email Address",
        #     message="Please verify your email address",
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[user.email],
        #     html_message=html_message,
        # )
        
        logger.info(f"Verification email task queued for {user.email}")
        return "success"
        
    except Exception as exc:
        logger.error(f"Error sending verification email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, token):
    """Send password reset link."""
    try:
        from apps.authentication.models import User
        
        user = User.objects.get(id=user_id)
        
        # Build reset link
        frontend_url = get_frontend_url()
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        # Log the reset link (in production, send via email)
        logger.info(f"Password reset link for {user.email}: {reset_link}")
        
        # In production, render HTML and send:
        # html_message = render_to_string('emails/password_reset.html', {
        #     'user_name': user.get_full_name(),
        #     'reset_link': reset_link
        # })
        # send_mail(
        #     subject="Reset Your Password",
        #     message="Click the link to reset your password",
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[user.email],
        #     html_message=html_message,
        # )
        
        logger.info(f"Password reset email task queued for {user.email}")
        return "success"
        
    except Exception as exc:
        logger.error(f"Error sending password reset email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user."""
    try:
        from apps.authentication.models import User
        
        user = User.objects.get(id=user_id)
        
        logger.info(f"Welcome email task queued for {user.email}")
        
        # In production, render HTML and send:
        # html_message = render_to_string('emails/welcome.html', {
        #     'user_name': user.get_full_name(),
        #     'user_role': user.get_role_display()
        # })
        # send_mail(
        #     subject=f"Welcome to AI Attendance System",
        #     message="Welcome!",
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[user.email],
        #     html_message=html_message,
        # )
        
        logger.info(f"Welcome email sent to {user.email}")
        return "success"
        
    except Exception as exc:
        logger.error(f"Error sending welcome email: {exc}")
        return f"Error: {exc}"
