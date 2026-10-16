"""Face recognition implementations."""
import logging

from .base import FaceRecognizer


logger = logging.getLogger(__name__)

# Conditional imports for optional dependencies
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    face_recognition = None
    HAS_FACE_RECOGNITION = False


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
