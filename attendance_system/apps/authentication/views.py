"""
Views for authentication endpoints.
"""
import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout, get_user_model
from django.utils.translation import gettext_lazy as _
from apps.authentication.serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserUpdateSerializer, ChangePasswordSerializer, LoginLogSerializer
)
from apps.authentication.models import LoginLog
from apps.authentication.permissions import IsAdmin
from apps.student.models import StudentProfile
from apps.ai_core.services import get_ai_manager

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationViewSet(viewsets.ViewSet):
    """ViewSet for authentication operations."""
    
    def get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"New user registered: {user.email}")
            return Response(
                {
                    'message': _('Registration successful. Please log in.'),
                    'user': UserSerializer(user).data
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
            
            # Log successful login
            LoginLog.objects.create(
                user=user,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True
            )
            
            login(request, user)
            logger.info(f"User logged in: {user.email}")
            
            return Response(
                {
                    'message': _('Login successful.'),
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_200_OK
            )
        
        # Log failed login attempt
        email = request.data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                ip = self.get_client_ip(request)
                LoginLog.objects.create(
                    user=user,
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=False,
                    failure_reason='Invalid password'
                )
            except User.DoesNotExist:
                pass
        
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
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
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
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
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


class UserManagementViewSet(viewsets.ModelViewSet):
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
    
    def destroy(self, request, *args, **kwargs):
        """Delete user account."""
        user = self.get_object()
        email = user.email
        response = super().destroy(request, *args, **kwargs)
        logger.info(f"User deleted: {email}")
        return response
