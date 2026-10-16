"""
Views for authentication endpoints.
"""

import contextlib
import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout, get_user_model
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from apps.authentication.serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserUpdateSerializer, ChangePasswordSerializer, LoginLogSerializer,
    EmailVerificationSerializer, ResendVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from apps.authentication.models import LoginLog, EmailVerificationToken, PasswordResetToken
from apps.authentication.email_utils import (
    send_verification_email, send_verification_success_email, resend_verification_email,
    send_teacher_approval_email, send_password_reset_email, send_password_reset_success_email
)
from apps.authentication.permissions import IsAdmin
from apps.student.models import StudentProfile
from apps.ai_core.services import get_ai_manager
from utils.viewsets import ClientIPMixin, BaseModelViewSet

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationViewSet(ClientIPMixin, viewsets.ViewSet):
    """ViewSet for authentication operations."""
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create StudentProfile automatically for student users
            if user.role == User.Role.STUDENT:
                # Generate temporary roll number that user can update later
                temp_roll = f"TEMP-{user.id}"
                StudentProfile.objects.create(
                    user=user,
                    roll_number=temp_roll,
                    is_active=True
                )
                logger.info(f"StudentProfile created for self-registered student: {user.email} with roll number: {temp_roll}")
            
            # Create verification token and send email
            token = EmailVerificationToken.objects.create(user=user)
            email_sent = send_verification_email(user, token)
            
            logger.info(f"New user registered: {user.email} (Role: {user.role}, Approved: {user.is_approved})")
            
            # Different messages based on role and approval status
            if user.role == User.Role.TEACHER and not user.is_approved:
                message = _('Registration successful! Your teacher account is pending admin approval. You will receive an email notification once your account is reviewed and approved.')
            else:
                message = _('Registration successful. Please check your email to verify your account.')
                if not email_sent:
                    message = _('Registration successful, but verification email could not be sent. Please request a new verification email.')
            
            return Response(
                {
                    'message': message,
                    'user': UserSerializer(user).data,
                    'email_sent': email_sent,
                    'requires_approval': user.role == User.Role.TEACHER and not user.is_approved
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_student_with_face(self, request):
        """Register new student with face capture."""
        # Extract form data
        user_data = {
            'email': request.data.get('email'),
            'password': request.data.get('password'),
            'password_confirm': request.data.get('password'),  # Use same password for confirmation
            'first_name': request.data.get('first_name'),
            'last_name': request.data.get('last_name'),
            'role': User.Role.STUDENT,  # Set role as student
        }
        
        # Extract student profile data
        student_data = {
            'roll_number': request.data.get('roll_number'),
            'department': request.data.get('department'),
            'semester': request.data.get('semester'),
        }
        
        # Get face image
        face_image = request.FILES.get('face_image')
        
        if not face_image:
            return Response(
                {'error': _('Face image is required for registration.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate user data
        user_serializer = UserRegistrationSerializer(data=user_data)
        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create user account
            user = user_serializer.save()
            user.user_role = 'student'
            user.save()
            
            # Create student profile
            student = StudentProfile.objects.create(
                user=user,
                roll_number=student_data['roll_number'],
                department=student_data['department'],
                semester=int(student_data['semester'])
            )
            
            # Register face
            ai_manager = get_ai_manager()
            face_result = ai_manager.register_student_face(face_image, student)
            
            if not face_result['success']:
                # Delete created user and student if face registration fails
                student.delete()
                user.delete()
                return Response(
                    {'error': f'Face registration failed: {face_result["message"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Student registered with face: {user.email} - {student.roll_number}")
            
            return Response(
                {
                    'message': _('Registration successful! Your face has been registered for attendance.'),
                    'user': UserSerializer(user).data,
                    'student': {
                        'id': student.id,
                        'roll_number': student.roll_number,
                        'department': student.department,
                        'semester': student.semester,
                        'is_face_registered': student.is_face_registered
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            # Cleanup if anything goes wrong
            try:
                if 'student' in locals():
                    student.delete()
                if 'user' in locals():
                    user.delete()
            except:
                pass
            
            return Response(
                {'error': _('Registration failed. Please try again.')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Login user."""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            ip = self.get_client_ip(request)

            # Check if email is verified (mandatory in production, optional in development)
            from django.conf import settings
            if not user.is_verified and not settings.DEBUG:
                return Response(
                    {
                        'error': _('Please verify your email address before logging in.'),
                        'requires_verification': True
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if teacher account is approved
            if user.role == User.Role.TEACHER and not user.is_approved:
                return Response(
                    {
                        'error': _('Your teacher account is pending admin approval. Please wait for approval to access the system.'),
                        'requires_approval': True
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # Log successful login
            LoginLog.objects.create(
                user=user,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True
            )

            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            login(request, user)
            logger.info(f"User logged in: {user.email}")

            return Response(
                {
                    'message': _('Login successful.'),
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    },
                    'is_verified': user.is_verified
                },
                status=status.HTTP_200_OK
            )

        # Log failed login attempt
        if email := request.data.get('email'):
            with contextlib.suppress(User.DoesNotExist):
                user = User.objects.get(email=email)
                ip = self.get_client_ip(request)
                LoginLog.objects.create(
                    user=user,
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=False,
                    failure_reason='Invalid password'
                )
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user."""
        user_email = request.user.email
        logout(request)
        logger.info(f"User logged out: {user_email}")
        return Response(
            {'message': _('Logout successful.')},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user details."""
        try:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in /me/ endpoint: {e}")
            return Response(
                {'error': 'Failed to retrieve user details'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated], url_path='profile-update')
    def profile_update(self, request):
        """Update user profile."""
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User profile updated: {request.user.email}")
            return Response(
                {
                    'message': _('Profile updated successfully.'),
                    'user': UserSerializer(request.user).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': _('Old password is incorrect.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            logger.info(f"Password changed for user: {user.email}")
            
            return Response(
                {'message': _('Password changed successfully.')},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, IsAdmin]
    )
    def login_logs(self, request):
        """Get login logs (admin only)."""
        logs = LoginLog.objects.all().order_by('-timestamp')
        
        # Pagination
        page = request.query_params.get('page', 1)
        page_size = 20
        start = (int(page) - 1) * page_size
        end = start + page_size
        
        serializer = LoginLogSerializer(logs[start:end], many=True)
        return Response(
            {
                'count': logs.count(),
                'results': serializer.data
            }
        )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='verify-email')
    def verify_email(self, request):
        """Verify user email with token."""
        from django.utils.decorators import method_decorator
        from django.views.decorators.csrf import csrf_exempt
        
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            user = token.user
            
            # Mark token as used
            token.is_used = True
            token.save()
            
            # Mark user as verified
            user.is_verified = True
            user.save()
            
            # Send success email
            send_verification_success_email(user)
            
            logger.info(f"Email verified for user: {user.email}")
            
            return Response(
                {
                    'message': _('Email verified successfully! You can now log in.'),
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def resend_verification(self, request):
        """Resend verification email."""
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['email']
            
            # Use the utility function to resend
            result = resend_verification_email(user)
            
            if result['success']:
                logger.info(f"Verification email resent to: {user.email}")
                return Response(
                    {'message': result['message']},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': result['message']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='forgot-password')
    def forgot_password(self, request):
        """Request password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Try to get user - if user doesn't exist, we still return success for security
            try:
                user = User.objects.get(email=email)
                
                if not user.is_active:
                    # Don't create token for inactive users but still return success
                    return Response(
                        {'message': _('If an account with this email exists, you will receive a password reset email shortly.')},
                        status=status.HTTP_200_OK
                    )
                
                # Deactivate any existing password reset tokens for this user
                PasswordResetToken.objects.filter(
                    user=user,
                    is_used=False
                ).update(is_used=True)
                
                # Create new password reset token
                token = PasswordResetToken.objects.create(
                    user=user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
                )
                
                # Send password reset email
                email_sent = send_password_reset_email(
                    user, 
                    token, 
                    ip_address=self.get_client_ip(request)
                )
                
                logger.info(f"Password reset requested for user: {user.email} from IP: {self.get_client_ip(request)}")
                
            except User.DoesNotExist:
                # For security, don't reveal if email exists
                logger.info(f"Password reset requested for non-existent email: {email} from IP: {self.get_client_ip(request)}")
            
            # Always return success response for security
            return Response(
                {'message': _('If an account with this email exists, you will receive a password reset email shortly.')},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='reset-password')
    def reset_password(self, request):
        """Confirm password reset with token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            user = token.user
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            token.is_used = True
            token.save()
            
            # Deactivate all other password reset tokens for this user
            PasswordResetToken.objects.filter(
                user=user,
                is_used=False
            ).exclude(id=token.id).update(is_used=True)
            
            # Send success notification email
            send_password_reset_success_email(
                user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.info(f"Password reset completed for user: {user.email} from IP: {self.get_client_ip(request)}")
            
            return Response(
                {
                    'message': _('Password reset successful! You can now log in with your new password.'),
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def verification_status(self, request):
        """Get email verification status for current user."""
        user = request.user
        return Response(
            {
                'is_verified': user.is_verified,
                'email': user.email,
                'user': UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )


class UserManagementViewSet(BaseModelViewSet):
    """ViewSet for user management (admin only)."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_queryset(self):
        """Filter users by role if specified."""
        queryset = User.objects.all()
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user account."""
        user = self.get_object()
        user.is_active = True
        user.save()
        logger.info(f"User activated: {user.email}")
        return Response({'message': _('User activated.')})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user account."""
        user = self.get_object()
        user.is_active = False
        user.save()
        logger.info(f"User deactivated: {user.email}")
        return Response({'message': _('User deactivated.')})
    
    @action(detail=True, methods=['post'])
    def approve_teacher(self, request, pk=None):
        """Approve a pending teacher account."""
        user = self.get_object()
        
        if user.role != User.Role.TEACHER:
            return Response(
                {'error': _('User is not a teacher.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.is_approved:
            return Response(
                {'error': _('Teacher is already approved.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_approved = True
        user.save()
        
        logger.info(f"Teacher approved: {user.email} by {request.user.email}")
        
        # Send approval notification email
        email_sent = send_teacher_approval_email(user, approved_by=request.user)
        
        return Response({
            'message': _('Teacher account approved successfully.'),
            'user': UserSerializer(user).data,
            'email_sent': email_sent
        })
    
    @action(detail=True, methods=['post'])
    def reject_teacher(self, request, pk=None):
        """Reject a pending teacher account (delete)."""
        user = self.get_object()
        
        if user.role != User.Role.TEACHER:
            return Response(
                {'error': _('User is not a teacher.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = user.email
        user.delete()
        
        logger.info(f"Teacher rejected and deleted: {email} by {request.user.email}")
        
        # Send rejection notification email
        try:
            from apps.authentication.email_utils import send_teacher_rejection_email
            send_teacher_rejection_email(user)
        except Exception as e:
            logger.warning(f"Failed to send rejection email to {email}: {e}")
        
        return Response({'message': _('Teacher account rejected and removed.')})
    
    @action(detail=False, methods=['get'])
    def pending_teachers(self, request):
        """Get list of teachers pending approval."""
        pending = User.objects.filter(
            role=User.Role.TEACHER,
            is_approved=False
        ).order_by('-created_at')
        
        serializer = UserSerializer(pending, many=True)
        return Response(serializer.data)
    

    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user account."""
        user = self.get_object()
        user.is_active = False
        user.save()
        logger.info(f"User deactivated: {user.email}")
        return Response({'message': _('User deactivated.')})
    
    def destroy(self, request, *args, **kwargs):
        """Delete user account."""
        user = self.get_object()
        email = user.email
        response = super().destroy(request, *args, **kwargs)
        logger.info(f"User deleted: {email}")
        return response
