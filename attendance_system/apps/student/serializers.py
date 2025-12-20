"""
Serializers for student management.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.student.models import (
    StudentProfile, Course, Enrollment, StudentFaceImage
)
from apps.authentication.serializers import UserRegistrationSerializer, UserSerializer
from apps.authentication.models import EmailVerificationToken
from apps.authentication.email_utils import send_student_welcome_email
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""

    instructor_name = serializers.CharField(
        source='instructor.get_full_name',
        read_only=True
    )
    student_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'code', 'name', 'description', 'instructor',
            'instructor_name', 'max_students', 'student_count',
            'is_full', 'is_active', 'semester', 'year',
            'start_date', 'end_date', 'created_at'
        ]
        read_only_fields = ['created_at']

    def get_student_count(self, obj):
        return obj.student_count()

    def get_is_full(self, obj):
        return obj.is_full()


class StudentFaceImageSerializer(serializers.ModelSerializer):
    """Serializer for StudentFaceImage model."""

    class Meta:
        model = StudentFaceImage
        fields = [
            'id', 'image', 'is_verified', 'is_training_data', 'created_at'
        ]
        read_only_fields = ['created_at']


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for StudentProfile model."""

    id = serializers.IntegerField(source='user.id', read_only=True)
    user = UserSerializer(read_only=True)
    face_images = StudentFaceImageSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'roll_number',
            'department', 'semester', 'is_face_registered',
            'face_encoding_updated_at', 'is_active', 'registration_date',
            'face_images', 'created_at'
        ]
        read_only_fields = [
            'id', 'is_face_registered', 'face_encoding_updated_at',
            'created_at', 'face_images'
        ]


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating StudentProfile."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = StudentProfile
        fields = [
            'roll_number', 'email', 'first_name', 'last_name', 'phone',
            'department', 'semester'
        ]

    def update(self, instance, validated_data):
        """Update student and user."""
        user_data = {
            'first_name': validated_data.pop('first_name', instance.user.first_name),
            'last_name': validated_data.pop('last_name', instance.user.last_name),
            'email': validated_data.pop('email', instance.user.email),
            'phone': validated_data.pop('phone', instance.user.phone),
        }
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

class StudentUserRegistrationSerializer(UserRegistrationSerializer):
    """Serializer for student registration, combining user and profile creation."""

    roll_number = serializers.CharField(max_length=50)
    department = serializers.CharField(max_length=100, required=False)
    semester = serializers.IntegerField(required=False)

    class Meta(UserRegistrationSerializer.Meta):
        # Exclude 'role' from fields - it will be set automatically to STUDENT
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'password', 'password_confirm',
            'roll_number', 'department', 'semester'
        ]

    def validate_roll_number(self, value):
        """Validate roll number uniqueness."""
        if StudentProfile.objects.filter(roll_number=value).exists():
            raise serializers.ValidationError(
                "Student with this roll number already exists."
            )
        return value

    def create(self, validated_data):
        """Create student user and profile."""
        # Always set role to STUDENT - users cannot send this field
        validated_data['role'] = User.Role.STUDENT
        
        # Get the request to identify who is creating the student
        request = self.context.get('request')
        created_by = request.user if request and request.user.is_authenticated else None
        
        # Create user account
        user = super().create(validated_data)
        
        # Create student profile
        StudentProfile.objects.create(
            user=user,
            roll_number=validated_data['roll_number'],
            department=validated_data.get('department'),
            semester=validated_data.get('semester')
        )
        
        # Create verification token and send welcome email
        try:
            token = EmailVerificationToken.objects.create(user=user)
            email_sent = send_student_welcome_email(user, token, created_by=created_by)
            if email_sent:
                logger.info(f"Welcome email sent to new student: {user.email} (created by {created_by})")
            else:
                logger.warning(f"Failed to send welcome email to: {user.email}")
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
        
        return user


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model."""

    student_roll = serializers.CharField(
        source='student.roll_number',
        read_only=True
    )
    course_code = serializers.CharField(
        source='course.code',
        read_only=True
    )
    course_name = serializers.CharField(
        source='course.name',
        read_only=True
    )

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_roll', 'course', 'course_code',
            'course_name', 'is_active', 'enrollment_date'
        ]
        read_only_fields = ['enrollment_date']


class EnrollmentWithStudentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model with nested student profile."""

    student = StudentProfileSerializer(read_only=True)
    course_code = serializers.CharField(
        source='course.code',
        read_only=True
    )
    course_name = serializers.CharField(
        source='course.name',
        read_only=True
    )

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'course', 'course_code',
            'course_name', 'is_active', 'enrollment_date'
        ]
        read_only_fields = ['enrollment_date']


class StudentStatsSerializer(serializers.Serializer):
    """Serializer for student statistics."""

    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    face_registered = serializers.IntegerField()
    courses_count = serializers.IntegerField()
