"""
Improved AI services with better separation of concerns and proper singleton implementation.
"""
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from PIL import Image
import os

from apps.student.models import StudentProfile, StudentFaceImage

logger = logging.getLogger(__name__)


class ServiceInterface(ABC):
    """Base interface for all AI services."""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available and properly initialized."""
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service."""
        pass


class FaceRecognitionServiceInterface(ServiceInterface):
    """Interface for face recognition services."""
    
    @abstractmethod
    def register_face(self, image: Union[UploadedFile, bytes], student: StudentProfile) -> Dict[str, Any]:
        """Register a student's face."""
        pass
    
    @abstractmethod
    def recognize_face(self, image: Union[UploadedFile, bytes], **kwargs) -> Dict[str, Any]:
        """Recognize a face in an image."""
        pass
    
    @abstractmethod
    def load_training_data(self) -> bool:
        """Load training data."""
        pass
    
    @abstractmethod
    def save_training_data(self) -> bool:
        """Save training data."""
        pass


class VoiceNotificationServiceInterface(ServiceInterface):
    """Interface for voice notification services."""
    
    @abstractmethod
    def notify_attendance_marked(self, student_name: str, status: str) -> bool:
        """Notify about attendance marking."""
        pass
    
    @abstractmethod
    def notify_recognition_result(self, result: Dict[str, Any]) -> bool:
        """Notify about face recognition result."""
        pass


class ThreadSafeSingleton(type):
    """
    Thread-safe singleton metaclass.
    """
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class FaceRecognitionService(FaceRecognitionServiceInterface, metaclass=ThreadSafeSingleton):
    """
    Thread-safe face recognition service implementation.
    """
    
    def __init__(self):
        self._pipeline = None
        self._pipeline_lock = threading.RLock()
        self._is_initialized = False
        self._initialization_error = None
    
    def _ensure_initialized(self):
        """Ensure the service is initialized (thread-safe)."""
        if self._is_initialized and self._pipeline is not None:
            return
        
        with self._pipeline_lock:
            if self._is_initialized and self._pipeline is not None:
                return
            
            try:
                self._initialize_pipeline()
                self._is_initialized = True
                self._initialization_error = None
            except Exception as e:
                self._initialization_error = str(e)
                logger.error(f"Failed to initialize face recognition pipeline: {e}")
                raise
    
    def _initialize_pipeline(self):
        """Initialize the facial recognition pipeline."""
        try:
            from apps.ai_core.facial_recognition import FacialRecognitionPipeline
            
            self._pipeline = FacialRecognitionPipeline()
            
            # Load existing training data
            training_data_path = os.path.join(
                settings.AI_SETTINGS['MODELS_DIR'],
                'face_encodings.pkl'
            )
            if os.path.exists(training_data_path):
                self._pipeline.load_training_data(training_data_path)
            
            logger.info("Face recognition pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing face recognition pipeline: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if the service is available."""
        try:
            self._ensure_initialized()
            return self._pipeline is not None and self._is_initialized
        except:
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            'service_name': 'Face Recognition Service',
            'is_available': self.is_available(),
            'is_initialized': self._is_initialized,
            'initialization_error': self._initialization_error,
            'pipeline_loaded': self._pipeline is not None
        }
    
    def register_face(self, image: Union[UploadedFile, bytes], student: StudentProfile) -> Dict[str, Any]:
        """Register a student's face."""
        result = {
            'success': False,
            'message': '',
            'encoding': None,
            'attempts_made': 0,
            'processing_method': None
        }
        
        try:
            self._ensure_initialized()
            
            from apps.ai_core.facial_recognition import ImageProcessor
            
            # Process image
            if isinstance(image, bytes):
                image_array = ImageProcessor.convert_image_bytes_to_cv2(image)
            else:
                pil_image = Image.open(image)
                image_array = ImageProcessor.convert_pil_to_cv2(pil_image)
            
            if image_array is None:
                result['message'] = 'Failed to process image file'
                return result
            
            # Register with pipeline
            with self._pipeline_lock:
                success, encoding, message, metadata = self._pipeline.register_face(
                    image_array,
                    str(student.user.id),
                    max_attempts=6
                )
            
            if success:
                # Update student profile
                student.set_face_embedding(encoding)
                student.is_face_registered = True
                from django.utils import timezone
                student.face_encoding_updated_at = timezone.now()
                student.save()
                
                # Save face image
                if not isinstance(image, bytes):
                    image.seek(0)
                    StudentFaceImage.objects.create(
                        student=student,
                        image=image,
                        is_verified=True,
                        is_training_data=True
                    )
                
                # Save training data
                self.save_training_data()
                
                result['success'] = True
                result['message'] = message
                result['encoding'] = encoding.tobytes() if encoding is not None else None
                result['attempts_made'] = metadata.get('attempts_made', 1) if metadata else 1
                result['processing_method'] = metadata.get('processing_method', 'unknown') if metadata else 'unknown'
                
                logger.info(f"Face registered successfully for student {student.roll_number}")
            else:
                result['message'] = message or "Registration failed"
                result['attempts_made'] = 6
                
        except Exception as e:
            result['message'] = f"Error registering face: {str(e)}"
            logger.error(f"Face registration error: {e}")
        
        return result
    
    def recognize_face(self, image: Union[UploadedFile, bytes], **kwargs) -> Dict[str, Any]:
        """Recognize a face in an image."""
        try:
            self._ensure_initialized()
            
            # Load student faces if storage is empty
            if self._pipeline.storage.count() == 0:
                self.load_training_data()
            
            from apps.ai_core.facial_recognition import ImageProcessor
            
            # Process image
            if isinstance(image, bytes):
                image_array = ImageProcessor.convert_image_bytes_to_cv2(image)
            else:
                pil_image = Image.open(image)
                image_array = ImageProcessor.convert_pil_to_cv2(pil_image)
            
            # Recognize face
            with self._pipeline_lock:
                result = self._pipeline.recognize_face(
                    image_array,
                    return_all_matches=kwargs.get('get_all_matches', False)
                )
            
            if result['success'] and 'student_id' in result:
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
                    logger.error(f"Student not found for user_id={result['student_id']}")
                    result['success'] = False
                    result['error'] = f"Student not found"
            
            return result
            
        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return {
                'success': False,
                'error': str(e),
                'face_detected': False
            }
    
    def load_training_data(self) -> bool:
        """Load all registered student faces."""
        try:
            self._ensure_initialized()
            
            students = StudentProfile.objects.filter(
                is_face_registered=True,
                face_embedding__isnull=False
            )
            
            count = 0
            with self._pipeline_lock:
                for student in students:
                    encoding = student.get_face_embedding()
                    if encoding is not None:
                        self._pipeline.storage.add_encoding(str(student.user.id), encoding)
                        count += 1
            
            logger.info(f"Loaded {count} student face encodings")
            return True
            
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return False
    
    def save_training_data(self) -> bool:
        """Save training data to disk."""
        try:
            self._ensure_initialized()
            
            training_data_path = os.path.join(
                settings.AI_SETTINGS['MODELS_DIR'],
                'face_encodings.pkl'
            )
            
            with self._pipeline_lock:
                return self._pipeline.save_training_data(training_data_path)
                
        except Exception as e:
            logger.error(f"Error saving training data: {e}")
            return False


class VoiceNotificationService(VoiceNotificationServiceInterface, metaclass=ThreadSafeSingleton):
    """
    Thread-safe voice notification service implementation.
    """
    
    def __init__(self):
        self._voice_notifier = None
        self._is_initialized = False
        self._initialization_error = None
        self._lock = threading.Lock()
    
    def _ensure_initialized(self):
        """Ensure the service is initialized (thread-safe)."""
        if self._is_initialized and self._voice_notifier is not None:
            return
        
        with self._lock:
            if self._is_initialized and self._voice_notifier is not None:
                return
            
            try:
                from apps.ai_core.voice_notifier import AttendanceVoiceNotifier
                self._voice_notifier = AttendanceVoiceNotifier()
                self._is_initialized = True
                self._initialization_error = None
                logger.info("Voice notification service initialized")
            except Exception as e:
                self._initialization_error = str(e)
                logger.warning(f"Voice notification service unavailable: {e}")
                # Don't raise - voice is optional
    
    def is_available(self) -> bool:
        """Check if the service is available."""
        try:
            self._ensure_initialized()
            return self._voice_notifier is not None
        except:
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            'service_name': 'Voice Notification Service',
            'is_available': self.is_available(),
            'is_initialized': self._is_initialized,
            'initialization_error': self._initialization_error,
            'notifier_loaded': self._voice_notifier is not None
        }
    
    def notify_attendance_marked(self, student_name: str, status: str) -> bool:
        """Notify about attendance marking."""
        try:
            self._ensure_initialized()
            if self._voice_notifier:
                return self._voice_notifier.announce_attendance(student_name, status)
            return False
        except Exception as e:
            logger.error(f"Error in voice notification: {e}")
            return False
    
    def notify_recognition_result(self, result: Dict[str, Any]) -> bool:
        """Notify about face recognition result."""
        try:
            if result.get('success') and 'student' in result:
                student_name = result['student'].get('name', 'Unknown')
                return self.notify_attendance_marked(student_name, 'present')
            return False
        except Exception as e:
            logger.error(f"Error in recognition notification: {e}")
            return False


class AIServiceRegistry(metaclass=ThreadSafeSingleton):
    """
    Central registry for all AI services.
    Provides a single point of access to all AI services with proper error handling.
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceInterface] = {}
        self._register_default_services()
    
    def _register_default_services(self):
        """Register default services."""
        self._services['face_recognition'] = FaceRecognitionService()
        self._services['voice_notification'] = VoiceNotificationService()
    
    def register_service(self, name: str, service: ServiceInterface):
        """Register a new service."""
        if not isinstance(service, ServiceInterface):
            raise ValueError("Service must implement ServiceInterface")
        self._services[name] = service
        logger.info(f"Registered service: {name}")
    
    def get_service(self, name: str) -> Optional[ServiceInterface]:
        """Get a service by name."""
        return self._services.get(name)
    
    def get_face_recognition_service(self) -> Optional[FaceRecognitionServiceInterface]:
        """Get the face recognition service."""
        return self._services.get('face_recognition')
    
    def get_voice_notification_service(self) -> Optional[VoiceNotificationServiceInterface]:
        """Get the voice notification service."""
        return self._services.get('voice_notification')
    
    def get_available_services(self) -> List[str]:
        """Get list of available (initialized) services."""
        return [name for name, service in self._services.items() if service.is_available()]
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services."""
        return {name: service.get_service_info() for name, service in self._services.items()}
    
    def initialize_all_services(self):
        """Initialize all services (for eager loading)."""
        logger.info("Initializing all AI services...")
        for name, service in self._services.items():
            try:
                service.is_available()  # This triggers initialization
                logger.info(f"Service '{name}' initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize service '{name}': {e}")
        
        # Load training data for face recognition
        face_service = self.get_face_recognition_service()
        if face_service and face_service.is_available():
            face_service.load_training_data()


# Convenience function for backward compatibility
def get_ai_manager() -> AIServiceRegistry:
    """Get the AI service registry (singleton)."""
    return AIServiceRegistry()