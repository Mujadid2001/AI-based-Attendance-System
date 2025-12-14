"""Unit tests for face alignment."""
import unittest
from unittest.mock import Mock, patch
import numpy as np


class TestFaceAligner(unittest.TestCase):
    """Test cases for FaceAligner."""
    
    def setUp(self):
        """Set up test fixtures."""
        from attendance_system.apps.ai_core.facial_recognition.alignment import FaceAligner
        self.aligner = FaceAligner()
    
    def test_aligner_initialization(self):
        """Test aligner initialization."""
        self.assertIsNotNone(self.aligner)
        self.assertEqual(self.aligner.desired_face_width, 256)
    
    def test_align_without_landmarks(self):
        """Test alignment returns original image when landmarks unavailable."""
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # If predictor not available, should return original
        if self.aligner.predictor is None:
            result = self.aligner.align_face(test_image)
            np.testing.assert_array_equal(result, test_image)


class TestSimpleFaceAligner(unittest.TestCase):
    """Test cases for SimpleFaceAligner."""
    
    def setUp(self):
        """Set up test fixtures."""
        from attendance_system.apps.ai_core.facial_recognition.alignment import SimpleFaceAligner, HAS_OPENCV
        
        if not HAS_OPENCV:
            self.skipTest("OpenCV not installed")
        
        self.aligner = SimpleFaceAligner(target_size=(160, 160))
    
    def test_aligner_initialization(self):
        """Test simple aligner initialization."""
        self.assertIsNotNone(self.aligner)
        self.assertEqual(self.aligner.target_size, (160, 160))
        self.assertEqual(self.aligner.margin, 0.2)
    
    def test_align_face(self):
        """Test simple face alignment."""
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        face_rect = (100, 100, 200, 200)
        
        aligned = self.aligner.align_face(test_image, face_rect)
        
        self.assertIsNotNone(aligned)
        self.assertEqual(aligned.shape[:2], self.aligner.target_size)
    
    def test_align_face_with_margin(self):
        """Test alignment includes margin around face."""
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        face_rect = (200, 200, 100, 100)
        
        aligned = self.aligner.align_face(test_image, face_rect)
        
        self.assertIsNotNone(aligned)
        # Should be resized to target size
        self.assertEqual(aligned.shape[:2], self.aligner.target_size)
    
    def test_align_face_edge_case(self):
        """Test alignment handles edge cases (face near image boundary)."""
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        face_rect = (0, 0, 50, 50)  # Face at corner
        
        aligned = self.aligner.align_face(test_image, face_rect)
        
        self.assertIsNotNone(aligned)
        self.assertEqual(aligned.shape[:2], self.aligner.target_size)


if __name__ == '__main__':
    unittest.main()
