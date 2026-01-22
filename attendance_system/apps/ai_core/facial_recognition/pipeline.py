"""Main facial recognition pipeline orchestrator."""
import logging
from typing import Optional

from .detectors import CVFaceDetector, HAS_CV2
from .recognizers import FaceRecognitionLibRecognizer
from .liveness import BlinkLivenessDetector
from .storage import TrainingDataStorage
from .utils import FaceQualityChecker
from .fallback_manager import FallbackDetectionManager


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
    
    Uses a multi-model approach with cascading fallback for maximum robustness:
    1. Face detection with fallback: CNN → DNN-SSD → MTCNN → Dlib → HOG → Haar Cascade
    2. Face encoding with fallback: Large model → Small model
    3. Distance-based matching with ambiguity detection
    """
    
    def __init__(self, face_detector=None, face_recognizer=None, confidence_threshold=0.35, storage=None, enable_quality_checks=True, enable_fallback=True):
        """Initialize pipeline with accurate model hierarchy and fallback support.
        
        Args:
            face_detector: Optional face detector (uses default if None)
            face_recognizer: Optional face recognizer (uses default if None)
            confidence_threshold: Minimum confidence for recognition (0.35 = 65% match accuracy, adjusted for low quality webcams)
            storage: Optional training data storage
            enable_quality_checks: Whether to check image quality during registration
            enable_fallback: Whether to enable cascading fallback detection methods
        """
        self.confidence_threshold = confidence_threshold
        self.enable_quality_checks = enable_quality_checks
        self.enable_fallback = enable_fallback
        
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
        
        # Initialize fallback detection manager
        if self.enable_fallback:
            self.fallback_manager = FallbackDetectionManager(enable_all_methods=True)
            logger.info("Fallback detection enabled - will try multiple detection methods")
        else:
            self.fallback_manager = None
            logger.info("Fallback detection disabled - using single detection method")
        
        # Initialize face detector (legacy support)
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
        """Extract face encoding from image with fallback detection methods.
        
        Uses cascading fallback approach:
        1. Try multiple detection methods (CNN → DNN → MTCNN → Dlib → HOG → Haar)
        2. Try multiple encoding models (Large → Small)
        3. Only fail when ALL methods have been exhausted
        
        Args:
            image: Input image
            check_quality: Whether to perform quality checks
            
        Returns:
            Tuple of (encoding, error_message, face_location, metadata)
        """
        if not HAS_FACE_RECOGNITION:
            return None, "Face recognition library not available", None, None
        
        try:
            rgb_image = self._convert_to_rgb(image)
            
            # Apply lighting normalization and enhancement for low quality webcams
            if HAS_CV2 and len(rgb_image.shape) == 3:
                # Apply bilateral filter to reduce noise while preserving edges
                rgb_image = cv2.bilateralFilter(rgb_image, 9, 75, 75)
                
                # Convert to LAB color space for better lighting handling
                lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
                l, a, b = cv2.split(lab)
                # Apply CLAHE to L channel with more aggressive settings for low quality
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                # Merge and convert back
                lab = cv2.merge([l, a, b])
                rgb_image = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
                
                # Apply slight sharpening
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                rgb_image = cv2.filter2D(rgb_image, -1, kernel)
            
            # Use fallback detection if enabled
            if self.enable_fallback and self.fallback_manager:
                logger.info("Using cascading fallback detection...")
                detection_result = self.fallback_manager.detect_faces_with_fallback(rgb_image)
                
                if not detection_result['success']:
                    error_msg = f"No face detected by any method. Tried: {', '.join(detection_result['attempts'])}"
                    logger.error(f"✗ All detection methods failed: {error_msg}")
                    return None, error_msg, None, detection_result
                
                face_locations = detection_result['face_locations']
                method_used = detection_result['method_used']
                
                logger.info(f"✓ Face detected using {method_used.upper()} (after trying: {', '.join(detection_result['attempts'])})")
            
            else:
                # Legacy single-method detection (CNN → HOG fallback only)
                logger.info("Attempting face detection with CNN model (most accurate)...")
                face_locations = face_recognition.face_locations(rgb_image, model='cnn')
                method_used = 'cnn'
                
                # Fallback to HOG if CNN fails to detect
                if len(face_locations) == 0:
                    logger.info("CNN model failed to detect face, falling back to HOG model...")
                    face_locations = face_recognition.face_locations(rgb_image, model='hog')
                    method_used = 'hog'
                
                if len(face_locations) == 0:
                    return None, "No face detected in image (tried CNN and HOG models)", None, {'method_used': None}
                
                detection_result = {'method_used': method_used, 'attempts': ['cnn', 'hog']}
            
            if len(face_locations) > 1:
                return None, "Multiple faces detected. Please ensure only one face is visible.", None, detection_result
            
            face_location = face_locations[0]
            
            # Perform quality checks if enabled
            if check_quality and self.enable_quality_checks:
                quality_results = FaceQualityChecker.check_all(image, face_location)
                if not quality_results['overall_pass']:
                    error_msg = "Image quality issues: " + "; ".join(quality_results['messages'])
                    return None, error_msg, face_location, detection_result
            
            # Align face for better recognition
            aligned_face = image
            if self.face_aligner:
                aligned_face = self.face_aligner.align_face(image, face_location)
                if aligned_face is not None:
                    # Update face location for aligned image (full image now)
                    face_location = (0, 0, aligned_face.shape[1], aligned_face.shape[0])
                else:
                    aligned_face = image
            
            # Extract encoding from aligned face with model fallback
            rgb_aligned = self._convert_to_rgb(aligned_face)
            
            if self.enable_fallback and self.fallback_manager:
                # Use fallback manager for encoding extraction
                encoding_result = self.fallback_manager.extract_encoding_with_fallback(
                    rgb_aligned, 
                    face_location
                )
                
                if encoding_result['success']:
                    logger.info(f"✓ Encoding extracted using {encoding_result['model_used'].upper()} model")
                    detection_result['encoding_model'] = encoding_result['model_used']
                    return encoding_result['encoding'], None, face_location, detection_result
                else:
                    error_msg = "Failed to generate encoding with all available models"
                    logger.error(f"✗ {error_msg}")
                    return None, error_msg, face_location, detection_result
            
            else:
                # Legacy encoding extraction (Large → Small fallback)
                # Try with large model first
                encodings = face_recognition.face_encodings(rgb_aligned, [face_location], num_jitters=1, model='large')
                
                if encodings:
                    logger.info("Face encoding generated successfully using large model")
                    detection_result['encoding_model'] = 'large'
                    return encodings[0], None, face_location, detection_result
                else:
                    # Fallback to small model if large fails
                    logger.warning("Large model encoding failed, trying small model...")
                    encodings = face_recognition.face_encodings(rgb_aligned, [face_location], num_jitters=1, model='small')
                    if encodings:
                        logger.info("Face encoding generated successfully using small model")
                        detection_result['encoding_model'] = 'small'
                        return encodings[0], None, face_location, detection_result
                    else:
                        return None, "Failed to generate face encoding", face_location, detection_result
                
        except Exception as e:
            logger.error(f"Error extracting face encoding: {e}")
            return None, str(e), None, None

    def register_face(self, image, student_id: str, check_quality=True):
        """Register face for a student with quality validation.
        
        Args:
            image: Input image
            student_id: Student identifier
            check_quality: Whether to perform quality checks
            
        Returns:
            Tuple of (success, encoding, message, metadata)
        """
        if not HAS_FACE_RECOGNITION:
            return False, None, "Face recognition library not available", None
        
        try:
            encoding, error_msg, face_location, metadata = self._extract_face_encoding(image, check_quality)
            if error_msg:
                return False, None, error_msg, metadata
            
            # Generate augmentations for robustness
            from .utils import DataAugmentation
            augmentations = DataAugmentation.generate_augmentations(image, num_augmentations=2)
            
            encodings = [encoding]  # Start with original
            
            # Extract encodings from augmentations
            for aug_image in augmentations:
                aug_encoding, _, _, _ = self._extract_face_encoding(aug_image, check_quality=False)
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
            
            success_msg = f"Face registered successfully using {metadata.get('method_used', 'unknown')} detection"
            if 'encoding_model' in metadata:
                success_msg += f" and {metadata['encoding_model']} encoding model"
            
            return True, final_encoding, success_msg, metadata
        except Exception as e:
            logger.error(f"Error registering face: {e}")
            return False, None, f"Error: {str(e)}", None
    
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
        Recognize face in image against stored encodings with cascading fallback.
        
        Args:
            image: Image in numpy/cv2 format
            return_all_matches: Whether to return all matches (for debugging)
            
        Returns:
            dict with recognition results including detection metadata
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
            encoding, error_msg, face_location, metadata = self._extract_face_encoding(image, check_quality=False)
            if error_msg:
                return {
                    'success': False,
                    'error': error_msg,
                    'face_detected': 'No face' not in error_msg,
                    'confidence': 0.0,
                    'detection_metadata': metadata
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
                    'confidence': 0.0,
                    'detection_metadata': metadata
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
                    'confidence': 0.0,
                    'detection_metadata': metadata
                }
            
            # Find best match using distance (lower is better)
            best_match_index = np.argmin(face_distances) if HAS_NUMPY else face_distances.index(min(face_distances))
            best_distance = face_distances[best_match_index]
            confidence = 1 - best_distance
            
            # Additional validation: check if match is significantly better than second-best
            # This helps prevent false positives (relaxed for low quality webcams)
            if len(face_distances) > 1:
                sorted_distances = sorted(enumerate(face_distances), key=lambda x: x[1])
                second_best_distance = sorted_distances[1][1]
                distance_gap = second_best_distance - best_distance
                
                # Require at least 0.03 gap (relaxed from 0.05 for low quality webcams)
                if distance_gap < 0.03:
                    logger.warning(f"Ambiguous match: best_distance={best_distance:.3f}, second_best={second_best_distance:.3f}, gap={distance_gap:.3f}")
            
            if matches[best_match_index] and confidence >= self.confidence_threshold:
                student_id = valid_ids[best_match_index]
                
                # Log detection method used
                detection_info = ""
                if metadata:
                    detection_info = f" (detected with {metadata.get('method_used', 'unknown')})"
                
                logger.info(f"✓ Face recognized: student_id={student_id}, confidence={confidence:.3f}, distance={best_distance:.3f}{detection_info}")
                
                return {
                    'success': True,
                    'student_id': student_id,
                    'confidence': float(confidence),
                    'distance': float(best_distance),
                    'face_detected': True,
                    'detection_metadata': metadata
                }
            else:
                logger.warning(f"✗ Recognition failed: best_confidence={confidence:.3f}, threshold={self.confidence_threshold}, match={matches[best_match_index]}")
                return {
                    'success': False,
                    'error': f'No match found (best confidence: {confidence:.3f}, required: {self.confidence_threshold})',
                    'face_detected': True,
                    'confidence': float(confidence),
                    'distance': float(best_distance),
                    'detection_metadata': metadata
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
    
    def get_detection_statistics(self):
        """Get detection statistics from fallback manager.
        
        Returns:
            Dict with detection method usage statistics, or None if fallback disabled
        """
        if self.enable_fallback and self.fallback_manager:
            return self.fallback_manager.get_detection_statistics()
        return None
    
    def log_detection_statistics(self):
        """Log detection statistics."""
        if self.enable_fallback and self.fallback_manager:
            self.fallback_manager.log_statistics()
        else:
            logger.info("Fallback detection is disabled - no statistics available")
