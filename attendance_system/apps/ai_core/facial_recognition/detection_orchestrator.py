"""Intelligent detection orchestrator with confidence-based cascading.

Implements production-grade detection strategy:
- Smart fast methods first (CNN is fast on GPU, HOG as fallback)
- Confidence scoring for each detection
- Adaptive method selection based on image characteristics
- Quality threshold-based stopping condition
"""
import logging
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    face_recognition = None
    HAS_FACE_RECOGNITION = False


class DetectionConfidenceLevel(Enum):
    """Detection confidence levels for intelligent stopping conditions."""
    EXCELLENT = ("excellent", 0.95, 1.0)
    HIGH = ("high", 0.85, 0.95)
    GOOD = ("good", 0.70, 0.85)
    ACCEPTABLE = ("acceptable", 0.50, 0.70)
    POOR = ("poor", 0.0, 0.50)
    
    def __init__(self, level_name, min_score, max_score):
        self.level_name = level_name
        self.min_score = min_score
        self.max_score = max_score


@dataclass
class DetectionResult:
    """Encapsulates detection results with metadata."""
    success: bool
    face_locations: List[Tuple[int, int, int, int]]
    method_used: str
    confidence_score: float
    confidence_level: str
    quality_metrics: Dict[str, float]
    attempts: List[str]
    processing_time: float
    preprocessing_applied: bool
    meets_quality_threshold: bool
    stop_reason: str


class DetectionConfidenceCalculator:
    """Calculates confidence scores for detections based on multiple factors."""
    
    # Weights for different quality factors
    DETECTION_CLARITY_WEIGHT = 0.40
    LIGHTING_STABILITY_WEIGHT = 0.25
    FACE_SIZE_WEIGHT = 0.20
    METHOD_RELIABILITY_WEIGHT = 0.15
    
    # Method reliability scores (based on historical accuracy)
    METHOD_RELIABILITY = {
        'cnn': 0.95,      # CNN: most reliable
        'hog': 0.80,      # HOG: fast, decent accuracy
        'dnn_ssd': 0.85,  # DNN-SSD: good balance
        'dlib': 0.82,     # DLIB: solid
        'mtcnn': 0.90,    # MTCNN: very accurate
        'haar_cascade': 0.70,  # Haar: fastest, least reliable
    }
    
    @staticmethod
    def calculate_detection_clarity(image: np.ndarray, face_location: Tuple) -> float:
        """Calculate clarity of detected face region.
        
        Args:
            image: Input image
            face_location: Face location tuple (top, right, bottom, left)
            
        Returns:
            Clarity score 0-1
        """
        if not HAS_OPENCV:
            return 0.5
        
        try:
            top, right, bottom, left = face_location
            face_roi = image[top:bottom, left:right]
            
            if face_roi.size == 0:
                return 0.0
            
            # Laplacian variance (sharpness indicator)
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            clarity = min(1.0, laplacian.var() / 500.0)
            
            return float(clarity)
        except Exception as e:
            logger.warning(f"Clarity calculation failed: {e}")
            return 0.5
    
    @staticmethod
    def calculate_lighting_stability(image: np.ndarray, face_location: Tuple) -> float:
        """Calculate lighting consistency in face region.
        
        Args:
            image: Input image
            face_location: Face location tuple
            
        Returns:
            Lighting stability score 0-1
        """
        if not HAS_OPENCV:
            return 0.5
        
        try:
            top, right, bottom, left = face_location
            face_roi = image[top:bottom, left:right]
            
            if face_roi.size == 0:
                return 0.0
            
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
            
            # Standard deviation of brightness (lower = more stable)
            brightness_std = np.std(gray)
            
            # Normalize to 0-1 (lower std = higher stability/confidence)
            stability = 1.0 - min(1.0, brightness_std / 100.0)
            
            return float(stability)
        except Exception as e:
            logger.warning(f"Lighting stability calculation failed: {e}")
            return 0.5
    
    @staticmethod
    def calculate_face_size_score(image: np.ndarray, face_location: Tuple) -> float:
        """Calculate adequacy of face size in image.
        
        Very small faces are hard to recognize accurately.
        
        Args:
            image: Input image
            face_location: Face location tuple
            
        Returns:
            Face size score 0-1
        """
        try:
            h, w = image.shape[:2]
            top, right, bottom, left = face_location
            
            face_height = bottom - top
            face_width = right - left
            face_area = face_height * face_width
            total_area = h * w
            face_area_ratio = face_area / total_area
            
            # Optimal ratio is 10-30% of image
            if face_area_ratio < 0.02:
                return 0.3  # Too small
            elif face_area_ratio < 0.10:
                return 0.6
            elif face_area_ratio > 0.40:
                return 0.7  # Too large
            else:
                return 1.0  # Optimal
        except Exception as e:
            logger.warning(f"Face size calculation failed: {e}")
            return 0.5
    
    @classmethod
    def calculate_overall_confidence(cls, image: np.ndarray, face_location: Tuple, 
                                   detection_method: str) -> Dict[str, float]:
        """Calculate overall confidence score.
        
        Args:
            image: Input image
            face_location: Face location tuple
            detection_method: Method used for detection
            
        Returns:
            Dict with detailed scores
        """
        clarity = cls.calculate_detection_clarity(image, face_location)
        lighting = cls.calculate_lighting_stability(image, face_location)
        size = cls.calculate_face_size_score(image, face_location)
        method_reliability = cls.METHOD_RELIABILITY.get(detection_method, 0.75)
        
        overall_confidence = (
            clarity * cls.DETECTION_CLARITY_WEIGHT +
            lighting * cls.LIGHTING_STABILITY_WEIGHT +
            size * cls.FACE_SIZE_WEIGHT +
            method_reliability * cls.METHOD_RELIABILITY_WEIGHT
        )
        
        return {
            'overall': float(overall_confidence),
            'clarity': float(clarity),
            'lighting_stability': float(lighting),
            'face_size': float(size),
            'method_reliability': float(method_reliability),
        }
    
    @staticmethod
    def get_confidence_level(score: float) -> str:
        """Get confidence level name for a score.
        
        Args:
            score: Confidence score 0-1
            
        Returns:
            Confidence level name
        """
        for level in sorted(DetectionConfidenceLevel, 
                          key=lambda x: x.min_score, reverse=True):
            if score >= level.min_score:
                return level.level_name
        return 'poor'


class IntelligentDetectionOrchestrator:
    """Orchestrates intelligent face detection with confidence-based cascading.
    
    Strategy:
    1. Preprocess image once using adaptive preprocessing
    2. Try CNN first (fastest on GPU, most accurate)
    3. Fall back to HOG if CNN fails (fast CPU fallback)
    4. Try advanced methods (DNN, MTCNN) only if confidence too low
    5. Stop when confidence threshold reached
    """
    
    # Minimum acceptable confidence thresholds
    MIN_CONFIDENCE_FAST_STOP = 0.85  # Stop if CNN achieves this confidence
    MIN_CONFIDENCE_ACCEPTABLE = 0.70  # Accept if any method achieves this
    MIN_CONFIDENCE_RETRY = 0.50      # If below this, try advanced methods
    
    # Detection method priority (balanced: speed + accuracy)
    DETECTION_PRIORITY = [
        ('cnn', 'neural_network', True),       # Fast on GPU, most accurate
        ('hog', 'traditional', False),         # Fast on CPU
        ('dnn_ssd', 'neural_network', True),   # Balanced accuracy/speed
        ('mtcnn', 'advanced', True),           # Very accurate but slower
        ('dlib', 'traditional', False),        # Decent accuracy
        ('haar_cascade', 'traditional', False), # Fastest but least accurate
    ]
    
    def __init__(self, confidence_threshold: float = 0.70, 
                 enable_preprocessing: bool = True):
        """Initialize orchestrator.
        
        Args:
            confidence_threshold: Minimum acceptable confidence
            enable_preprocessing: Whether to preprocess images
        """
        self.confidence_threshold = confidence_threshold
        self.enable_preprocessing = enable_preprocessing
        self.stats = {
            'total_detections': 0,
            'fast_success': 0,  # CNN succeeded
            'fallback_success': 0,
            'advanced_success': 0,
            'total_failed': 0,
        }
    
    def detect_faces_intelligently(self, image: np.ndarray,
                                  preprocessing_metadata: Optional[Dict] = None
                                  ) -> DetectionResult:
        """Detect faces using intelligent cascading strategy.
        
        Args:
            image: Input image (BGR format)
            preprocessing_metadata: Metadata from preprocessing step
            
        Returns:
            DetectionResult with detailed information
        """
        import time
        start_time = time.time()
        
        self.stats['total_detections'] += 1
        attempts = []
        best_result = None
        best_confidence = 0.0
        
        try:
            working_image = image.copy()
            
            # Preprocess image if enabled
            if self.enable_preprocessing and preprocessing_metadata is None:
                from .preprocessing import ImagePreprocessor
                preprocessor = ImagePreprocessor(enable_adaptive_preprocessing=True)
                working_image, preprocessing_metadata = preprocessor.preprocess(
                    image, aggressive=False
                )
            
            preprocessing_applied = preprocessing_metadata is not None and \
                                  preprocessing_metadata.get('preprocessing_successful', False)
            
            # Try detection methods in priority order
            for method_name, method_type, uses_preprocessing in self.DETECTION_PRIORITY:
                attempts.append(method_name)
                
                try:
                    logger.info(f"Attempting detection with {method_name.upper()}...")
                    
                    # Get face locations based on method
                    face_locations = self._try_detection_method(
                        method_name, working_image if uses_preprocessing else image
                    )
                    
                    if not face_locations or len(face_locations) == 0:
                        logger.debug(f"{method_name} returned no faces")
                        continue
                    
                    # Multiple faces detected - skip
                    if len(face_locations) > 1:
                        logger.warning(f"{method_name} detected multiple faces, skipping")
                        continue
                    
                    face_location = face_locations[0]
                    
                    # Calculate confidence score
                    quality_metrics = DetectionConfidenceCalculator.calculate_overall_confidence(
                        image, face_location, method_name
                    )
                    
                    confidence = quality_metrics['overall']
                    confidence_level = DetectionConfidenceCalculator.get_confidence_level(confidence)
                    
                    logger.info(f"✓ {method_name.upper()}: confidence={confidence:.2f} ({confidence_level})")
                    
                    # Store best result so far
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_result = (face_location, quality_metrics, method_name, confidence_level)
                    
                    # Check stopping conditions
                    if method_type == 'neural_network' and confidence >= self.MIN_CONFIDENCE_FAST_STOP:
                        logger.info(f"🚀 FAST SUCCESS: {method_name} achieved high confidence {confidence:.2f}")
                        self.stats['fast_success'] += 1
                        processing_time = time.time() - start_time
                        
                        return DetectionResult(
                            success=True,
                            face_locations=[face_location],
                            method_used=method_name,
                            confidence_score=confidence,
                            confidence_level=confidence_level,
                            quality_metrics=quality_metrics,
                            attempts=attempts,
                            processing_time=processing_time,
                            preprocessing_applied=preprocessing_applied,
                            meets_quality_threshold=confidence >= self.confidence_threshold,
                            stop_reason=f"Fast method achieved confidence {confidence:.2f}"
                        )
                    
                    # Accept if meets minimum threshold
                    if confidence >= self.confidence_threshold:
                        logger.info(f"✓ Accepting {method_name} with confidence {confidence:.2f}")
                        self.stats['fallback_success' if method_type != 'neural_network' else 'fast_success'] += 1
                        processing_time = time.time() - start_time
                        
                        return DetectionResult(
                            success=True,
                            face_locations=[face_location],
                            method_used=method_name,
                            confidence_score=confidence,
                            confidence_level=confidence_level,
                            quality_metrics=quality_metrics,
                            attempts=attempts,
                            processing_time=processing_time,
                            preprocessing_applied=preprocessing_applied,
                            meets_quality_threshold=True,
                            stop_reason=f"{method_name} met confidence threshold {confidence:.2f}"
                        )
                
                except Exception as e:
                    logger.debug(f"Error with {method_name}: {e}")
                    continue
            
            # Return best result even if below threshold
            if best_result is not None:
                face_location, quality_metrics, method_used, confidence_level = best_result
                self.stats['advanced_success'] += 1
                processing_time = time.time() - start_time
                
                logger.warning(f"Returning best result from {method_used} with confidence {best_confidence:.2f}")
                
                return DetectionResult(
                    success=True,
                    face_locations=[face_location],
                    method_used=method_used,
                    confidence_score=best_confidence,
                    confidence_level=confidence_level,
                    quality_metrics=quality_metrics,
                    attempts=attempts,
                    processing_time=processing_time,
                    preprocessing_applied=preprocessing_applied,
                    meets_quality_threshold=best_confidence >= self.confidence_threshold,
                    stop_reason=f"No method met threshold, returning best ({method_used}, {best_confidence:.2f})"
                )
            
            # Complete failure
            self.stats['total_failed'] += 1
            processing_time = time.time() - start_time
            
            logger.error(f"✗ No faces detected by any method")
            
            return DetectionResult(
                success=False,
                face_locations=[],
                method_used=None,
                confidence_score=0.0,
                confidence_level='poor',
                quality_metrics={},
                attempts=attempts,
                processing_time=processing_time,
                preprocessing_applied=preprocessing_applied,
                meets_quality_threshold=False,
                stop_reason="No detection method succeeded"
            )
        
        except Exception as e:
            logger.error(f"Detection orchestration failed: {e}")
            processing_time = time.time() - start_time
            
            return DetectionResult(
                success=False,
                face_locations=[],
                method_used=None,
                confidence_score=0.0,
                confidence_level='poor',
                quality_metrics={},
                attempts=attempts,
                processing_time=processing_time,
                preprocessing_applied=False,
                meets_quality_threshold=False,
                stop_reason=f"Exception: {str(e)}"
            )
    
    def _try_detection_method(self, method_name: str, image: np.ndarray) -> List[Tuple]:
        """Try a specific detection method.
        
        Args:
            method_name: Name of detection method
            image: Input image
            
        Returns:
            List of face locations or empty list
        """
        if not HAS_FACE_RECOGNITION and method_name in ['cnn', 'hog']:
            return []
        
        if method_name == 'cnn':
            return face_recognition.face_locations(image, model='cnn')
        elif method_name == 'hog':
            return face_recognition.face_locations(image, model='hog')
        else:
            # Try to get detector from detectors module
            from . import detectors as detector_module
            detector_class_name = f"{method_name.upper().replace('_', '')}FaceDetector"
            
            if hasattr(detector_module, detector_class_name):
                detector_class = getattr(detector_module, detector_class_name)
                try:
                    detector = detector_class()
                    faces = detector.detect_faces(image)
                    
                    # Convert from (x, y, w, h) to face_recognition format
                    face_locations = []
                    for (x, y, w, h) in faces:
                        top, right, bottom, left = y, x + w, y + h, x
                        face_locations.append((top, right, bottom, left))
                    
                    return face_locations
                except Exception as e:
                    logger.debug(f"Could not init {method_name}: {e}")
            
            return []
