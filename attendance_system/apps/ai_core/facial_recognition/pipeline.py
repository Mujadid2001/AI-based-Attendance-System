"""Main facial recognition pipeline orchestrator."""
import logging
from typing import Optional

from .detectors import CVFaceDetector, HAS_CV2
from .recognizers import FaceRecognitionLibRecognizer
from .liveness import BlinkLivenessDetector
from .storage import TrainingDataStorage
from .utils import FaceQualityChecker


logger = logging.getLogger(__name__)

# Conditional imports for optional dependencies
try:
    import cv2
except ImportError:
    cv2 = None

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


class FacialRecognitionPipeline:
    """Orchestrator for facial recognition operations."""
    
    def __init__(self, face_detector=None, face_recognizer=None, confidence_threshold=0.5, storage=None, enable_quality_checks=True):
        """Initialize pipeline with lower confidence threshold for lower quality webcams."""
        self.confidence_threshold = confidence_threshold
        self.enable_quality_checks = enable_quality_checks
        
        # Initialize storage
        if storage:
            self.storage = storage
        else:
            self.storage = TrainingDataStorage()
        
        # Backward compatibility properties
        self.known_encodings = self.storage.known_encodings
        self.known_ids = self.storage.known_ids

        # Initialize recognizer
        if face_recognizer:
            self.face_recognizer = face_recognizer
        else:
            self.face_recognizer = FaceRecognitionLibRecognizer()
        
        # Initialize liveness detector
        self.liveness_detector = BlinkLivenessDetector()
        
        # Initialize face detector
        if face_detector:
            self.face_detector = face_detector
        elif HAS_CV2:
            try:
                self.face_detector = CVFaceDetector()
            except Exception as e:
                logger.warning(f"Could not initialize face detector: {e}")
                self.face_detector = None
        else:
            self.face_detector = None
    
    def _convert_to_rgb(self, image):
        """Convert image to RGB format."""
        if not cv2 or not HAS_NUMPY:
            return image
        if len(image.shape) == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def _extract_face_encoding(self, image, check_quality=True):
        """Extract face encoding from image with optional quality checks.
        
        Args:
            image: Input image
            check_quality: Whether to perform quality checks
            
        Returns:
            Tuple of (encoding, error_message, face_location)
        """
        if not HAS_FACE_RECOGNITION:
            return None, "Face recognition library not available", None
        
        try:
            rgb_image = self._convert_to_rgb(image)
            face_locations = face_recognition.face_locations(rgb_image, model='hog')
            
            if len(face_locations) == 0:
                return None, "No face detected in image", None
            elif len(face_locations) > 1:
                return None, "Multiple faces detected. Please ensure only one face is visible.", None
            
            face_location = face_locations[0]
            
            # Perform quality checks if enabled
            if check_quality and self.enable_quality_checks:
                quality_results = FaceQualityChecker.check_all(image, face_location)
                if not quality_results['overall_pass']:
                    error_msg = "Image quality issues: " + "; ".join(quality_results['messages'])
                    return None, error_msg, face_location
            
            # Extract encoding
            encodings = face_recognition.face_encodings(rgb_image, face_locations)
            if encodings:
                return encodings[0], None, face_location
            else:
                return None, "Failed to generate face encoding", face_location
                
        except Exception as e:
            logger.error(f"Error extracting face encoding: {e}")
            return None, str(e), None

    def register_face(self, image, student_id: str, check_quality=True):
        """Register face for a student with quality validation.
        
        Args:
            image: Input image
            student_id: Student identifier
            check_quality: Whether to perform quality checks
            
        Returns:
            Tuple of (success, encoding, message)
        """
        if not HAS_FACE_RECOGNITION:
            return False, None, "Face recognition library not available"
        
        try:
            encoding, error_msg, face_location = self._extract_face_encoding(image, check_quality)
            if error_msg:
                return False, None, error_msg
            
            # Store encoding with student ID
            self.storage.add_encoding(student_id, encoding)
            
            return True, encoding, "Face registered successfully"
        except Exception as e:
            logger.error(f"Error registering face: {e}")
            return False, None, f"Error: {str(e)}"
    
    def load_training_data(self, path: str):
        """Load training data from file."""
        result = self.storage.load_from_file(path)
        # Update backward compatibility references
        self.known_encodings = self.storage.known_encodings
        self.known_ids = self.storage.known_ids
        return result
    
    def save_training_data(self, path: str):
        """Save training data to file."""
        return self.storage.save_to_file(path)
    
    def recognize_face(self, image, return_all_matches: bool = False):
        """
        Recognize face in image against stored encodings.
        
        Args:
            image: Image in numpy/cv2 format
            return_all_matches: Whether to return all matches (for debugging)
            
        Returns:
            dict with recognition results
        """
        if not HAS_FACE_RECOGNITION or self.storage.count() == 0:
            logger.warning(f"Recognition failed: HAS_FACE_RECOGNITION={HAS_FACE_RECOGNITION}, storage count={self.storage.count()}")
            return {
                'success': False,
                'error': 'No enrolled faces or recognition library unavailable',
                'face_detected': False,
                'confidence': 0.0
            }
        
        try:
            encoding, error_msg, face_location = self._extract_face_encoding(image, check_quality=False)
            if error_msg:
                return {
                    'success': False,
                    'error': error_msg,
                    'face_detected': 'No face' not in error_msg,
                    'confidence': 0.0
                }
            
            # Compare against all known encodings
            all_ids = self.storage.get_all_ids()
            known_encodings_list = [self.storage.get_encoding(sid) for sid in all_ids]
            matches = face_recognition.compare_faces(
                known_encodings_list,
                encoding,
                tolerance=1 - self.confidence_threshold
            )
            face_distances = face_recognition.face_distance(
                known_encodings_list,
                encoding
            )
            
            if len(face_distances) == 0:
                return {
                    'success': False,
                    'error': 'No known encodings to compare against',
                    'face_detected': True,
                    'confidence': 0.0
                }
            
            best_match_index = np.argmin(face_distances) if HAS_NUMPY else face_distances.index(min(face_distances))
            best_distance = face_distances[best_match_index]
            confidence = 1 - best_distance
            
            if matches[best_match_index] and confidence >= self.confidence_threshold:
                student_id = all_ids[best_match_index]
                logger.info(f"Face recognized: student_id={student_id}, confidence={confidence:.2f}")
                return {
                    'success': True,
                    'student_id': student_id,
                    'confidence': float(confidence),
                    'distance': float(best_distance),
                    'face_detected': True
                }
            else:
                logger.warning(f"Recognition failed: best_confidence={confidence:.2f}, threshold={self.confidence_threshold}, match={matches[best_match_index]}")
                return {
                    'success': False,
                    'error': f'No match found (best confidence: {confidence:.2f}, required: {self.confidence_threshold})',
                    'face_detected': True,
                    'confidence': float(confidence),
                    'distance': float(best_distance)
                }
        
        except Exception as e:
            logger.error(f"Error recognizing face: {e}")
            return {
                'success': False,
                'error': str(e),
                'face_detected': False,
                'confidence': 0.0
            }
    
    def check_liveness(self, frames):
        """Check if face is alive."""
        try:
            return self.liveness_detector.check_liveness(frames)
        except Exception as e:
            logger.error(f"Error checking liveness: {e}")
            return True  # Assume live on error
