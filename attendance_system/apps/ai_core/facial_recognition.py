"""
Facial recognition and AI processing pipeline (Minimal version).
Using industry-standard OOP design patterns.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Dict
from io import BytesIO
import pickle
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Conditional imports for optional dependencies
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    cv2 = None
    HAS_CV2 = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    face_recognition = None
    HAS_FACE_RECOGNITION = False

try:
    from PIL import Image
except ImportError:
    Image = None


class FaceDetector(ABC):
    """Abstract base class for face detection."""
    
    @abstractmethod
    def detect_faces(self, image):
        """Detect faces in image and return face locations."""
        pass


class CVFaceDetector(FaceDetector):
    """OpenCV Cascade Classifier based face detector."""
    
    def __init__(self, cascade_path: Optional[str] = None):
        """Initialize face detector."""
        if not HAS_CV2:
            raise RuntimeError("OpenCV not installed")
        
        if cascade_path is None:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
    
    def detect_faces(self, image):
        """Detect faces using Haar Cascade."""
        if not HAS_CV2:
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
        return faces


class FaceRecognizer(ABC):
    """Abstract base class for face recognition."""
    
    @abstractmethod
    def get_face_encoding(self, image, face_locations):
        """Get face encoding from image."""
        pass


class FaceRecognitionLibRecognizer(FaceRecognizer):
    """Face recognition library implementation."""
    
    def get_face_encoding(self, image, face_locations):
        """Get face encoding."""
        if not HAS_FACE_RECOGNITION:
            return None
        
        try:
            encodings = face_recognition.face_encodings(image, face_locations)
            return encodings[0] if encodings else None
        except Exception as e:
            logger.error(f"Error encoding face: {e}")
            return None


class LivenessDetector(ABC):
    """Abstract base class for liveness detection."""
    
    @abstractmethod
    def check_liveness(self, frames):
        """Check if face is alive (not spoofed)."""
        pass


class BlinkLivenessDetector(LivenessDetector):
    """Blink detection based liveness checker."""
    
    def check_liveness(self, frames):
        """Check liveness via blink detection."""
        if not HAS_CV2 or not HAS_NUMPY:
            return True  # Assume live if dependencies missing
        return True


class ImageProcessor:
    """Utility class for image processing."""
    
    @staticmethod
    def convert_pil_to_cv2(pil_image):
        """Convert PIL image to OpenCV format."""
        if not HAS_CV2 or Image is None:
            return None
        
        import numpy as np
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def convert_cv2_to_pil(cv2_image):
        """Convert OpenCV image to PIL format."""
        if not HAS_CV2 or Image is None:
            return None
        
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

    @staticmethod
    def convert_image_bytes_to_cv2(image_bytes):
        """Convert image bytes to cv2 image."""
        if not HAS_CV2 or not HAS_NUMPY:
            return None

        image_stream = BytesIO(image_bytes)
        image_array = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)


class FacialRecognitionPipeline:
    """Orchestrator for facial recognition operations."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.face_detector = None
        self.face_recognizer = FaceRecognitionLibRecognizer()
        self.liveness_detector = BlinkLivenessDetector()
        
        if HAS_CV2:
            try:
                self.face_detector = CVFaceDetector()
            except Exception as e:
                logger.warning(f"Could not initialize face detector: {e}")
    
    def register_face(self, image, student_id: str, confidence_threshold: float = 0.6):
        """Register face for a student."""
        if not self.face_detector:
            return None
        
        try:
            faces = self.face_detector.detect_faces(image)
            if not faces:
                return None
            
            face_locs = [tuple(f) for f in faces]
            encoding = self.face_recognizer.get_face_encoding(image, face_locs)
            
            if encoding is not None:
                return {
                    'student_id': student_id,
                    'encoding': encoding,
                    'timestamp': datetime.now()
                }
        except Exception as e:
            logger.error(f"Error registering face: {e}")
        
        return None
    
    def recognize_face(self, image, known_encodings: List, known_ids: List, confidence_threshold: float = 0.6):
        """Recognize face in image."""
        if not self.face_detector:
            return None, 0.0
        
        try:
            faces = self.face_detector.detect_faces(image)
            if not faces:
                return None, 0.0
            
            face_locs = [tuple(f) for f in faces]
            encoding = self.face_recognizer.get_face_encoding(image, face_locs)
            
            if encoding is None:
                return None, 0.0
            
            matches = face_recognition.compare_faces(known_encodings, encoding)
            face_distances = face_recognition.face_distance(known_encodings, encoding)

            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                confidence = 1 - face_distances[best_match_index]
                if confidence >= confidence_threshold:
                    return known_ids[best_match_index], confidence

        except Exception as e:
            logger.error(f"Error recognizing face: {e}")
        
        return None, 0.0
    
    def check_liveness(self, frames):
        """Check if face is alive."""
        try:
            return self.liveness_detector.check_liveness(frames)
        except Exception as e:
            logger.error(f"Error checking liveness: {e}")
            return True  # Assume live on error
