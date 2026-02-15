"""
Email utilities for sending verification and notification emails.
"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from apps.authentication.utils import get_frontend_url


logger = logging.getLogger(__name__)

SYSTEM_NAME = "AI Attendance System"
YEAR = "2025"
SYSTEM_ICON = "🎓"

def send_verification_email(user, token):
    """
    Send email verification link to user.
    
    Args:
        user: User instance
        token: EmailVerificationToken instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Verify Your Email - {SYSTEM_NAME}'
        
        # Verification token to be used by frontend
        verification_token = str(token.token)
        
        # Create verification link for frontend
        frontend_url = get_frontend_url()
        verification_link = f"{frontend_url}/verify-email?token={verification_token}"
        
        # Create HTML message with clickable link
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    margin: 20px 0;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                .button:hover {{ background-color: #1d4ed8; }}
                .token-box {{ 
                    background-color: #f0f0f0; 
                    border: 1px solid #2563eb; 
                    padding: 15px; 
                    margin: 20px 0; 
                    text-align: center; 
                    font-family: monospace; 
                    font-size: 12px; 
                    word-break: break-all;
                    border-radius: 5px;
                }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .info {{ background-color: #e0f2fe; padding: 10px; border-left: 4px solid #0284c7; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {SYSTEM_NAME}!</h1>
                </div>
                <div class="content">
                    <h2>Hello {user.get_full_name() or user.email},</h2>
                    <p>Thank you for registering with {SYSTEM_NAME}. Please verify your email address to complete your registration and access the system.</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email Address</a>
                    </div>
                    
                    <p style="text-align: center; color: #666; font-size: 12px;">Or copy this link:</p>
                    <div class="token-box">
                        <a href="{verification_link}" style="color: #2563eb; text-decoration: none; word-wrap: break-word;">{verification_link}</a>
                    </div>
                    
                    <div class="info">
                        <strong>Verification Token (if link doesn't work):</strong><br>
                        {verification_token}
                    </div>
                    
                    <p><strong>⏰ This link will expire in 48 hours.</strong></p>
                    <p>If you didn't create an account, please ignore this email and your account will not be activated.</p>
                </div>
                <div class="footer">
                    <p>&copy; {YEAR} {SYSTEM_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        plain_message = f"""
Hello {user.get_full_name() or user.email},

Thank you for registering with {SYSTEM_NAME}. Please verify your email address to complete your registration.

Click the link below to verify your email:
{verification_link}

Or copy and paste this verification token in the application:
{verification_token}

This link will expire in 48 hours.

If you didn't create an account, please ignore this email.

© {YEAR} {SYSTEM_NAME}. All rights reserved.
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def send_verification_success_email(user):
    """
    Send email confirmation after successful verification.
    
    Args:
        user: User instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Email Verified Successfully - {SYSTEM_NAME}'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✓ Email Verified!</h1>
                </div>
                <div class="content">
                    <h2>Hello {user.get_full_name()},</h2>
                    <p>Your email address has been successfully verified!</p>
                    <p>You can now access all features of the {SYSTEM_NAME}.</p>
                    <p>Thank you for completing your registration.</p>
                </div>
                <div class="footer">
                    <p>&copy; {YEAR} {SYSTEM_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Hello {user.get_full_name()},
        
        Your email address has been successfully verified!
        
        You can now access all features of the {SYSTEM_NAME}.
        
        Thank you for completing your registration.
        
        © {YEAR} {SYSTEM_NAME}. All rights reserved.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification success email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification success email to {user.email}: {e}")
        return False


def resend_verification_email(user):
    """
    Resend verification email to user.
    
    Args:
        user: User instance
    
    Returns:
        dict: Result with success status and message
    """
    from apps.authentication.models import EmailVerificationToken
    
    if user.is_verified:
        return {
            'success': False,
            'message': 'Email is already verified.'
        }
    
    # Invalidate old tokens
    EmailVerificationToken.objects.filter(
        user=user,
        is_used=False
    ).update(is_used=True)
    
    # Create new token
    token = EmailVerificationToken.objects.create(user=user)
    
    # Send email
    email_sent = send_verification_email(user, token)
    
    if email_sent:
        return {
            'success': True,
            'message': 'Verification email sent successfully.'
        }
    else:
        return {
            'success': False,
            'message': 'Failed to send verification email. Please try again.'
        }


def send_student_welcome_email(user, token, created_by=None):
    """
    Send welcome email to student created by teacher with verification instructions.
    
    Args:
        user: User instance (student)
        token: EmailVerificationToken instance
        created_by: User instance (teacher who created the account), optional
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Welcome to {SYSTEM_NAME} - Verify Your Email'
        
        verification_token = str(token.token)
        frontend_url = get_frontend_url()
        verification_link = f"{frontend_url}/verify-email?token={verification_token}"
        
        teacher_name = created_by.get_full_name() if created_by else "your teacher"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #1f2937;
                    background-color: #f3f4f6;
                    padding: 20px;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                    color: #ffffff;
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 28px;
                    font-weight: 700;
                    margin: 10px 0 0 0;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .content p {{
                    margin: 15px 0;
                    color: #4b5563;
                }}
                .info-box {{
                    background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 100%);
                    border-left: 4px solid #2563eb;
                    padding: 20px;
                    margin: 25px 0;
                    border-radius: 6px;
                }}
                .info-box strong {{
                    color: #1e40af;
                }}
                .info-box br {{
                    display: block;
                    content: "";
                    margin: 8px 0;
                }}
                .section-title {{
                    color: #1f2937;
                    font-size: 20px;
                    font-weight: 700;
                    margin: 30px 0 20px 0;
                }}
                .steps {{
                    background-color: #f9fafb;
                    padding: 25px;
                    border-radius: 8px;
                    margin: 25px 0;
                }}
                .step {{
                    display: flex;
                    align-items: start;
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #ffffff;
                    border-radius: 6px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }}
                .step-number {{
                    flex-shrink: 0;
                    width: 36px;
                    height: 36px;
                    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                    color: #ffffff;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 700;
                    font-size: 16px;
                    margin-right: 15px;
                }}
                .step-content {{
                    flex: 1;
                }}
                .step-content strong {{
                    color: #1f2937;
                    display: block;
                    margin-bottom: 5px;
                }}
                .button-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 16px 40px;
                    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                    color: #ffffff !important;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 700;
                    font-size: 16px;
                    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
                    transition: all 0.3s ease;
                }}
                .link-box {{
                    background-color: #f9fafb;
                    border: 2px dashed #d1d5db;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                    border-radius: 8px;
                }}
                .link-box a {{
                    color: #2563eb;
                    word-break: break-all;
                    font-size: 13px;
                    text-decoration: none;
                }}
                .warning-box {{
                    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                    border-left: 4px solid #f59e0b;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 25px 0;
                }}
                .warning-box strong {{
                    color: #92400e;
                }}
                .footer {{
                    padding: 30px;
                    text-align: center;
                    background-color: #f9fafb;
                    color: #6b7280;
                    font-size: 13px;
                    border-top: 1px solid #e5e7eb;
                }}
                .footer p {{
                    margin: 8px 0;
                }}
                .highlight {{
                    color: #2563eb;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div style="font-size: 48px;">🎓</div>
                    <h1>Welcome to AI Attendance System!</h1>
                </div>
                <div class="content">
                    <p>Dear <strong>{user.get_full_name()}</strong>,</p>
                    
                    <p>Your student account has been created by <span class="highlight">{teacher_name}</span> in the AI Attendance System.</p>
                    
                    <div class="info-box">
                        <strong>📧 Email:</strong> {user.email}<br>
                        <strong>👤 Name:</strong> {user.get_full_name()}<br>
                        <strong>{SYSTEM_ICON} Role:</strong> Student
                    </div>
                    
                    <h3 class="section-title">📋 Next Steps:</h3>
                    <div class="steps">
                        <div class="step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <strong>Verify Your Email</strong>
                                <span style="color: #6b7280;">Click the button below to verify your email address</span>
                            </div>
                        </div>
                        <div class="step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <strong>Login to Your Account</strong>
                                <span style="color: #6b7280;">Use your email and the password provided by your teacher</span>
                            </div>
                        </div>
                        <div class="step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <strong>Change Your Password</strong>
                                <span style="color: #6b7280;">Set a new secure password after your first login</span>
                            </div>
                        </div>
                        <div class="step">
                            <div class="step-number">4</div>
                            <div class="step-content">
                                <strong>Register Your Face</strong>
                                <span style="color: #6b7280;">Complete face registration for {SYSTEM_NAME}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="button-container">
                        <a href="{verification_link}" class="button">✓ Verify Email Address</a>
                    </div>
                    
                    <p style="text-align: center; color: #6b7280; font-size: 13px; margin-top: 15px;">Or copy this verification link:</p>
                    <div class="link-box">
                        <a href="{verification_link}">{verification_link}</a>
                    </div>
                    
                    <div class="warning-box">
                        <strong>⏰ Important:</strong> This verification link will expire in 48 hours. Please verify your email as soon as possible.
                    </div>
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #6b7280;">
                        If you have any questions, please contact <strong style="color: #1f2937;">{teacher_name}</strong> or the system administrator.
                    </p>
                </div>
                <div class="footer">
                    <p style="font-weight: 600; color: #1f2937;">© {YEAR} {SYSTEM_NAME}</p>
                    <p>All rights reserved.</p>
                    <p style="margin-top: 10px;">This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
Hello {user.get_full_name()},

Your student account has been created by {teacher_name} in the AI Attendance System.

Account Details:
- Email: {user.email}
- Name: {user.get_full_name()}
- Role: Student

NEXT STEPS:

1. Verify Your Email
   Click the link below to verify your email address:
   {verification_link}
   
2. Login to Your Account
   Use your email and the password provided by your teacher
   
3. Change Your Password
   Set a new secure password after your first login
   
4. Register Your Face
   Complete face registration for {SYSTEM_NAME}

IMPORTANT: This verification link will expire in 48 hours.

If you have any questions, please contact {teacher_name} or the system administrator.

© {YEAR} {SYSTEM_NAME}. All rights reserved.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Student welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send student welcome email to {user.email}: {e}")
        return False


def send_teacher_approval_email(user, approved_by=None):
    """
    Send approval notification email to teacher.
    
    Args:
        user: User instance (teacher)
        approved_by: User instance (admin who approved), optional
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Teacher Account Approved - {SYSTEM_NAME}'
        
        frontend_url = get_frontend_url()
        login_link = f"{frontend_url}/login"
        
        approver_name = approved_by.get_full_name() if approved_by else "Administrator"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 30px; background-color: #f9fafb; border: 1px solid #e5e7eb; }}
                .success-icon {{ font-size: 48px; text-align: center; margin: 20px 0; }}
                .button {{
                    display: inline-block;
                    padding: 14px 32px;
                    margin: 25px 0;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    text-align: center;
                }}
                .button:hover {{ background-color: #1d4ed8; }}
                .info-box {{ 
                    background-color: #dbeafe; 
                    border-left: 4px solid #2563eb; 
                    padding: 15px; 
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
                .highlight {{ color: #2563eb; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">🎉 Account Approved!</h1>
                </div>
                <div class="content">
                    <div class="success-icon">✅</div>
                    
                    <h2 style="color: #10b981; text-align: center;">Welcome to {SYSTEM_NAME}</h2>
                    
                    <p>Dear <strong>{user.get_full_name()}</strong>,</p>
                    
                    <p>Great news! Your teacher account has been approved by <span class="highlight">{approver_name}</span>.</p>
                    
                    <div class="info-box">
                        <strong>📧 Email:</strong> {user.email}<br>
                        <strong>👤 Role:</strong> Teacher<br>
                        <strong>✓ Status:</strong> Active
                    </div>
                    
                    <p>You now have full access to the AI Attendance System and can:</p>
                    <ul>
                        <li>✓ Manage student attendance</li>
                        <li>✓ Use AI-powered face recognition</li>
                        <li>✓ Create and manage courses</li>
                        <li>✓ Generate attendance reports</li>
                        <li>✓ Monitor student performance</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="{login_link}" class="button">Login to Your Account</a>
                    </div>
                    
                    <p style="margin-top: 25px; font-size: 14px; color: #6b7280;">
                        If you have any questions or need assistance, please don't hesitate to contact the system administrator.
                    </p>
                </div>
                <div class="footer">
                    <p>© {YEAR} {SYSTEM_NAME}. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Hello {user.get_full_name()},
        
        Great news! Your teacher account has been approved by {approver_name}.
        
        Account Details:
        - Email: {user.email}
        - Role: Teacher
        - Status: Active
        
        You now have full access to the {SYSTEM_NAME}.
        
        Login here: {login_link}
        
        Features you can access:
        - Manage student attendance
        - Use AI-powered face recognition
        - Create and manage courses
        - Generate attendance reports
        - Monitor student performance
        
        If you have any questions, please contact the system administrator.
        
        © {YEAR} {SYSTEM_NAME}. All rights reserved.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Teacher approval email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send teacher approval email to {user.email}: {e}")
        return False


def send_password_reset_email(user, token, ip_address=None):
    """
    Send password reset email to user.
    
    Args:
        user: User instance
        token: PasswordResetToken instance
        ip_address: IP address from which reset was requested
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Password Reset Request - {SYSTEM_NAME}'
        
        # Password reset token to be used by frontend
        reset_token = str(token.token)
        
        # Create reset link for frontend
        frontend_url = get_frontend_url()
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
        # Create HTML message with security information
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    margin: 20px 0;
                    background-color: #dc2626;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                .button:hover {{ background-color: #b91c1c; }}
                .token-box {{ 
                    background-color: #f0f0f0; 
                    border: 1px solid #dc2626; 
                    padding: 15px; 
                    margin: 20px 0; 
                    text-align: center; 
                    font-family: monospace; 
                    font-size: 12px; 
                    word-break: break-all;
                    border-radius: 5px;
                }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .security-info {{ background-color: #fef2f2; padding: 15px; border-left: 4px solid #dc2626; margin: 15px 0; }}
                .warning {{ background-color: #fffbeb; padding: 15px; border-left: 4px solid #f59e0b; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hello {user.get_full_name() or user.email},</h2>
                    <p>We received a request to reset the password for your {SYSTEM_NAME} account.</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    
                    <p style="text-align: center; color: #666; font-size: 12px;">Or copy this link:</p>
                    <div class="token-box">
                        <a href="{reset_link}" style="color: #dc2626; text-decoration: none; word-wrap: break-word;">{reset_link}</a>
                    </div>
                    
                    <div class="security-info">
                        <strong>🛡️ Security Information:</strong><br>
                        • This link will expire in <strong>1 hour</strong> for your security<br>
                        • Request time: {token.created_at.strftime('%Y-%m-%d at %H:%M:%S UTC')}<br>
                        {f"• Requested from IP: {ip_address}" if ip_address else ""}<br>
                        • Only the most recent reset link will work
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong><br>
                        • If you didn't request this password reset, please ignore this email<br>
                        • Your password will not be changed unless you click the link above<br>
                        • For security concerns, contact our support team immediately
                    </div>
                    
                    <p><strong>Need help?</strong> If you're having trouble with the link above, you can use this reset token directly on our password reset page:</p>
                    <div class="token-box" style="background-color: #fffbeb; border-color: #f59e0b;">
                        <strong>Reset Token:</strong><br>
                        {reset_token}
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; {YEAR} {SYSTEM_NAME}. All rights reserved.</p>
                    <p>This is an automated security email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text message as fallback
        text_message = f"""
        Password Reset Request - {SYSTEM_NAME}
        
        Hello {user.get_full_name() or user.email},
        
        We received a request to reset the password for your {SYSTEM_NAME} account.
        
        To reset your password, visit the following link:
        {reset_link}
        
        Or use this reset token on our password reset page:
        {reset_token}
        
        Security Information:
        • This link will expire in 1 hour for your security
        • Request time: {token.created_at.strftime('%Y-%m-%d at %H:%M:%S UTC')}
        {f"• Requested from IP: {ip_address}" if ip_address else ""}
        • Only the most recent reset link will work
        
        Important:
        • If you didn't request this password reset, please ignore this email
        • Your password will not be changed unless you click the link above
        • For security concerns, contact our support team immediately
        
        {SYSTEM_NAME} Team
        
        This is an automated security email. Please do not reply.
        """
        
        # Send email
        sent = send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message
        )
        
        if sent:
            logger.info(f"Password reset email sent to {user.email}")
        else:
            logger.warning(f"Password reset email sending returned False for {user.email}")
            
        return bool(sent)
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return False


def send_password_reset_success_email(user, ip_address=None, user_agent=None):
    """
    Send confirmation email after successful password reset.
    
    Args:
        user: User instance
        ip_address: IP address from which reset was completed
        user_agent: User agent string from reset completion
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Password Reset Successful - {SYSTEM_NAME}'
        
        # Create HTML message
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #059669; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .security-info {{ background-color: #f0fdf4; padding: 15px; border-left: 4px solid #059669; margin: 15px 0; }}
                .warning {{ background-color: #fef2f2; padding: 15px; border-left: 4px solid #dc2626; margin: 15px 0; }}
                .login-button {{
                    display: inline-block;
                    padding: 12px 30px;
                    margin: 20px 0;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Password Reset Successful</h1>
                </div>
                <div class="content">
                    <h2>Hello {user.get_full_name() or user.email},</h2>
                    <p>Your password for {SYSTEM_NAME} has been successfully reset.</p>
                    
                    <div class="security-info">
                        <strong>🔐 Security Details:</strong><br>
                        • Password changed at: {timezone.now().strftime('%Y-%m-%d at %H:%M:%S UTC')}<br>
                        {f"• Changed from IP: {ip_address}" if ip_address else ""}<br>
                        • All existing sessions have been logged out<br>
                        • You can now login with your new password
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{get_frontend_url()}/login" class="login-button">Login to Your Account</a>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Security Alert:</strong><br>
                        If you didn't reset your password, your account may be compromised. 
                        Please contact our support team immediately and change your password again.
                    </div>
                    
                    <p>For your security, we recommend:</p>
                    <ul>
                        <li>Using a strong, unique password</li>
                        <li>Enabling two-factor authentication if available</li>
                        <li>Regularly updating your password</li>
                        <li>Not sharing your login credentials</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>&copy; {YEAR} {SYSTEM_NAME}. All rights reserved.</p>
                    <p>This is an automated security notification. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text message as fallback
        text_message = f"""
        Password Reset Successful - {SYSTEM_NAME}
        
        Hello {user.get_full_name() or user.email},
        
        Your password for {SYSTEM_NAME} has been successfully reset.
        
        Security Details:
        • Password changed at: {timezone.now().strftime('%Y-%m-%d at %H:%M:%S UTC')}
        {f"• Changed from IP: {ip_address}" if ip_address else ""}
        • All existing sessions have been logged out
        • You can now login with your new password
        
        Security Alert:
        If you didn't reset your password, your account may be compromised. 
        Please contact our support team immediately and change your password again.
        
        For your security, we recommend:
        • Using a strong, unique password
        • Enabling two-factor authentication if available
        • Regularly updating your password
        • Not sharing your login credentials
        
        You can login at: {get_frontend_url()}/login
        
        {SYSTEM_NAME} Team
        
        This is an automated security notification. Please do not reply.
        """
        
        # Send email
        sent = send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message
        )
        
        if sent:
            logger.info(f"Password reset success notification sent to {user.email}")
        else:
            logger.warning(f"Password reset success notification failed to send to {user.email}")
            
        return bool(sent)
        
    except Exception as e:
        logger.error(f"Failed to send password reset success email to {user.email}: {e}")
        return False


def send_teacher_rejection_email(user, ip_address=None):
    """
    Send teacher account rejection notification email.
    
    Args:
        user: User instance
        ip_address: Optional IP address for security info
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        from django.utils import timezone
        
        subject = f'Teacher Account Application - {SYSTEM_NAME}'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                .warning {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{SYSTEM_ICON} {SYSTEM_NAME}</h1>
                    <h2>Teacher Account Application Status</h2>
                </div>
                <div class="content">
                    <p>Hello {user.get_full_name() or user.email},</p>
                    
                    <div class="warning">
                        <p><strong>We regret to inform you that your teacher account application has been rejected.</strong></p>
                    </div>
                    
                    <p>After reviewing your application, our administrators have decided that your request for a teacher account cannot be approved at this time.</p>
                    
                    <h3>What happens next:</h3>
                    <ul>
                        <li>Your account has been removed from our system</li>
                        <li>You will need to re-register if you wish to apply again</li>
                        <li>Please ensure you meet all requirements before reapplying</li>
                    </ul>
                    
                    <h3>If you believe this is an error:</h3>
                    <p>Please contact our support team with your application details and any supporting documentation.</p>
                    
                    <p>Thank you for your interest in {SYSTEM_NAME}.</p>
                </div>
                <div class="footer">
                    <p>{SYSTEM_NAME} - © {YEAR}</p>
                    <p>This is an automated notification. Please do not reply to this email.</p>
                    {f"<p>Notification sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>" if ip_address else ""}
                </div>
            </div>
        </body>
        </html>
        """
        
        text_message = f"""
        Teacher Account Application - {SYSTEM_NAME}
        
        Hello {user.get_full_name() or user.email},
        
        We regret to inform you that your teacher account application has been rejected.
        
        After reviewing your application, our administrators have decided that your request 
        for a teacher account cannot be approved at this time.
        
        What happens next:
        • Your account has been removed from our system
        • You will need to re-register if you wish to apply again
        • Please ensure you meet all requirements before reapplying
        
        If you believe this is an error:
        Please contact our support team with your application details and any supporting documentation.
        
        Thank you for your interest in {SYSTEM_NAME}.
        
        {SYSTEM_NAME} Team
        
        This is an automated notification. Please do not reply.
        """
        
        # Send email
        sent = send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message
        )
        
        if sent:
            logger.info(f"Teacher rejection notification sent to {user.email}")
        else:
            logger.warning(f"Teacher rejection notification failed to send to {user.email}")
            
        return bool(sent)
        
    except Exception as e:
        logger.error(f"Failed to send teacher rejection email to {user.email}: {e}")
        return False
