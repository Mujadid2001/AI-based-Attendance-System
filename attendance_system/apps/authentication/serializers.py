"""
Serializers for authentication endpoints.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from apps.authentication.models import LoginLog

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    role = serializers.ChoiceField(choices=User.Role.choices)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone', 'role',
            'password', 'password_confirm'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, data):
        """Validate passwords match."""
        if data.get('password') != data.pop('password_confirm'):
            raise serializers.ValidationError(
                _("Passwords don't match.")
            )
        return data
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("Email address already registered.")
            )
        return value
    
    def create(self, validated_data):
        """Create new user."""
        return User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone'),
            role=validated_data.get('role', User.Role.STUDENT),
            password=validated_data['password'],
        )
        


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, data):
        """Authenticate user."""
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(
                username=email,
                password=password
            )
            if not user:
                raise serializers.ValidationError(
                    _("Invalid email or password.")
                )
            data['user'] = user
        else:
            raise serializers.ValidationError(
                _("Email and password are required.")
            )
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    
    role_display = serializers.CharField(
        source='get_role_display_verbose',
        read_only=True
    )
    full_name = serializers.CharField(
        source='get_full_name',
        read_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'role_display', 'profile_picture',
            'is_verified', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates."""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'profile_picture'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField(
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        """Validate passwords."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(
                _("New passwords don't match.")
            )
        return data


class LoginLogSerializer(serializers.ModelSerializer):
    """Serializer for login logs."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = LoginLog
        fields = [
            'id', 'user', 'user_email', 'ip_address', 'success',
            'failure_reason', 'timestamp'
        ]
        read_only_fields = fields
