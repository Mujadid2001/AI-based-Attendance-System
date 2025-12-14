"""Abstract base classes for facial recognition components using Strategy Pattern."""
from abc import ABC, abstractmethod


class FaceDetector(ABC):
    """Abstract base class for face detection."""
    
    @abstractmethod
    def detect_faces(self, image):
        """Detect faces in image and return face locations."""
        pass


class FaceRecognizer(ABC):
    """Abstract base class for face recognition."""
    
    @abstractmethod
    def get_face_encoding(self, image, face_locations):
        """Get face encoding from image."""
        pass


class LivenessDetector(ABC):
    """Abstract base class for liveness detection."""
    
    @abstractmethod
    def check_liveness(self, frames):
        """Check if face is alive (not spoofed)."""
        pass
