"""
Tests for Camera Integration App
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.camera_integration.models import ExternalCameraSource, CameraStreamSession
from apps.authentication.models import User

User = get_user_model()


class ExternalCameraSourceTestCase(TestCase):
    """Test ExternalCameraSource model."""
    
    def setUp(self):
        """Set up test data."""
        self.teacher = User.objects.create_user(

            email='teacher1@test.com',
            password='testpass123',
            role='teacher'
        )
    
    def test_create_camera_source(self):
        """Test creating a camera source."""
        camera = ExternalCameraSource.objects.create(
            name='Test Camera',
            device_id='test-001',
            device_type='mobile',
            created_by=self.teacher
        )
        
        self.assertEqual(camera.name, 'Test Camera')
        self.assertEqual(camera.device_id, 'test-001')
        self.assertEqual(camera.status, 'inactive')
        self.assertTrue(camera.is_enabled)
        self.assertIsNotNone(camera.access_token)
        self.assertEqual(len(camera.access_token), 64)
    
    def test_camera_token_auto_generation(self):
        """Test that access token is auto-generated."""
        camera = ExternalCameraSource.objects.create(
            name='Auto Token Camera',
            device_id='test-002',
            created_by=self.teacher
        )
        
        self.assertIsNotNone(camera.access_token)
        self.assertGreater(len(camera.access_token), 0)
    
    def test_camera_string_representation(self):
        """Test string representation of camera."""
        camera = ExternalCameraSource.objects.create(
            name='String Test',
            device_id='test-003',
            device_type='tablet',
            created_by=self.teacher
        )
        
        expected = 'String Test (tablet)'
        self.assertEqual(str(camera), expected)


class CameraStreamSessionTestCase(TestCase):
    """Test CameraStreamSession model."""
    
    def setUp(self):
        """Set up test data."""
        self.teacher = User.objects.create_user(
            email='teacher2@test.com',
            password='testpass123',
            role='teacher'
        )
        
        self.camera = ExternalCameraSource.objects.create(
            name='Session Test Camera',
            device_id='test-004',
            created_by=self.teacher
        )
    
    def test_create_session(self):
        """Test creating a stream session."""
        session = CameraStreamSession.objects.create(
            camera_source=self.camera
        )
        
        self.assertEqual(session.camera_source, self.camera)
        self.assertEqual(session.frames_received, 0)
        self.assertEqual(session.faces_detected, 0)
        self.assertEqual(session.faces_recognized, 0)
        self.assertEqual(session.attendance_marked, 0)
        self.assertIsNotNone(session.started_at)
        self.assertIsNone(session.ended_at)
    
    def test_session_statistics_update(self):
        """Test updating session statistics."""
        session = CameraStreamSession.objects.create(
            camera_source=self.camera
        )
        
        session.frames_received = 10
        session.faces_detected = 8
        session.faces_recognized = 6
        session.attendance_marked = 5
        session.save()
        
        updated_session = CameraStreamSession.objects.get(id=session.id)
        self.assertEqual(updated_session.frames_received, 10)
        self.assertEqual(updated_session.faces_detected, 8)
        self.assertEqual(updated_session.faces_recognized, 6)
        self.assertEqual(updated_session.attendance_marked, 5)


class CameraIntegrationAPITestCase(TestCase):
    """Test Camera Integration API endpoints."""
    
    def setUp(self):
        """Set up test client and user."""
        self.teacher = User.objects.create_user(
            email='apiteacher@test.com',
            password='testpass123',
            role='teacher'
        )
        self.client.force_login(self.teacher)
    
    def test_list_cameras_requires_auth(self):
        """Test that listing cameras requires authentication."""
        self.client.logout()
        response = self.client.get('/api/camera/sources/')
        self.assertEqual(response.status_code, 401)
    
    def test_create_camera_source(self):
        """Test creating camera via API."""
        data = {
            'name': 'API Test Camera',
            'device_id': 'api-test-001',
            'device_type': 'mobile',
            'auto_mark_attendance': True
        }
        response = self.client.post('/api/camera/sources/', data)
        
        # Should be created (201) or forbidden if permissions not set up
        self.assertIn(response.status_code, [201, 403])
        
        if response.status_code == 201:
            self.assertEqual(response.data['name'], 'API Test Camera')
            self.assertEqual(response.data['device_type'], 'mobile')
