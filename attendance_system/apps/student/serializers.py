"""
Serializers for student management.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.student.models import (
    StudentProfile, Course, Enrollment, StudentFaceImage
)
from apps.authentication.serializers import UserRegistrationSerializer, UserSerializer

User = get_user_model()


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

    user = UserSerializer(read_only=True)
    face_images = StudentFaceImageSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'user', 'roll_number',
            'department', 'semester', 'is_face_registered',
            'face_encoding_updated_at', 'is_active', 'registration_date',
            'face_images', 'created_at'
        ]
        read_only_fields = [
            'is_face_registered', 'face_encoding_updated_at',
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
        user = super().create(validated_data)

        StudentProfile.objects.create(
            user=user,
            roll_number=validated_data['roll_number'],
            department=validated_data.get('department'),
            semester=validated_data.get('semester')
        )
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


class StudentStatsSerializer(serializers.Serializer):
    """Serializer for student statistics."""

    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    face_registered = serializers.IntegerField()
    courses_count = serializers.IntegerField()
