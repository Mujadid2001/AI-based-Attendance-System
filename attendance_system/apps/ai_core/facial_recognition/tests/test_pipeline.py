"""Unit tests for facial recognition pipeline."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import os
import tempfile


class TestFacialRecognitionPipeline(unittest.TestCase):
    """Test cases for FacialRecognitionPipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        from apps.ai_core.facial_recognition import FacialRecognitionPipeline
        from apps.ai_core.facial_recognition.storage import TrainingDataStorage
        
        self.storage = TrainingDataStorage()
        self.pipeline = FacialRecognitionPipeline(
            storage=self.storage,
            confidence_threshold=0.4,
            enable_quality_checks=False  # Disable for basic tests
        )
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes correctly."""
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline.confidence_threshold, 0.4)
        self.assertIsNotNone(self.pipeline.storage)
        self.assertIsNotNone(self.pipeline.face_recognizer)
        self.assertIsNotNone(self.pipeline.liveness_detector)
    
    @patch('face_recognition.face_locations')
    @patch('face_recognition.face_encodings')
    def test_register_face_success(self, mock_encodings, mock_locations):
        """Test successful face registration."""
        # Mock image
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock face detection and encoding
        mock_locations.return_value = [(100, 200, 300, 100)]
        mock_encoding = np.random.rand(128)
        mock_encodings.return_value = [mock_encoding]
        
        # Register face
        success, encoding, message = self.pipeline.register_face(test_image, "student123")
        
        self.assertTrue(success)
        self.assertIsNotNone(encoding)
        self.assertEqual(message, "Face registered successfully")
        self.assertEqual(self.pipeline.storage.count(), 1)
    
    @patch('face_recognition.face_locations')
    def test_register_face_no_face_detected(self, mock_locations):
        """Test registration fails when no face detected."""
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_locations.return_value = []
        
        success, encoding, message = self.pipeline.register_face(test_image, "student123")
        
        self.assertFalse(success)
        self.assertIsNone(encoding)
        self.assertIn("No face detected", message)
    
    @patch('face_recognition.face_locations')
    def test_register_face_multiple_faces(self, mock_locations):
        """Test registration fails with multiple faces."""
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_locations.return_value = [(100, 200, 300, 100), (400, 500, 600, 400)]
        
        success, encoding, message = self.pipeline.register_face(test_image, "student123")
        
        self.assertFalse(success)
        self.assertIsNone(encoding)
        self.assertIn("Multiple faces", message)
    
    @patch('face_recognition.face_locations')
    @patch('face_recognition.face_encodings')
    @patch('face_recognition.compare_faces')
    @patch('face_recognition.face_distance')
    def test_recognize_face_success(self, mock_distance, mock_compare, mock_encodings, mock_locations):
        """Test successful face recognition."""
        # Register a face first
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_locations.return_value = [(100, 200, 300, 100)]
        mock_encoding = np.random.rand(128)
        mock_encodings.return_value = [mock_encoding]
        
        self.pipeline.register_face(test_image, "student123", check_quality=False)
        
        # Now try to recognize
        mock_compare.return_value = [True]
        mock_distance.return_value = np.array([0.3])
        
        result = self.pipeline.recognize_face(test_image)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['student_id'], "student123")
        self.assertGreater(result['confidence'], 0.6)
    
    @patch('face_recognition.face_locations')
    @patch('face_recognition.face_encodings')
    @patch('face_recognition.compare_faces')
    @patch('face_recognition.face_distance')
    def test_recognize_face_no_match(self, mock_distance, mock_compare, mock_encodings, mock_locations):
        """Test recognition with no match found."""
        # Register a face
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_locations.return_value = [(100, 200, 300, 100)]
        mock_encoding = np.random.rand(128)
        mock_encodings.return_value = [mock_encoding]
        
        self.pipeline.register_face(test_image, "student123", check_quality=False)
        
        # Try to recognize with low confidence
        mock_compare.return_value = [False]
        mock_distance.return_value = np.array([0.8])
        
        result = self.pipeline.recognize_face(test_image)
        
        self.assertFalse(result['success'])
        self.assertIn("No match found", result['error'])
    
    def test_save_and_load_training_data(self):
        """Test saving and loading training data."""
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
            temp_path = f.name
        
        try:
            # Add some encodings
            self.storage.add_encoding("student1", np.random.rand(128))
            self.storage.add_encoding("student2", np.random.rand(128))
            
            # Save
            success = self.pipeline.save_training_data(temp_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_path))
            
            # Create new pipeline and load
            from apps.ai_core.facial_recognition import FacialRecognitionPipeline
            from apps.ai_core.facial_recognition.storage import TrainingDataStorage
            new_storage = TrainingDataStorage()
            new_pipeline = FacialRecognitionPipeline(storage=new_storage)
            success = new_pipeline.load_training_data(temp_path)
            
            self.assertTrue(success)
            self.assertEqual(new_storage.count(), 2)
            self.assertIn("student1", new_storage.get_all_ids())
            self.assertIn("student2", new_storage.get_all_ids())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestTrainingDataStorage(unittest.TestCase):
    """Test cases for TrainingDataStorage."""
    
    def setUp(self):
        """Set up test fixtures."""
        from apps.ai_core.facial_recognition.storage import TrainingDataStorage
        self.storage = TrainingDataStorage()
    
    def test_add_encoding(self):
        """Test adding encodings."""
        encoding = np.random.rand(128)
        self.storage.add_encoding("student1", encoding)
        
        self.assertEqual(self.storage.count(), 1)
        self.assertIn("student1", self.storage.get_all_ids())
        np.testing.assert_array_equal(self.storage.get_encoding("student1"), encoding)
    
    def test_remove_encoding(self):
        """Test removing encodings."""
        self.storage.add_encoding("student1", np.random.rand(128))
        self.storage.add_encoding("student2", np.random.rand(128))
        
        success = self.storage.remove_encoding("student1")
        
        self.assertTrue(success)
        self.assertEqual(self.storage.count(), 1)
        self.assertNotIn("student1", self.storage.get_all_ids())
    
    def test_clear(self):
        """Test clearing all encodings."""
        self.storage.add_encoding("student1", np.random.rand(128))
        self.storage.add_encoding("student2", np.random.rand(128))
        
        self.storage.clear()
        
        self.assertEqual(self.storage.count(), 0)
        self.assertEqual(len(self.storage.get_all_ids()), 0)
    
    def test_encryption_key_generation(self):
        """Test encryption key generation."""
        from apps.ai_core.facial_recognition.storage import TrainingDataStorage, HAS_CRYPTOGRAPHY
        
        if not HAS_CRYPTOGRAPHY:
            self.skipTest("Cryptography package not installed")
        
        storage = TrainingDataStorage(enable_encryption=True)
        key = storage.get_encryption_key()
        
        self.assertIsNotNone(key)
        self.assertIsInstance(key, bytes)


class TestFaceQualityChecker(unittest.TestCase):
    """Test cases for FaceQualityChecker."""
    
    def setUp(self):
        """Set up test fixtures."""
        from apps.ai_core.facial_recognition.utils import FaceQualityChecker
        self.checker = FaceQualityChecker()
    
    def test_check_blur_sharp_image(self):
        """Test blur check on sharp image."""
        # Create a sharp image with high variance
        sharp_image = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        
        is_sharp, score, message = self.checker.check_blur(sharp_image, threshold=10.0)
        
        self.assertTrue(is_sharp)
        self.assertGreater(score, 10.0)
    
    def test_check_blur_blurry_image(self):
        """Test blur check on blurry image."""
        # Create a very uniform (blurry) image
        blurry_image = np.ones((480, 640), dtype=np.uint8) * 128
        
        is_sharp, score, message = self.checker.check_blur(blurry_image, threshold=100.0)
        
        self.assertFalse(is_sharp)
        self.assertLess(score, 100.0)
    
    def test_check_brightness_good(self):
        """Test brightness check on well-lit image."""
        good_image = np.ones((480, 640), dtype=np.uint8) * 128
        
        is_good, brightness, message = self.checker.check_brightness(good_image)
        
        self.assertTrue(is_good)
        self.assertGreater(brightness, 40)
        self.assertLess(brightness, 220)
    
    def test_check_brightness_dark(self):
        """Test brightness check on dark image."""
        dark_image = np.ones((480, 640), dtype=np.uint8) * 20
        
        is_good, brightness, message = self.checker.check_brightness(dark_image)
        
        self.assertFalse(is_good)
        self.assertLess(brightness, 40)
    
    def test_check_brightness_bright(self):
        """Test brightness check on overexposed image."""
        bright_image = np.ones((480, 640), dtype=np.uint8) * 240
        
        is_good, brightness, message = self.checker.check_brightness(bright_image)
        
        self.assertFalse(is_good)
        self.assertGreater(brightness, 220)
    
    def test_check_face_size_good(self):
        """Test face size check with acceptable size."""
        face_location = (100, 250, 250, 100)  # 150x150 face
        
        is_good, size, message = self.checker.check_face_size(face_location)
        
        self.assertTrue(is_good)
        self.assertEqual(size, (150, 150))
    
    def test_check_face_size_too_small(self):
        """Test face size check with too small face."""
        face_location = (100, 130, 130, 100)  # 30x30 face
        
        is_good, size, message = self.checker.check_face_size(face_location)
        
        self.assertFalse(is_good)
        self.assertIn("too small", message)
    
    def test_check_all(self):
        """Test comprehensive quality check."""
        # Create decent quality image
        image = np.random.randint(80, 180, (480, 640), dtype=np.uint8)
        face_location = (100, 250, 250, 100)
        
        results = self.checker.check_all(image, face_location)
        
        self.assertIn('overall_pass', results)
        self.assertIn('checks', results)
        self.assertIn('messages', results)
        self.assertIn('blur', results['checks'])
        self.assertIn('brightness', results['checks'])
        self.assertIn('face_size', results['checks'])


class TestLivenessDetection(unittest.TestCase):
    """Test cases for liveness detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        from apps.ai_core.facial_recognition.liveness import (
            BlinkLivenessDetector, MotionLivenessDetector
        )
        self.blink_detector = BlinkLivenessDetector()
        self.motion_detector = MotionLivenessDetector()
    
    def test_blink_detector_initialization(self):
        """Test blink detector initialization."""
        self.assertIsNotNone(self.blink_detector)
        self.assertEqual(self.blink_detector.ear_threshold, 0.21)
        self.assertEqual(self.blink_detector.min_blinks, 1)
    
    def test_motion_detector_initialization(self):
        """Test motion detector initialization."""
        self.assertIsNotNone(self.motion_detector)
        self.assertEqual(self.motion_detector.motion_threshold, 0.02)
    
    def test_liveness_insufficient_frames(self):
        """Test liveness check with insufficient frames."""
        frames = [np.zeros((480, 640, 3), dtype=np.uint8)]
        
        # Should return True when insufficient frames
        result = self.blink_detector.check_liveness(frames)
        self.assertTrue(result)
    
    def test_motion_detection_static_frames(self):
        """Test motion detection with static frames."""
        # Create identical frames (no motion)
        frames = [np.ones((480, 640, 3), dtype=np.uint8) * 128] * 5
        
        result = self.motion_detector.check_liveness(frames)
        
        # Should detect no motion
        self.assertFalse(result)
    
    def test_motion_detection_with_motion(self):
        """Test motion detection with moving frames."""
        # Create frames with different content (motion)
        frames = [
            np.ones((480, 640, 3), dtype=np.uint8) * i * 40
            for i in range(5)
        ]
        
        result = self.motion_detector.check_liveness(frames)
        
        # Should detect motion
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
