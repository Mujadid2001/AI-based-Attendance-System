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
    """Orchestrator for facial recognition operations.
    
    Uses a multi-model approach for maximum accuracy:
    1. CNN model for face detection (falls back to HOG if needed)
    2. Large model for face encoding (falls back to small model if needed)
    3. Distance-based matching with ambiguity detection
    """
    
    def __init__(self, face_detector=None, face_recognizer=None, confidence_threshold=0.4, storage=None, enable_quality_checks=True):
        """Initialize pipeline with accurate model hierarchy.
        
        Args:
            face_detector: Optional face detector (uses default if None)
            face_recognizer: Optional face recognizer (uses default if None)
            confidence_threshold: Minimum confidence for recognition (0.4 = 60% match accuracy)
            storage: Optional training data storage
            enable_quality_checks: Whether to check image quality during registration
        """
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
        
        # Initialize face aligner for better recognition
        try:
            from .alignment import FaceAligner
            self.face_aligner = FaceAligner()
        except Exception as e:
            logger.warning(f"Could not initialize face aligner: {e}")
            self.face_aligner = None
    
    def _convert_to_rgb(self, image):
        """Convert image to RGB format."""
        if not cv2 or not HAS_NUMPY:
            return image
        if len(image.shape) == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def _extract_face_encoding(self, image, check_quality=True):
        """Extract face encoding from image with optional quality checks.
        Uses accurate CNN model first, falls back to HOG if needed for better accuracy.
        
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
            
            # Apply lighting normalization
            if HAS_CV2 and len(rgb_image.shape) == 3:
                # Convert to LAB color space for better lighting handling
                lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
                l, a, b = cv2.split(lab)
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                # Merge and convert back
                lab = cv2.merge([l, a, b])
                rgb_image = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
            # Try CNN model first (most accurate)
            logger.info("Attempting face detection with CNN model (most accurate)...")
            face_locations = face_recognition.face_locations(rgb_image, model='cnn')
            model_used = 'cnn'
            
            # Fallback to HOG if CNN fails to detect
            if len(face_locations) == 0:
                logger.info("CNN model failed to detect face, falling back to HOG model...")
                face_locations = face_recognition.face_locations(rgb_image, model='hog')
                model_used = 'hog'
            
            if len(face_locations) == 0:
                return None, "No face detected in image (tried CNN and HOG models)", None
            elif len(face_locations) > 1:
                return None, "Multiple faces detected. Please ensure only one face is visible.", None
            
            face_location = face_locations[0]
            logger.info(f"Face detected successfully using {model_used.upper()} model")
            
            # Perform quality checks if enabled
            if check_quality and self.enable_quality_checks:
                quality_results = FaceQualityChecker.check_all(image, face_location)
                if not quality_results['overall_pass']:
                    error_msg = "Image quality issues: " + "; ".join(quality_results['messages'])
                    return None, error_msg, face_location
            
            # Align face for better recognition
            aligned_face = image
            if self.face_aligner:
                aligned_face = self.face_aligner.align_face(image, face_location)
                if aligned_face is not None:
                    # Update face location for aligned image (full image now)
                    face_location = (0, 0, aligned_face.shape[1], aligned_face.shape[0])
                else:
                    aligned_face = image
            
            # Extract encoding from aligned face using CNN for maximum accuracy
            rgb_aligned = self._convert_to_rgb(aligned_face)
            
            # Try with CNN model first (num_jitters=1 for balance of speed/accuracy)
            encodings = face_recognition.face_encodings(rgb_aligned, [face_location], num_jitters=1, model='large')
            
            if encodings:
                logger.info("Face encoding generated successfully using large model")
                return encodings[0], None, face_location
            else:
                # Fallback to small model if large fails
                logger.warning("Large model encoding failed, trying small model...")
                encodings = face_recognition.face_encodings(rgb_aligned, [face_location], num_jitters=1, model='small')
                if encodings:
                    logger.info("Face encoding generated successfully using small model")
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
            
            # Generate augmentations for robustness
            from .utils import DataAugmentation
            augmentations = DataAugmentation.generate_augmentations(image, num_augmentations=2)
            
            encodings = [encoding]  # Start with original
            
            # Extract encodings from augmentations
            for aug_image in augmentations:
                aug_encoding, _, _ = self._extract_face_encoding(aug_image, check_quality=False)
                if aug_encoding is not None:
                    encodings.append(aug_encoding)
            
            # Average encodings for better robustness
            if len(encodings) > 1:
                avg_encoding = np.mean(encodings, axis=0)
                # Normalize to unit vector
                avg_encoding = avg_encoding / np.linalg.norm(avg_encoding)
                final_encoding = avg_encoding
            else:
                final_encoding = encoding
            
            # Store averaged encoding
            self.storage.add_encoding(student_id, final_encoding)
            
            return True, final_encoding, "Face registered successfully"
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
            
            # Compare against all known encodings using accurate distance metric
            all_ids = self.storage.get_all_ids()
            known_encodings_list = []
            valid_ids = []
            
            # Validate and filter encodings
            for sid in all_ids:
                enc = self.storage.get_encoding(sid)
                if enc is not None and isinstance(enc, np.ndarray) and enc.shape == (128,):
                    known_encodings_list.append(enc)
                    valid_ids.append(sid)
                else:
                    logger.warning(f"Invalid encoding for student {sid}: type={type(enc)}, shape={enc.shape if hasattr(enc, 'shape') else 'N/A'}")
            
            if len(known_encodings_list) == 0:
                return {
                    'success': False,
                    'error': 'No valid encodings to compare against',
                    'face_detected': True,
                    'confidence': 0.0
                }
            
            # Convert to numpy array for face_recognition library
            known_encodings_array = np.array(known_encodings_list)
            
            # Use a stricter tolerance for initial matching (converted from confidence threshold)
            # Lower tolerance = stricter matching for better accuracy
            tolerance = 1 - self.confidence_threshold
            
            matches = face_recognition.compare_faces(
                known_encodings_array,
                encoding,
                tolerance=tolerance
            )
            face_distances = face_recognition.face_distance(
                known_encodings_array,
                encoding
            )
            
            if len(face_distances) == 0:
                return {
                    'success': False,
                    'error': 'No known encodings to compare against',
                    'face_detected': True,
                    'confidence': 0.0
                }
            
            # Find best match using distance (lower is better)
            best_match_index = np.argmin(face_distances) if HAS_NUMPY else face_distances.index(min(face_distances))
            best_distance = face_distances[best_match_index]
            confidence = 1 - best_distance
            
            # Additional validation: check if match is significantly better than second-best
            # This helps prevent false positives
            if len(face_distances) > 1:
                sorted_distances = sorted(enumerate(face_distances), key=lambda x: x[1])
                second_best_distance = sorted_distances[1][1]
                distance_gap = second_best_distance - best_distance
                
                # Require at least 0.05 gap between best and second-best for confident recognition
                if distance_gap < 0.05:
                    logger.warning(f"Ambiguous match: best_distance={best_distance:.3f}, second_best={second_best_distance:.3f}, gap={distance_gap:.3f}")
            
            if matches[best_match_index] and confidence >= self.confidence_threshold:
                student_id = valid_ids[best_match_index]
                logger.info(f"✓ Face recognized: student_id={student_id}, confidence={confidence:.3f}, distance={best_distance:.3f}")
                return {
                    'success': True,
                    'student_id': student_id,
                    'confidence': float(confidence),
                    'distance': float(best_distance),
                    'face_detected': True
                }
            else:
                logger.warning(f"✗ Recognition failed: best_confidence={confidence:.3f}, threshold={self.confidence_threshold}, match={matches[best_match_index]}")
                return {
                    'success': False,
                    'error': f'No match found (best confidence: {confidence:.3f}, required: {self.confidence_threshold})',
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
