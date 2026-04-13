"""Production-grade facial recognition pipeline with intelligent detection."""
import logging
from typing import Optional, Tuple, Dict, Any, List

from .recognizers import FaceRecognitionLibRecognizer
from .liveness import BlinkLivenessDetector
from .storage import TrainingDataStorage
from .utils import FaceQualityChecker
from .preprocessing import ImagePreprocessor
from .detection_orchestrator import IntelligentDetectionOrchestrator, DetectionConfidenceCalculator

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False


class FacialRecognitionPipeline:
    """Production-grade facial recognition pipeline.
    
    Implements intelligent cascading with:
    - Adaptive image preprocessing
    - Confidence-based detection orchestration
    - Quality-aware encoding extraction
    - Distance-based robust recognition
    """
    
    def __init__(self, face_recognizer=None, confidence_threshold: float = 0.70,
                 storage=None, enable_quality_checks: bool = True,
                 enable_preprocessing: bool = True, encoding_num_jitters: int = 1):
        """Initialize pipeline.
        
        Args:
            face_recognizer: Optional recognizer instance
            confidence_threshold: Minimum detection confidence (0.70 = 70% quality)
            storage: Optional training data storage
            enable_quality_checks: Enable image quality validation
            enable_preprocessing: Enable adaptive preprocessing
            encoding_num_jitters: Number of times to resample for encoding (accuracy vs speed)
        """
        if not HAS_FACE_RECOGNITION:
            raise RuntimeError("face_recognition library not installed")
        
        self.confidence_threshold = confidence_threshold
        self.enable_quality_checks = enable_quality_checks
        self.enable_preprocessing = enable_preprocessing
        self.encoding_num_jitters = encoding_num_jitters
        
        self.storage = storage or TrainingDataStorage()
        self.face_recognizer = face_recognizer or FaceRecognitionLibRecognizer()
        self.liveness_detector = BlinkLivenessDetector()
        self.preprocessor = ImagePreprocessor(enable_adaptive_preprocessing=True)
        self.detection_orchestrator = IntelligentDetectionOrchestrator(
            confidence_threshold=confidence_threshold,
            enable_preprocessing=enable_preprocessing
        )
        
        # Backward compatibility
        self.known_encodings = self.storage.known_encodings
        self.known_ids = self.storage.known_ids
        
        logger.info(f"Pipeline initialized with confidence_threshold={confidence_threshold}")
    
    def _detect_face(self, image: np.ndarray) -> Tuple[bool, Optional[Tuple], Dict]:
        """Detect a single face using intelligent orchestration.
        
        Args:
            image: Input image (BGR)
            
        Returns:
            Tuple of (success, face_location, metadata)
        """
        try:
            preprocessing_metadata = None
            working_image = image.copy()
            
            if self.enable_preprocessing:
                working_image, preprocessing_metadata = self.preprocessor.preprocess(
                    image, aggressive=False
                )
            
            result = self.detection_orchestrator.detect_faces_intelligently(
                working_image, preprocessing_metadata
            )
            
            if result.success and result.meets_quality_threshold:
                return True, result.face_locations[0], {
                    'confidence': result.confidence_score,
                    'method': result.method_used,
                    'quality_metrics': result.quality_metrics,
                }
            elif result.success:
                logger.warning(f"Detection confidence {result.confidence_score:.2f} below threshold")
                return False, None, {'reason': 'insufficient_confidence'}
            else:
                return False, None, {'reason': result.stop_reason}
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return False, None, {'error': str(e)}
    
    def _extract_encoding(self, image: np.ndarray, face_location: Tuple) -> Optional[np.ndarray]:
        """Extract face encoding from detected face.
        
        Args:
            image: Input image (BGR)
            face_location: Face location tuple (top, right, bottom, left)
            
        Returns:
            128-dimensional encoding or None
        """
        try:
            rgb_image = np.array(image)
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = image[:, :, ::-1]  # BGR to RGB
            
            encodings = face_recognition.face_encodings(
                rgb_image,
                [face_location],
                num_jitters=self.encoding_num_jitters,
                model='large'
            )
            
            if encodings:
                return encodings[0]
            
            # Fallback to small model
            logger.warning("Large encoding model failed, trying small model")
            encodings = face_recognition.face_encodings(
                rgb_image,
                [face_location],
                num_jitters=max(1, self.encoding_num_jitters // 2),
                model='small'
            )
            
            return encodings[0] if encodings else None
        
        except Exception as e:
            logger.error(f"Encoding extraction failed: {e}")
            return None
    
    def register_face(self, image: np.ndarray, student_id: str, max_attempts: int = 1) -> Tuple[bool, Optional[np.ndarray], str, Dict]:
        """Register a student's face for recognition.
        
        Args:
            image: Input image (BGR)
            student_id: Unique student identifier
            max_attempts: Maximum registration attempts (for compatibility)
            
        Returns:
            Tuple of (success, encoding, message, metadata)
        """
        try:
            if self.enable_quality_checks:
                is_acceptable, quality_msg = FaceQualityChecker.check_image_suitability(image)
                if not is_acceptable:
                    metadata = {
                        'processing_method': 'quality_check_failed',
                        'attempt_used': 0,
                        'quality_issue': quality_msg,
                        'attempts_log': []
                    }
                    return False, None, f"Image quality issue: {quality_msg}", metadata
            
            success, face_location, detection_metadata = self._detect_face(image)
            if not success:
                metadata = {
                    'processing_method': 'detection_failed',
                    'attempt_used': 0,
                    'reason': detection_metadata.get('reason', 'unknown'),
                    'attempts_log': []
                }
                return False, None, f"Face detection failed", metadata
            
            encoding = self._extract_encoding(image, face_location)
            if encoding is None:
                metadata = {
                    'processing_method': 'encoding_failed',
                    'attempt_used': 1,
                    'attempts_log': []
                }
                return False, None, "Failed to generate face encoding", metadata
            
            self.storage.add_encoding(student_id, encoding)
            
            metadata = {
                'processing_method': detection_metadata.get('method', 'orchestrated'),
                'attempt_used': 1,
                'quality_score': detection_metadata.get('confidence', 0.0),
                'environment': 'unknown',
                'encodings_averaged': 1,
                'attempts_log': [{
                    'method': detection_metadata.get('method', 'orchestrated'),
                    'quality_score': detection_metadata.get('confidence', 0.0),
                    'error': None,
                    'face_detected': True
                }],
                'emergency_mode': False
            }
            
            logger.info(f"✓ Face registered for student {student_id}")
            return True, encoding, f"Face successfully registered for {student_id}", metadata
        
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            metadata = {
                'processing_method': 'error',
                'attempt_used': 0,
                'error': str(e),
                'attempts_log': []
            }
            return False, None, str(e), metadata
    
    def recognize_face(self, image: np.ndarray, distance_threshold: float = 0.6,
                      return_all_matches: bool = False) -> Dict[str, Any]:
        """Recognize a face in an image.
        
        Args:
            image: Input image (BGR)
            distance_threshold: Maximum distance for positive match (lower = stricter)
            return_all_matches: Whether to return all matches or just best
            
        Returns:
            Recognition result dict with 'success' key
        """
        try:
            success, face_location, detection_metadata = self._detect_face(image)
            if not success:
                return {
                    'success': False,
                    'error': detection_metadata.get('reason', 'detection_failed'),
                    'face_detected': False,
                    'confidence': 0.0,
                    'detection_metadata': detection_metadata
                }
            
            encoding = self._extract_encoding(image, face_location)
            if encoding is None:
                return {
                    'success': False,
                    'error': 'encoding_extraction_failed',
                    'face_detected': True,
                    'confidence': 0.0,
                    'detection_metadata': detection_metadata
                }
            
            if not self.storage.known_encodings:
                return {
                    'success': False,
                    'error': 'No training data',
                    'face_detected': True,
                    'confidence': 0.0,
                    'detection_metadata': detection_metadata
                }
            
            # Calculate distances to all known encodings
            known_encodings_list = list(self.storage.known_encodings.values())
            known_ids_list = list(self.storage.known_encodings.keys())
            
            distances = face_recognition.face_distance(known_encodings_list, encoding)
            
            # Find best match
            best_match_index = np.argmin(distances) if len(distances) > 0 else -1
            if best_match_index < 0:
                return {
                    'success': False,
                    'error': 'No valid encodings to compare',
                    'face_detected': True,
                    'confidence': 0.0,
                    'detection_metadata': detection_metadata
                }
            
            best_distance = distances[best_match_index]
            best_student_id = known_ids_list[best_match_index]
            confidence = 1.0 - best_distance
            
            # Check if match is acceptable
            if best_distance <= distance_threshold:
                # Secondary check: ensure significantly better than second best
                if len(distances) > 1:
                    sorted_distances = sorted(distances)
                    second_best = sorted_distances[1]
                    distance_gap = second_best - best_distance
                    if distance_gap < 0.03:
                        logger.warning(f"Ambiguous match detected (gap={distance_gap:.3f})")
                
                logger.info(f"✓ Face recognized: {best_student_id}, confidence={confidence:.3f}")
                
                matches = []
                if return_all_matches:
                    for sid, dist in zip(known_ids_list, distances):
                        if dist <= distance_threshold:
                            matches.append({
                                'student_id': sid,
                                'distance': float(dist),
                                'confidence': float(1.0 - dist)
                            })
                    matches.sort(key=lambda x: x['distance'])
                
                return {
                    'success': True,
                    'student_id': best_student_id,
                    'confidence': float(confidence),
                    'distance': float(best_distance),
                    'face_detected': True,
                    'matches': matches if return_all_matches else None,
                    'detection_metadata': detection_metadata
                }
            else:
                logger.warning(f"✗ Recognition failed: confidence={confidence:.3f}, threshold={distance_threshold}")
                return {
                    'success': False,
                    'error': f'No match found (best confidence: {confidence:.3f})',
                    'face_detected': True,
                    'confidence': float(confidence),
                    'distance': float(best_distance),
                    'detection_metadata': detection_metadata
                }
        
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return {
                'success': False,
                'error': str(e),
                'face_detected': False,
                'confidence': 0.0
            }
    
    def check_liveness(self, frames: List[np.ndarray]) -> Tuple[bool, str]:
        """Check if faces in frames are live (anti-spoofing).
        
        Args:
            frames: List of sequential frames
            
        Returns:
            Tuple of (is_live, message)
        """
        try:
            if not frames:
                return False, "No frames provided"
            
            is_live, blink_count = self.liveness_detector.check_liveness(frames)
            
            if is_live:
                return True, f"Liveness confirmed ({blink_count} blinks detected)"
            else:
                return False, "Liveness check failed (possible spoof)"
        
        except Exception as e:
            logger.warning(f"Liveness check error: {e}")
            return False, str(e)
    
    def load_training_data(self, path: str) -> bool:
        """Load training data from file.
        
        Args:
            path: Path to training data
            
        Returns:
            Success status
        """
        try:
            self.storage.load(path)
            logger.info(f"Training data loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
            return False
    
    def save_training_data(self, path: str) -> bool:
        """Save training data to file.
        
        Args:
            path: Path to save training data
            
        Returns:
            Success status
        """
        try:
            self.storage.save(path)
            logger.info(f"Training data saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save training data: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics.
        
        Returns:
            Statistics dict
        """
        return {
            'total_students_registered': len(self.storage.known_encodings),
            'detection_stats': self.detection_orchestrator.stats,
            'confidence_threshold': self.confidence_threshold,
        }
