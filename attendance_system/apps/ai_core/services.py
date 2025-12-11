import logging
from django.conf import settings
from apps.student.models import StudentProfile, StudentFaceImage
from PIL import Image
import os

logger = logging.getLogger(__name__)


class AIServiceManager:
    """Singleton manager for AI services with lazy loading."""
    
    _instance = None
    _pipeline = None
    _voice_notifier = None
    _pipeline_initialized = False
    _voice_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _ensure_pipeline_initialized(self):
        if self._pipeline_initialized:
            return
        
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the facial recognition pipeline."""
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
            logger.error(f"Error initializing facial recognition pipeline: {e}")
            raise
    
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
    
    def get_pipeline(self):
        """Get facial recognition pipeline (lazy loads on first access)."""
        self._ensure_pipeline_initialized()
        return self._pipeline
    
    def get_voice_notifier(self):
        """Get voice notifier (lazy loads on first access)."""
        self._ensure_voice_initialized()
        return self._voice_notifier
    
    def register_student_face(self, image_file, student: StudentProfile) -> dict:
        """
        Register student face and update training data.
        
        Args:
            image_file: Django uploaded file
            student: StudentProfile instance
        
        Returns:
            dict with registration status and details
        """
        result = {
            'success': False,
            'message': '',
            'encoding': None
        }
        
        try:
            # Ensure pipeline is initialized
            self._ensure_pipeline_initialized()
            
            # Import ImageProcessor
            from apps.ai_core.facial_recognition import ImageProcessor
            
            # Convert image to numpy array
            image = Image.open(image_file)
            image_array = ImageProcessor.convert_pil_to_cv2(image)
            
            # Register face
            success, encoding, message = self._pipeline.register_face(
                image_array,
                str(student.user.id)
            )
            
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
                result['message'] = 'Face registered successfully'
                result['encoding'] = encoding.tobytes()
                
                logger.info(f"Student face registered: {student.roll_number}")
            else:
                result['message'] = message
        
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
                        'id': student.id,
                        'roll_number': student.roll_number,
                        'name': student.user.get_full_name(),
                        'email': student.user.email
                    }
                except StudentProfile.DoesNotExist:
                    result['success'] = False
                    result['error'] = 'Student not found'
            
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
                    self._pipeline.known_encodings[str(student.user.id)] = encoding
                    count += 1
            
            logger.info(f"Loaded {count} student face encodings")
            return True
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


def get_ai_manager() -> AIServiceManager:
    """Get singleton AI service manager."""
    return AIServiceManager()
