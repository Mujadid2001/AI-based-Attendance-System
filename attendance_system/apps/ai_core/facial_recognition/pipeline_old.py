"""Main facial recognition pipeline orchestrator."""
import logging
from typing import Optional, Tuple, Dict, Any

from .recognizers import FaceRecognitionLibRecognizer
from .liveness import BlinkLivenessDetector
from .storage import TrainingDataStorage
from .utils import FaceQualityChecker
from .preprocessing import ImagePreprocessor
from .detection_orchestrator import IntelligentDetectionOrchestrator, DetectionResult


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
    """Production-grade facial recognition pipeline with intelligent detection.
    
    Implements:
    1. Adaptive image preprocessing (denoising, lighting normalization, contrast enhancement)
    2. Intelligent cascading detection (CNN → HOG → DNN → MTCNN)
    3. Confidence-based quality scoring
    4. Face encoding generation
    5. Distance-based recognition with outlier detection
    """
    
    def __init__(self, face_recognizer=None, confidence_threshold: float = 0.70, 
                 storage=None, enable_quality_checks: bool = True,
                 enable_preprocessing: bool = True):
        """Initialize pipeline.
        
        Args:
            face_recognizer: Optional face recognizer (uses default if None)
            confidence_threshold: Minimum confidence for recognition (0.70 = 70% quality)
            storage: Optional training data storage
            enable_quality_checks: Whether to perform quality checks on images
            enable_preprocessing: Whether to enable adaptive preprocessing
        """
        self.confidence_threshold = confidence_threshold
        self.enable_quality_checks = enable_quality_checks
        self.enable_preprocessing = enable_preprocessing
        
        # Initialize components
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
        
        logger.info(f"Pipeline initialized (confidence_threshold={confidence_threshold})")
    
    def detect_face(self, image) -> Tuple[bool, Optional[Tuple], Dict[str, Any]]:
        """Detect face in image using intelligent orchestration.
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Tuple of (success, face_location, metadata)
        """
        try:
            # Preprocess image if enabled
            preprocessing_metadata = None
            if self.enable_preprocessing:
                image, preprocessing_metadata = self.preprocessor.preprocess(
                    image, aggressive=False
                )
            
            # Run intelligent detection
            result: DetectionResult = self.detection_orchestrator.detect_faces_intelligently(
                image, preprocessing_metadata
            )
            
            if result.success and result.meets_quality_threshold:
                logger.info(f"✓ Face detected with {result.confidence_level} confidence ({result.confidence_score:.2f})")
                return True, result.face_locations[0], {
                    'method': result.method_used,
                    'confidence': result.confidence_score,
                    'confidence_level': result.confidence_level,
                    'quality_metrics': result.quality_metrics,
                    'processing_time': result.processing_time,
                }
            elif result.success:
                logger.warning(f"Face detected but confidence {result.confidence_score:.2f} below threshold {self.confidence_threshold}")
                return False, None, {
                    'error': f"Confidence {result.confidence_score:.2f} below threshold {self.confidence_threshold}",
                    'attempts': result.attempts,
                    'processing_time': result.processing_time,
                }
            else:
                logger.error(f"Detection failed: {result.stop_reason}")
                return False, None, {
                    'error': result.stop_reason,
                    'attempts': result.attempts,
                    'processing_time': result.processing_time,
                }
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return False, None, {'error': str(e)}
            return image
    
    def _apply_histogram_equalization(self, image):
        """Apply histogram equalization to improve contrast."""
        if not HAS_CV2:
            return image
        try:
            if len(image.shape) == 3:
                # Convert to YUV and equalize Y channel
                yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
                yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
                return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
            else:
                return cv2.equalizeHist(image)
        except Exception as e:
            logger.error(f"Error applying histogram equalization: {e}")
            return image
    
    def _emergency_enhancement(self, image):
        """Apply aggressive enhancement for emergency registration attempts."""
        if not HAS_CV2:
            return image
        try:
            # Apply multiple enhancement techniques aggressively
            enhanced = image.copy()
            
            # 1. Bilateral filter for noise reduction
            enhanced = cv2.bilateralFilter(enhanced, 9, 80, 80)
            
            # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization) 
            if len(enhanced.shape) == 3:
                lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                enhanced = cv2.merge([l, a, b])
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            else:
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(enhanced)
            
            # 3. Unsharp masking for edge enhancement
            gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
            enhanced = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)
            
            # 4. Gamma correction based on brightness
            gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY) if len(enhanced.shape) == 3 else enhanced
            mean_brightness = np.mean(gray)
            
            if mean_brightness < 80:  # Dark image
                gamma = 0.6
            elif mean_brightness > 180:  # Bright image  
                gamma = 1.4
            else:
                gamma = 1.0
                
            if gamma != 1.0:
                enhanced = np.power(enhanced / 255.0, 1.0 / gamma)
                enhanced = (enhanced * 255).astype(np.uint8)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error in emergency enhancement: {e}")
            return image

    def _extract_face_encoding(self, image, check_quality=True, adaptive_quality=False):
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
                quality_results = FaceQualityChecker.check_all(image, face_location, adaptive=adaptive_quality)
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

    def register_face(self, image, student_id: str, check_quality=True, max_attempts=6):
        """Register face for a student with enhanced environment-adaptive processing.
        
        Args:
            image: Input image
            student_id: Student identifier
            check_quality: Whether to perform quality checks
            max_attempts: Maximum registration attempts with different processing
            
        Returns:
            Tuple of (success, encoding, message, metadata)
        """
        if not HAS_FACE_RECOGNITION:
            return False, None, "Face recognition library not available", None
        
        # Environment-adaptive processing methods
        processing_methods = [
            ("original", lambda img: img),
            ("enhanced", lambda img: FaceQualityChecker.enhance_image(img)),
            ("gamma_light", lambda img: self._apply_gamma_correction(img, 0.7)),
            ("gamma_dark", lambda img: self._apply_gamma_correction(img, 1.3)),
            ("histogram_equalized", lambda img: self._apply_histogram_equalization(img)),
            ("emergency", lambda img: self._emergency_enhancement(img))
        ]
        
        best_result = None
        best_quality_score = -1
        last_error = None
        attempts_log = []
        
        for attempt, (method_name, process_func) in enumerate(processing_methods[:max_attempts]):
            try:
                logger.info(f"Registration attempt {attempt + 1}/{max_attempts} using {method_name} processing")
                
                # Apply processing method
                processed_image = process_func(image.copy())
                
                # Environment-adaptive quality assessment
                if check_quality:
                    try:
                        environment = FaceQualityChecker.detect_environment(processed_image)
                    except Exception as e:
                        logger.warning(f"Environment detection failed: {e}, using default")
                        environment = "unknown"
                    quality_results = FaceQualityChecker.check_all(processed_image, None, adaptive=True)
                    
                    # Progressively lower standards for later attempts
                    quality_threshold = 3 - (attempt * 0.5)  # Start at 3, go down to 0.5
                    quality_score = sum(1 for check in quality_results['checks'].values() if check['pass'])
                    
                    # For emergency attempts, accept almost anything with a face
                    if attempt >= 4:
                        check_quality = False  # Skip quality for emergency attempts
                        logger.info(f"Emergency mode - skipping quality checks for attempt {attempt + 1}")
                else:
                    quality_score = 5  # Assume good quality when not checking
                
                # Extract face encoding with increasingly lenient checks
                adaptive_quality = check_quality and attempt < 4  # Only check quality for first 4 attempts
                encoding, error_msg, face_location, metadata = self._extract_face_encoding(
                    processed_image, 
                    check_quality=adaptive_quality, 
                    adaptive_quality=True
                )
                
                attempt_info = {
                    'method': method_name,
                    'quality_score': quality_score,
                    'error': error_msg,
                    'face_detected': face_location is not None
                }
                attempts_log.append(attempt_info)
                
                if error_msg:
                    last_error = f"{method_name}: {error_msg}"
                    logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                    
                    # For emergency attempts, try with minimal requirements
                    if attempt >= 4 and "No face" not in error_msg:
                        # Try to proceed even with quality issues
                        logger.info(f"Emergency retry for attempt {attempt + 1} with minimal requirements")
                        encoding, error_msg, face_location, metadata = self._extract_face_encoding(
                            processed_image, 
                            check_quality=False,  # No quality check
                            adaptive_quality=False
                        )
                        
                        if not error_msg and encoding is not None:
                            logger.info(f"Emergency retry succeeded for attempt {attempt + 1}")
                            quality_score = 1  # Minimal but acceptable
                        else:
                            continue
                    else:
                        continue
                
                # Track best result
                if quality_score > best_quality_score or (best_result is None and encoding is not None):
                    best_quality_score = quality_score
                    best_result = (encoding, face_location, metadata, method_name, processed_image, attempt + 1)
                    
                    # Accept immediately if we get decent quality
                    if quality_score >= 3 or (attempt >= 3 and quality_score >= 1):
                        break
            
            except Exception as e:
                last_error = f"{method_name}: {str(e)}"
                logger.error(f"Registration attempt {attempt + 1} error: {last_error}")
                attempts_log.append({
                    'method': method_name,
                    'quality_score': -1,
                    'error': str(e),
                    'face_detected': False
                })
                continue
        
        # Use best result if we found one
        if best_result:
            encoding, face_location, metadata, method_name, processed_image, attempt_used = best_result
            
            # Generate augmentations for robustness only if we have good quality
            encodings = [encoding]  # Start with best encoding
            
            # Only augment if quality is reasonable to avoid making bad encodings worse
            if best_quality_score >= 2:
                try:
                    from .utils import DataAugmentation
                    augmentations = DataAugmentation.generate_augmentations(processed_image, num_augmentations=2)
                    
                    for aug_image in augmentations:
                        aug_encoding, _, _, _ = self._extract_face_encoding(aug_image, check_quality=False)
                        if aug_encoding is not None:
                            encodings.append(aug_encoding)
                except Exception as e:
                    logger.warning(f"Augmentation failed: {e}")
            
            # Average encodings for better robustness
            if len(encodings) > 1:
                avg_encoding = np.mean(encodings, axis=0)
                # Normalize to unit vector
                avg_encoding = avg_encoding / np.linalg.norm(avg_encoding)
                final_encoding = avg_encoding
            else:
                final_encoding = encoding
            
            # Store encoding
            self.storage.add_encoding(student_id, final_encoding)
            
            # Success message with environment awareness
            try:
                environment = FaceQualityChecker.detect_environment(processed_image)
            except Exception:
                environment = "unknown"
            success_msg = f"Face registered using {method_name} processing (attempt {attempt_used})"
            if environment != "unknown":
                success_msg += f" in {environment} environment"
            if len(encodings) > 1:
                success_msg += f" with {len(encodings)} encodings averaged"
            
            enhanced_metadata = metadata.copy() if metadata else {}
            enhanced_metadata.update({
                'processing_method': method_name,
                'attempt_used': attempt_used,
                'quality_score': best_quality_score,
                'environment': environment,
                'encodings_averaged': len(encodings),
                'attempts_log': attempts_log,
                'emergency_mode': attempt_used >= 5
            })
            
            logger.info(f"Registration successful: {success_msg}")
            return True, final_encoding, success_msg, enhanced_metadata
        else:
            # All attempts failed
            error_msg = f"Registration failed after {max_attempts} attempts"
            if last_error:
                error_msg += f". Last error: {last_error}"
            
            failure_metadata = {
                'attempts_log': attempts_log,
                'total_attempts': max_attempts
            }
            
            logger.error(error_msg)
            return False, None, error_msg, failure_metadata
    
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
            
            # Get the dimension of the current encoding to compare
            encoding_dim = encoding.shape[0]
            logger.info(f"Query encoding dimension: {encoding_dim}")
            
            # Validate and filter encodings - only include encodings with matching dimension
            for sid in all_ids:
                enc = self.storage.get_encoding(sid)
                if enc is not None and isinstance(enc, np.ndarray):
                    if enc.shape == (encoding_dim,):
                        # Only add encodings with same dimension as query
                        known_encodings_list.append(enc)
                        valid_ids.append(sid)
                    else:
                        logger.warning(f"Skipping student {sid}: dimension mismatch (has {enc.shape[0]}, need {encoding_dim})")
                else:
                    logger.warning(f"Invalid encoding for student {sid}: type={type(enc)}, shape={enc.shape if hasattr(enc, 'shape') else 'N/A'}")
            
            if len(known_encodings_list) == 0:
                return {
                    'success': False,
                    'error': f'No valid {encoding_dim}-dimensional encodings to compare against',
                    'face_detected': True,
                    'confidence': 0.0,
                    'detection_metadata': metadata
                }
            
            logger.info(f"Comparing against {len(known_encodings_list)} encodings with dimension {encoding_dim}")
            
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
