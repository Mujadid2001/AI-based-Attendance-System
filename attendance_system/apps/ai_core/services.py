import logging
from django.conf import settings
from apps.student.models import StudentProfile, StudentFaceImage
from PIL import Image
import os
try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger(__name__)


class AIFeatureUnavailable(Exception):
    """
    Raised when an AI feature is requested that cannot run on this server.

    The heavy machine-learning libraries (face_recognition, dlib, OpenCV) are
    optional: they are imported inside try/except blocks so the app boots
    without them. This exception is how the rest of the code learns that a
    particular feature is switched off, instead of the underlying ImportError
    escaping as an unhandled 500.

    `apps/ai_core` views let it propagate and the DRF exception handler in
    `utils.responses.api_exception_handler` turns it into a 503 with an
    actionable message.
    """

    def __init__(self, message, *, reason=None):
        super().__init__(message)
        self.message = message
        self.reason = reason


class _NullVoiceNotifier:
    """
    Stand-in used when pyttsx3 (or espeak) is not installed.

    Voice feedback is a nicety, never a requirement, so every method logs at
    debug level and reports "not spoken" instead of failing the request.
    """

    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            logger.debug('Voice notification %s skipped: pyttsx3 unavailable', name)
            return False
        return _noop

    def __bool__(self):
        return False


class AIServiceManager:
    """Singleton manager for AI services."""
    
    _instance = None
    _pipeline = None
    _voice_notifier = None
    _pipeline_initialized = False
    _voice_initialized = False
    _pipeline_error = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _ensure_pipeline_initialized(self):
        if self._pipeline_initialized:
            return
        
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """
        Initialize the facial recognition pipeline.

        Records why initialisation failed instead of re-attempting (and
        re-raising) on every single request.
        """
        if self._pipeline_error is not None:
            raise AIFeatureUnavailable(
                'Facial recognition is not available on this server.',
                reason=str(self._pipeline_error),
            )

        try:
            # Import only when needed to avoid slow startup
            from apps.ai_core.facial_recognition import (
                FacialRecognitionPipeline, CVFaceDetector,
                FaceRecognitionLibRecognizer, ImageProcessor
            )
            
            # Initialize facial recognition pipeline
            self._pipeline = FacialRecognitionPipeline()
            
            # Load training data if exists
            training_data_path = os.path.join(
                settings.AI_SETTINGS['MODELS_DIR'],
                'face_encodings.pkl'
            )
            if os.path.exists(training_data_path):
                self._pipeline.load_training_data(training_data_path)
            
            self._pipeline_initialized = True
            logger.info("Facial recognition pipeline initialized")
        except Exception as e:
            # Cache the failure so we log once, not once per request.
            self._pipeline_error = e
            logger.error(
                'Facial recognition pipeline unavailable: %s', e
            )
            raise AIFeatureUnavailable(
                'Facial recognition is not available on this server. '
                'Install the optional dependencies with '
                '"pip install -r requirements-optional.txt".',
                reason=str(e),
            ) from e

    def is_facial_recognition_available(self):
        """
        Whether the facial recognition pipeline can be used.

        Never raises: safe to call from health checks and capability probes.
        """
        try:
            self._ensure_pipeline_initialized()
        except AIFeatureUnavailable:
            return False
        return True

    def unavailable_reason(self):
        """Why facial recognition is unavailable, or None if it is available."""
        if self._pipeline_error is None:
            self.is_facial_recognition_available()
        return str(self._pipeline_error) if self._pipeline_error else None

    def get_status(self):
        """Machine-readable capability report for the frontend / health checks."""
        available = self.is_facial_recognition_available()
        self._ensure_voice_initialized()
        return {
            'facial_recognition': {
                'available': available,
                'reason': str(self._pipeline_error) if self._pipeline_error else None,
                'threshold': getattr(self._pipeline, 'confidence_threshold', None),
            },
            'voice_notifications': {
                'available': self._voice_notifier is not None,
            },
        }

    def _ensure_voice_initialized(self):
        """Lazy initialize voice notifier only when needed."""
        if not self._voice_initialized:
            try:
                # Import only when needed
                from apps.ai_core.voice_notifier import AttendanceVoiceNotifier
                
                self._voice_notifier = AttendanceVoiceNotifier()
                self._voice_initialized = True
                logger.info("Voice notifier initialized")
            except Exception as e:
                logger.error(f"Error initializing voice notifier: {e}")
                # Don't raise - voice is optional
                self._voice_notifier = None
    
    def initialize_all_services(self):
        """
        Eagerly initialize all AI services.
        This is called during Django startup for better first-request performance.
        """
        logger.info("Initializing all AI services (eager loading)...")
        
        # Initialize facial recognition pipeline
        if not self._pipeline_initialized:
            self._initialize_pipeline()
            # Load all registered student faces
            self.load_all_student_faces()
        
        # Initialize voice notifier
        if not self._voice_initialized:
            self._ensure_voice_initialized()
        
        logger.info("All AI services initialized and ready")
    
    def get_pipeline(self):
        """Get facial recognition pipeline (lazy loads on first access)."""
        self._ensure_pipeline_initialized()
        return self._pipeline
    
    def get_voice_notifier(self):
        """
        Get the voice notifier (lazy loads on first access).

        Never returns None: callers invoke methods like notify_present()
        inline in request handling, and an AttributeError on a missing optional
        package must never turn into a 500. Falls back to a no-op notifier.
        """
        self._ensure_voice_initialized()
        if self._voice_notifier is None:
            return _NullVoiceNotifier()
        return self._voice_notifier
    
    def register_student_face(self, image_file, student: StudentProfile, max_attempts=6) -> dict:
        """
        Register student face with enhanced processing and multiple attempts.
        
        Args:
            image_file: Django uploaded file
            student: StudentProfile instance
            max_attempts: Maximum registration attempts (default 6 for environment-adaptive processing)
        
        Returns:
            dict with registration status and details
        """
        result = {
            'success': False,
            'message': '',
            'encoding': None,
            'attempts_made': 0,
            'processing_method': None
        }
        
        try:
            # Ensure pipeline is initialized
            self._ensure_pipeline_initialized()
            
            # Import ImageProcessor
            from apps.ai_core.facial_recognition import ImageProcessor
            
            # Convert image to numpy array
            image = Image.open(image_file)
            image_array = ImageProcessor.convert_pil_to_cv2(image)
            
            if image_array is None:
                result['message'] = 'Failed to process image file'
                return result
            
            # Register face with multiple attempts
            success, encoding, message, metadata = self._pipeline.register_face(
                image_array,
                str(student.user.id),
                max_attempts=max_attempts
            )
            
            # Handle metadata safely
            attempts_used = max_attempts
            processing_method = 'unknown'
            
            if metadata and isinstance(metadata, dict):
                attempts_used = metadata.get('attempt_used', metadata.get('attempts_made', max_attempts))
                processing_method = metadata.get('processing_method', metadata.get('method_used', 'unknown'))
            
            result['attempts_made'] = attempts_used if success else max_attempts
            
            if success:
                # Update student profile
                student.set_face_embedding(encoding)
                student.is_face_registered = True
                from django.utils import timezone
                student.face_encoding_updated_at = timezone.now()
                student.save()
                
                # Save face image to database
                image_file.seek(0)
                StudentFaceImage.objects.create(
                    student=student,
                    image=image_file,
                    is_verified=True,
                    is_training_data=True
                )
                
                # Save updated training data
                training_data_path = os.path.join(
                    settings.AI_SETTINGS['MODELS_DIR'],
                    'face_encodings.pkl'
                )
                self._pipeline.save_training_data(training_data_path)
                
                result['success'] = True
                result['message'] = message
                result['encoding'] = encoding.tobytes()
                result['processing_method'] = processing_method
                
                logger.info(f"Student face registered successfully: {student.roll_number} using {processing_method} (attempt {attempts_used})")
            else:
                result['message'] = message or f"Registration failed after {result['attempts_made']} attempts"
                logger.warning(f"Face registration failed for {student.roll_number}: {result['message']}")
        
        except Exception as e:
            result['message'] = f"Error registering face: {str(e)}"
            logger.error(f"Face registration error: {e}")
        
        return result
    
    def recognize_student_face(self, image_file, get_all_matches: bool = False) -> dict:
        """
        Recognize student face from image.
        
        Args:
            image_file: Django uploaded file or bytes
            get_all_matches: Whether to return all matches
        
        Returns:
            dict with recognition result
        """
        try:
            # Ensure pipeline is initialized
            self._ensure_pipeline_initialized()
            
            # Load all registered faces if storage is empty
            if self._pipeline.storage.count() == 0:
                logger.info("Storage empty, loading all registered student faces...")
                self.load_all_student_faces()
            
            # Import ImageProcessor
            from apps.ai_core.facial_recognition import ImageProcessor
            
            # Convert image to numpy array
            if isinstance(image_file, bytes):
                image_array = ImageProcessor.convert_image_bytes_to_cv2(image_file)
            else:
                image = Image.open(image_file)
                image_array = ImageProcessor.convert_pil_to_cv2(image)
            
            # Recognize face
            result = self._pipeline.recognize_face(
                image_array,
                return_all_matches=get_all_matches
            )
            
            if result['success']:
                # Get student
                try:
                    user_id = int(result['student_id'])
                    student = StudentProfile.objects.get(user_id=user_id)
                    result['student'] = {
                        'id': student.user.id,
                        'roll_number': student.roll_number,
                        'name': student.user.get_full_name(),
                        'email': student.user.email
                    }
                except StudentProfile.DoesNotExist:
                    logger.error(f"Student profile not found for user_id={result['student_id']}")
                    result['success'] = False
                    result['error'] = f"Student profile not found for ID {result['student_id']}"
                except Exception as e:
                    logger.error(f"Error fetching student profile: {e}")
                    result['success'] = False
                    result['error'] = f"Error fetching student: {str(e)}"
            
            return result
        
        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return {
                'success': False,
                'error': str(e),
                'face_detected': False
            }
    
    def load_all_student_faces(self) -> bool:
        """Load all registered student faces into pipeline."""
        try:
            # Ensure pipeline is initialized
            self._ensure_pipeline_initialized()
            
            students = StudentProfile.objects.filter(
                is_face_registered=True,
                face_embedding__isnull=False
            )
            
            count = 0
            for student in students:
                encoding = student.get_face_embedding()
                if encoding is not None:
                    # Use storage API to add encoding
                    self._pipeline.storage.add_encoding(str(student.user.id), encoding)
                    count += 1
            
            logger.info(f"Loaded {count} student face encodings into pipeline storage")
            return True
        except AIFeatureUnavailable:
            # "the feature is switched off" is not the same as "the load
            # failed" - let it reach the client as a 503.
            raise
        except Exception as e:
            logger.error(f"Error loading student faces: {e}")
            return False
    
    def save_training_data(self) -> bool:
        """Save current training data."""
        try:
            # Ensure pipeline is initialized
            self._ensure_pipeline_initialized()
            
            training_data_path = os.path.join(
                settings.AI_SETTINGS['MODELS_DIR'],
                'face_encodings.pkl'
            )
            return self._pipeline.save_training_data(training_data_path)
        except AIFeatureUnavailable:
            raise
        except Exception as e:
            logger.error(f"Error saving training data: {e}")
            return False
    
    def set_confidence_threshold(self, threshold: float) -> bool:
        """Adjust confidence threshold for recognition."""
        # Ensure pipeline is initialized
        self._ensure_pipeline_initialized()
        
        if 0 <= threshold <= 1:
            self._pipeline.confidence_threshold = threshold
            logger.info(f"Confidence threshold set to {threshold}")
            return True
        return False
    
    def check_face_duplicate(self, image_file, current_student_roll: str) -> dict:
        """
        Check if the face in the image is already registered for another student.
        
        Args:
            image_file: Django uploaded file containing face image
            current_student_roll: Roll number of student trying to register (to exclude from duplicate check)
        
        Returns:
            dict with 'is_duplicate' boolean and 'existing_student' if duplicate found
        """
        result = {
            'is_duplicate': False,
            'existing_student': None,
            'confidence': 0.0
        }
        
        try:
            # Ensure pipeline is initialized
            self._ensure_pipeline_initialized()
            
            # Convert image to numpy array
            from PIL import Image
            from apps.ai_core.facial_recognition import ImageProcessor
            
            # Safe import of face_recognition with error handling
            try:
                import face_recognition
                import numpy as np
                HAS_FACE_RECOGNITION = True
            except ImportError as e:
                logger.warning(f"Face recognition models not available: {e}")
                logger.info("Please install face_recognition_models: pip install git+https://github.com/ageitgey/face_recognition_models")
                result['status'] = 'warning'
                result['message'] = 'Face recognition models not installed. Basic duplicate check performed.'
                return result
            
            logger.info(f"Starting duplicate check for student: {current_student_roll}")
            
            image = Image.open(image_file)
            image_array = ImageProcessor.convert_pil_to_cv2(image)
            
            if image_array is None:
                logger.warning("Could not convert image for duplicate check")
                return result
            
            # Get face encoding for the input image
            logger.debug("Extracting face encoding from input image...")
            encoding, error_message, face_location, metadata = self._pipeline._extract_face_encoding(
                image_array, 
                check_quality=False  # Skip quality checks for faster comparison
            )
            
            if encoding is None:
                logger.warning(f"Could not extract face encoding for duplicate check: {error_message}")
                return result
                
            # Ensure encoding is a proper numpy array
            if not isinstance(encoding, np.ndarray):
                logger.warning(f"Encoding is not numpy array: {type(encoding)}")
                return result
                
            if encoding.size == 0:
                logger.warning("Face encoding is empty for duplicate check")
                return result
            
            logger.info(f"Successfully extracted encoding of shape: {encoding.shape}")
            
            # Get all registered students (excluding current student)
            registered_students = StudentProfile.objects.filter(
                is_face_registered=True,
                face_embedding__isnull=False
            ).exclude(roll_number=current_student_roll)
            
            logger.info(f"Checking for duplicates against {registered_students.count()} registered students")
            
            # Check against each registered student's face
            for student in registered_students:
                try:
                    logger.debug(f"Checking student: {student.roll_number}")
                    
                    # Get stored encoding safely
                    stored_encoding = None
                    try:
                        stored_encoding = student.get_face_embedding()
                    except Exception as encoding_error:
                        logger.error(f"Failed to get encoding for student {student.roll_number}: {encoding_error}")
                        continue
                    
                    # Validate stored encoding
                    if stored_encoding is None:
                        logger.debug(f"Student {student.roll_number} has no face encoding")
                        continue
                        
                    if not isinstance(stored_encoding, np.ndarray):
                        logger.debug(f"Student {student.roll_number} encoding is not numpy array: {type(stored_encoding)}")
                        continue
                        
                    if stored_encoding.size == 0:
                        logger.debug(f"Student {student.roll_number} has empty encoding")
                        continue
                    
                    logger.debug(f"Student {student.roll_number} encoding shape: {stored_encoding.shape}")
                    
                    # Use a more sensitive tolerance for duplicate detection
                    tolerance = 0.5
                    
                    # Perform face comparison safely
                    try:
                        logger.debug(f"Comparing faces for student {student.roll_number}...")
                        
                        # Ensure both encodings are properly formatted
                        stored_encoding_list = [stored_encoding]  # Wrap in list for face_recognition
                        
                        matches = face_recognition.compare_faces(
                            stored_encoding_list, 
                            encoding, 
                            tolerance=tolerance
                        )
                        
                        distances = face_recognition.face_distance(stored_encoding_list, encoding)
                        
                        if len(matches) > 0 and len(distances) > 0:
                            match_found = bool(matches[0])  # Explicit boolean conversion
                            distance = float(distances[0])  # Explicit float conversion
                            confidence = 1 - distance
                            
                            logger.info(f"Student {student.roll_number}: distance={distance:.3f}, confidence={confidence:.3f}, match={match_found}")
                            
                            if match_found:  # Face match found
                                result['is_duplicate'] = True
                                result['existing_student'] = student.roll_number
                                result['confidence'] = confidence
                                
                                logger.warning(f"Duplicate face detected! Face matches student {student.roll_number} with {confidence:.2f} confidence")
                                return result
                        else:
                            logger.warning(f"Empty comparison results for student {student.roll_number}")
                            
                    except Exception as comparison_error:
                        logger.error(f"Face comparison failed for student {student.roll_number}: {comparison_error}")
                        continue
                        
                except Exception as student_error:
                    logger.error(f"Error processing student {student.roll_number}: {student_error}")
                    continue
            
            logger.info("No duplicate faces found")
            
        except Exception as e:
            logger.error(f"Error during duplicate face check: {e}")
        
        return result


def get_ai_manager() -> AIServiceManager:
    """Get singleton AI service manager."""
    return AIServiceManager()
