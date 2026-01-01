"""Serializers for Camera Integration."""
from rest_framework import serializers
from django.conf import settings
from utils.network import get_server_base_url
from .models import ExternalCameraSource, CameraStreamSession


class ExternalCameraSourceSerializer(serializers.ModelSerializer):
    """Serializer for External Camera Source."""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    camera_url = serializers.SerializerMethodField()
    session_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExternalCameraSource
        fields = [
            'id', 'name', 'device_id', 'device_type', 'status',
            'last_connected', 'is_enabled', 'auto_mark_attendance',
            'created_by', 'created_by_username', 'created_by_name',
            'created_at', 'updated_at', 'qr_code_url', 'camera_url',
            'session_count', 'access_token'
        ]
        read_only_fields = ['id', 'access_token', 'created_at', 'updated_at', 'status', 'last_connected']
    
    def get_qr_code_url(self, obj):
        """Get URL for QR code generation."""
        request = self.context.get('request')
        if request:
            # Use dynamic network detection for consistency
            base_url = get_server_base_url(
                request=request,
                force_detect=getattr(settings, 'FORCE_DYNAMIC_IP_DETECTION', False)
            )
            return f"{base_url}/api/camera/sources/{obj.id}/qr-code/"
        return None
    
    def get_camera_url(self, obj):
        """Get URL for mobile camera interface."""
        request = self.context.get('request')
        if request:
            # Use dynamic network detection for mobile accessibility
            base_url = get_server_base_url(
                request=request,
                force_detect=getattr(settings, 'FORCE_DYNAMIC_IP_DETECTION', False)
            )
            return f"{base_url}/camera.html?id={obj.id}&token={obj.access_token}"
        return None
    
    def get_session_count(self, obj):
        """Get total session count."""
        return obj.stream_sessions.count()


class ExternalCameraSourceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating External Camera Source."""
    
    class Meta:
        model = ExternalCameraSource
        fields = ['name', 'device_id', 'device_type', 'auto_mark_attendance']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CameraStreamSessionSerializer(serializers.ModelSerializer):
    """Serializer for Camera Stream Session."""
    
    camera_name = serializers.CharField(source='camera_source.name', read_only=True)
    attendance_session_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = CameraStreamSession
        fields = [
            'id', 'camera_source', 'camera_name', 'attendance_session',
            'attendance_session_name', 'started_at', 'ended_at',
            'frames_received', 'faces_detected', 'faces_recognized',
            'attendance_marked', 'duration'
        ]
        read_only_fields = ['id', 'started_at', 'ended_at']
    
    def get_attendance_session_name(self, obj):
        """Get attendance session name."""
        if obj.attendance_session:
            return f"{obj.attendance_session.course.name} - {obj.attendance_session.date}"
        return None
    
    def get_duration(self, obj):
        """Calculate session duration in seconds."""
        if obj.ended_at and obj.started_at:
            return (obj.ended_at - obj.started_at).total_seconds()
        return None


class ExternalCameraFrameSerializer(serializers.Serializer):
    """Serializer for receiving camera frames from external sources."""
    
    image = serializers.ImageField(required=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    attendance_session_id = serializers.IntegerField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, allow_null=True)
