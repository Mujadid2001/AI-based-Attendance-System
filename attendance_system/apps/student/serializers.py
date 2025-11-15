"""
Serializers for student management.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.student.models import (
    StudentProfile, Course, Enrollment, StudentFaceImage
)

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
            'is_full', 'is_active', 'created_at'
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
    
    user_email = serializers.CharField(
        source='user.email',
        read_only=True
    )
    full_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    phone = serializers.CharField(
        source='user.phone',
        read_only=True
    )
    face_images = StudentFaceImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = [
            'user', 'user_email', 'full_name', 'phone', 'roll_number',
            'department', 'semester', 'is_face_registered',
            'face_encoding_updated_at', 'is_active', 'registration_date',
            'face_images', 'created_at'
        ]
        read_only_fields = [
            'is_face_registered', 'face_encoding_updated_at',
            'created_at', 'face_images'
        ]


class StudentProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating StudentProfile."""
    
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
    
    def validate_roll_number(self, value):
        """Validate roll number uniqueness."""
        if StudentProfile.objects.filter(roll_number=value).exists():
            raise serializers.ValidationError(
                "Student with this roll number already exists."
            )
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already registered."
            )
        return value
    
    def create(self, validated_data):
        """Create student and user."""
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        phone = validated_data.pop('phone', '')
        
        # Create user
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=User.Role.STUDENT,
            password='DefaultPassword123!'
        )
        
        # Create student profile
        student = StudentProfile.objects.create(
            user=user,
            **validated_data
        )
        
        return student


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
