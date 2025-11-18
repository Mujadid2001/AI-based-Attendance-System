"""
AI/ML service layer for Django integration.
"""
import logging
from django.conf import settings
from apps.ai_core.facial_recognition import (
    FacialRecognitionPipeline, CVFaceDetector,
    FaceRecognitionLibRecognizer, ImageProcessor
)
from apps.ai_core.voice_notifier import AttendanceVoiceNotifier
from apps.student.models import StudentProfile, StudentFaceImage
from PIL import Image
import os

logger = logging.getLogger(__name__)


class AIServiceManager:
    """Singleton manager for AI services."""
    
    _instance = None
    _pipeline = None
    _voice_notifier = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize AI services."""
        try:
            # Initialize facial recognition pipeline
            self._pipeline = FacialRecognitionPipeline(
                face_detector=CVFaceDetector(),
                face_recognizer=FaceRecognitionLibRecognizer(model='cnn'),
                confidence_threshold=settings.AI_SETTINGS['FACE_RECOGNITION_THRESHOLD']
            )
            
            # Load training data
            training_data_path = os.path.join(
                settings.AI_SETTINGS['MODELS_DIR'],
                'face_encodings.pkl'
            )
            self._pipeline.load_training_data(training_data_path)
            
            # Initialize voice notifier
            self._voice_notifier = AttendanceVoiceNotifier()
            
            logger.info("AI services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AI services: {e}")
    
    def get_pipeline(self) -> FacialRecognitionPipeline:
        """Get facial recognition pipeline."""
        return self._pipeline
    
    def get_voice_notifier(self) -> AttendanceVoiceNotifier:
        """Get voice notifier."""
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
        if 0 <= threshold <= 1:
            self._pipeline.confidence_threshold = threshold
            logger.info(f"Confidence threshold set to {threshold}")
            return True
        return False


def get_ai_manager() -> AIServiceManager:
    """Get singleton AI service manager."""
    return AIServiceManager()
