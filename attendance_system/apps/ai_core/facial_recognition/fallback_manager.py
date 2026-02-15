"""Fallback manager for facial recognition with cascading detection methods."""
import logging
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

# Conditional imports
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
    import cv2
    HAS_CV2 = True
except ImportError:
    cv2 = None
    HAS_CV2 = False


class DetectionMethod(Enum):
    """Enumeration of available detection methods ordered by accuracy."""
    CNN = "cnn"  # Most accurate, GPU recommended
    DNN_SSD = "dnn_ssd"  # ResNet-based, good for various angles
    MTCNN = "mtcnn"  # Multi-task CNN with landmarks
    HOG = "hog"  # Fast, CPU-friendly
    DLIB = "dlib"  # Good balance
    HAAR_CASCADE = "haar_cascade"  # Fastest, least accurate


class RecognitionModel(Enum):
    """Enumeration of recognition models ordered by accuracy."""
    LARGE = "large"  # Most accurate, slower
    SMALL = "small"  # Faster, slightly less accurate


class FallbackDetectionManager:
    """Manager for cascading face detection with multiple fallback methods.
    
    Attempts detection in order of accuracy, falling back to less accurate
    but more robust methods if higher accuracy methods fail.
    """
    
    def __init__(self, enable_all_methods: bool = True):
        """Initialize fallback detection manager.
        
        Args:
            enable_all_methods: Whether to enable all available detection methods
        """
        self.enable_all_methods = enable_all_methods
        self.detection_stats = {method: {'attempts': 0, 'successes': 0} 
                               for method in DetectionMethod}
        
        # Initialize detectors lazily
        self._detectors = {}
        
        # Define detection method order (fastest first, then fallback to more accurate but slower)
        # Priority: Speed first, then accuracy
        self.detection_order = [
            DetectionMethod.HOG,            # Fastest - CPU friendly
            DetectionMethod.HAAR_CASCADE,   # Very fast - traditional OpenCV
            DetectionMethod.DLIB,          # Balanced speed/accuracy
            DetectionMethod.DNN_SSD,       # Good accuracy, moderate speed  
            DetectionMethod.CNN,           # Most accurate but slower
            DetectionMethod.MTCNN,         # Slowest but handles difficult cases
        ]
        
        logger.info("Fallback detection manager initialized")
    
    def _get_detector(self, method: DetectionMethod):
        """Lazily initialize and retrieve detector for given method.
        
        Args:
            method: Detection method to retrieve
            
        Returns:
            Detector instance or None if unavailable
        """
        if method in self._detectors:
            return self._detectors[method]
        
        detector = None
        
        try:
            if method == DetectionMethod.CNN or method == DetectionMethod.HOG:
                # These are built into face_recognition library
                if HAS_FACE_RECOGNITION:
                    detector = method.value  # Store as string for face_recognition
            
            elif method == DetectionMethod.DNN_SSD:
                if HAS_CV2:
                    from .detectors import DNNFaceDetector
                    detector = DNNFaceDetector()
            
            elif method == DetectionMethod.MTCNN:
                try:
                    from .detectors import MTCNNFaceDetector
                    detector = MTCNNFaceDetector()
                except Exception as e:
                    logger.debug(f"MTCNN not available: {e}")
            
            elif method == DetectionMethod.DLIB:
                try:
                    from .detectors import DlibFaceDetector
                    detector = DlibFaceDetector()
                except Exception as e:
                    logger.debug(f"Dlib not available: {e}")
            
            elif method == DetectionMethod.HAAR_CASCADE:
                if HAS_CV2:
                    from .detectors import CVFaceDetector
                    detector = CVFaceDetector()
            
            if detector is not None:
                self._detectors[method] = detector
                logger.debug(f"Initialized {method.value} detector")
            
        except Exception as e:
            logger.warning(f"Could not initialize {method.value} detector: {e}")
        
        return detector
    
    def _convert_to_rgb(self, image):
        """Convert image to RGB format."""
        if not HAS_CV2 or not HAS_NUMPY:
            return image
        if len(image.shape) == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
    
    def _apply_image_enhancements(self, image):
        """Apply image enhancements to improve detection.
        
        Args:
            image: Input image in RGB format
            
        Returns:
            Enhanced image
        """
        if not HAS_CV2 or not HAS_NUMPY:
            return image
        
        try:
            # Apply bilateral filter to reduce noise
            enhanced = cv2.bilateralFilter(image, 9, 75, 75)
            
            # Apply CLAHE for better lighting
            lab = cv2.cvtColor(enhanced, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
            # Apply sharpening
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            
            return enhanced
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image
    
    def detect_faces_with_fallback(self, image, methods: Optional[List[DetectionMethod]] = None) -> Dict[str, Any]:
        """Detect faces using cascading fallback methods - SPEED OPTIMIZED.
        
        Tries each detection method in order of SPEED (fastest first), stopping immediately
        when a face is successfully detected to minimize processing time.
        
        Args:
            image: Input image (BGR or RGB)
            methods: Optional list of methods to try (defaults to speed-optimized order)
            
        Returns:
            Dict containing:
                - success: Whether face was detected
                - face_locations: List of face locations (face_recognition format)
                - method_used: Detection method that succeeded
                - attempts: List of methods attempted
                - error: Error message if all methods failed
        """
        if methods is None:
            methods = self.detection_order
        
        rgb_image = self._convert_to_rgb(image)
        
        attempts = []
        last_error = None
        
        # Try fast methods first with original image (no enhancement for speed)
        fast_methods = [DetectionMethod.HOG, DetectionMethod.HAAR_CASCADE]
        enhanced_image = None  # Only enhance when needed
        
        for i, method in enumerate(methods):
            self.detection_stats[method]['attempts'] += 1
            attempts.append(method.value)
            
            # Use original image for fast methods, enhanced for slower methods
            if method in fast_methods:
                working_image = rgb_image
                logger.debug(f"Using original image for fast method: {method.value}")
            else:
                if enhanced_image is None:
                    enhanced_image = self._apply_image_enhancements(rgb_image)
                    logger.debug("Applied image enhancements for accuracy-focused methods")
                working_image = enhanced_image
            
            try:
                logger.info(f"Attempting face detection with {method.value.upper()} method...")
                
                # Try with face_recognition library methods (CNN/HOG)
                if method in [DetectionMethod.CNN, DetectionMethod.HOG]:
                    if not HAS_FACE_RECOGNITION:
                        logger.debug(f"{method.value} skipped: face_recognition not available")
                        continue
                    
                    face_locations = face_recognition.face_locations(
                        working_image, 
                        model=method.value
                    )
                    
                    if len(face_locations) > 0:
                        self.detection_stats[method]['successes'] += 1
                        logger.info(f"🚀 FAST SUCCESS: Face detected using {method.value.upper()} on attempt {len(attempts)}")
                        return {
                            'success': True,
                            'face_locations': face_locations,
                            'method_used': method.value,
                            'attempts': attempts,
                            'error': None,
                            'detection_speed': 'fast' if len(attempts) <= 2 else 'fallback'
                        }
                    else:
                        logger.debug(f"{method.value} detected 0 faces")
                
                # Try with custom detector classes (DNN, MTCNN, DLIB, Haar)
                else:
                    detector = self._get_detector(method)
                    if detector is None:
                        logger.debug(f"{method.value} skipped: detector not available")
                        continue
                    
                    # Convert to BGR for OpenCV-based detectors
                    bgr_image = cv2.cvtColor(working_image, cv2.COLOR_RGB2BGR) if HAS_CV2 else working_image
                    
                    # Detect faces (returns (x, y, w, h) format)
                    faces = detector.detect_faces(bgr_image)
                    
                    # Check if faces were detected (avoid numpy array boolean ambiguity)
                    if faces is not None and len(faces) > 0:
                        # Convert to face_recognition format (top, right, bottom, left)
                        face_locations = []
                        for (x, y, w, h) in faces:
                            top = y
                            right = x + w
                            bottom = y + h
                            left = x
                            face_locations.append((top, right, bottom, left))
                        
                        self.detection_stats[method]['successes'] += 1
                        logger.info(f"🚀 SUCCESS: Face detected using {method.value.upper()} on attempt {len(attempts)}")
                        return {
                            'success': True,
                            'face_locations': face_locations,
                            'method_used': method.value,
                            'attempts': attempts,
                            'error': None,
                            'detection_speed': 'fast' if len(attempts) <= 2 else 'fallback'
                        }
                    else:
                        logger.debug(f"{method.value} detected 0 faces")
            
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error with {method.value} detection: {e}")
                continue
        
        # All methods failed
        error_msg = f"No face detected by any method (tried: {', '.join(attempts)})"
        if last_error:
            error_msg += f" - Last error: {last_error}"
        
        logger.warning(f"✗ {error_msg}")
        return {
            'success': False,
            'face_locations': [],
            'method_used': None,
            'attempts': attempts,
            'error': error_msg
        }
    
    def extract_encoding_with_fallback(self, image, face_location, 
                                      models: Optional[List[RecognitionModel]] = None) -> Dict[str, Any]:
        """Extract face encoding with model fallback.
        
        Tries to extract encoding using different models, falling back if needed.
        
        Args:
            image: Input image in RGB format
            face_location: Face location in face_recognition format
            models: Optional list of models to try (defaults to [LARGE, SMALL])
            
        Returns:
            Dict containing:
                - success: Whether encoding was extracted
                - encoding: Face encoding (128-d vector)
                - model_used: Model that succeeded
                - error: Error message if failed
        """
        if not HAS_FACE_RECOGNITION:
            return {
                'success': False,
                'encoding': None,
                'model_used': None,
                'error': 'face_recognition library not available'
            }
        
        if models is None:
            models = [RecognitionModel.LARGE, RecognitionModel.SMALL]
        
        for model in models:
            try:
                logger.info(f"Attempting face encoding with {model.value.upper()} model...")
                
                encodings = face_recognition.face_encodings(
                    image,
                    [face_location],
                    num_jitters=1,
                    model=model.value
                )
                
                # Check if encodings were generated (avoid numpy array boolean ambiguity)
                if encodings is not None and len(encodings) > 0:
                    logger.info(f"✓ Face encoding generated successfully using {model.value.upper()} model")
                    return {
                        'success': True,
                        'encoding': encodings[0],
                        'model_used': model.value,
                        'error': None
                    }
                else:
                    logger.debug(f"{model.value} model produced no encodings")
            
            except Exception as e:
                logger.warning(f"Error with {model.value} model: {e}")
                continue
        
        return {
            'success': False,
            'encoding': None,
            'model_used': None,
            'error': 'Failed to generate encoding with all models'
        }
    
    def get_detection_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics about detection method usage and success rates.
        
        Returns:
            Dict mapping method names to their stats
        """
        stats = {}
        for method, data in self.detection_stats.items():
            attempts = data['attempts']
            successes = data['successes']
            success_rate = (successes / attempts * 100) if attempts > 0 else 0.0
            
            stats[method.value] = {
                'attempts': attempts,
                'successes': successes,
                'success_rate': f"{success_rate:.1f}%"
            }
        
        return stats
    
    def log_statistics(self):
        """Log detection statistics."""
        stats = self.get_detection_statistics()
        logger.info("=== Face Detection Statistics ===")
        for method, data in stats.items():
            logger.info(f"{method.upper()}: {data['successes']}/{data['attempts']} "
                       f"({data['success_rate']}) success rate")
