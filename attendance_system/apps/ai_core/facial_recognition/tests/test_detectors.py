"""Unit tests for face detectors."""
import unittest
from unittest.mock import Mock, patch
import numpy as np


class TestCVFaceDetector(unittest.TestCase):
    """Test cases for OpenCV face detector."""
    
    def setUp(self):
        """Set up test fixtures."""
        from apps.ai_core.facial_recognition.detectors import CVFaceDetector, HAS_CV2
        
        if not HAS_CV2:
            self.skipTest("OpenCV not installed")
        
        self.detector = CVFaceDetector()
    
    def test_detector_initialization(self):
        """Test detector initializes correctly."""
        self.assertIsNotNone(self.detector)
        self.assertIsNotNone(self.detector.face_cascade)
    
    @patch('cv2.CascadeClassifier.detectMultiScale')
    def test_detect_faces(self, mock_detect):
        """Test face detection."""
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_detect.return_value = np.array([[100, 100, 150, 150]])
        
        faces = self.detector.detect_faces(test_image)
        
        self.assertEqual(len(faces), 1)
        self.assertEqual(tuple(faces[0]), (100, 100, 150, 150))


class TestDNNFaceDetector(unittest.TestCase):
    """Test cases for DNN face detector."""
    
    def test_detector_initialization(self):
        """Test DNN detector initialization."""
        from apps.ai_core.facial_recognition.detectors import DNNFaceDetector, HAS_CV2
        
        if not HAS_CV2:
            self.skipTest("OpenCV not installed")
        
        detector = DNNFaceDetector()
        self.assertIsNotNone(detector)
    
    def test_detector_with_missing_models(self):
        """Test DNN detector handles missing model files gracefully."""
        from apps.ai_core.facial_recognition.detectors import DNNFaceDetector, HAS_CV2
        
        if not HAS_CV2:
            self.skipTest("OpenCV not installed")
        
        detector = DNNFaceDetector(
            model_path="/nonexistent/model.caffemodel",
            config_path="/nonexistent/config.prototxt"
        )
        
        # Should initialize but net should be None
        self.assertIsNone(detector.net)
        
        # Should return empty list when detecting
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = detector.detect_faces(test_image)
        self.assertEqual(len(faces), 0)


class TestMTCNNFaceDetector(unittest.TestCase):
    """Test cases for MTCNN face detector."""
    
    def test_detector_initialization_no_mtcnn(self):
        """Test MTCNN detector handles missing package."""
        from apps.ai_core.facial_recognition.detectors import MTCNNFaceDetector
        
        detector = MTCNNFaceDetector()
        self.assertIsNotNone(detector)
        
        # Should handle missing package gracefully
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = detector.detect_faces(test_image)
        self.assertIsInstance(faces, list)


class TestDlibFaceDetector(unittest.TestCase):
    """Test cases for Dlib face detector."""
    
    def test_detector_initialization_no_dlib(self):
        """Test Dlib detector handles missing package."""
        from apps.ai_core.facial_recognition.detectors import DlibFaceDetector
        
        detector = DlibFaceDetector()
        self.assertIsNotNone(detector)
        
        # Should handle missing package gracefully
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = detector.detect_faces(test_image)
        self.assertIsInstance(faces, list)


if __name__ == '__main__':
    unittest.main()
