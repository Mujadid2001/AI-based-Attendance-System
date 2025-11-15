"""
Voice notification service for attendance feedback.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional
import pyttsx3
import threading

logger = logging.getLogger(__name__)


class VoiceNotificationService(ABC):
    """Abstract base class for voice notifications."""
    
    @abstractmethod
    def speak(self, text: str, wait: bool = True) -> bool:
        """Speak text."""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop current speech."""
        pass


class PyTTSX3VoiceNotifier(VoiceNotificationService):
    """Voice notification using pyttsx3."""
    
    def __init__(self, rate: int = 150, voice_index: int = 0):
        """
        Initialize voice notifier.
        
        Args:
            rate: Speech rate (words per minute)
            voice_index: Voice index (0 = default, 1+ = alternative voices)
        """
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            
            voices = self.engine.getProperty('voices')
            if voice_index < len(voices):
                self.engine.setProperty('voice', voices[voice_index].id)
            
            logger.info(f"Voice notifier initialized (rate: {rate})")
        except Exception as e:
            logger.error(f"Error initializing voice notifier: {e}")
            self.engine = None
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """Speak text using pyttsx3."""
        if not self.engine:
            logger.warning("Voice engine not initialized")
            return False
        
        try:
            self.engine.say(text)
            if wait:
                self.engine.runAndWait()
            else:
                # Run in background thread
                thread = threading.Thread(target=self.engine.runAndWait)
                thread.daemon = True
                thread.start()
            
            logger.info(f"Speaking: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error speaking: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop current speech."""
        try:
            if self.engine:
                self.engine.stop()
                return True
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")
        return False


class AttendanceVoiceNotifier:
    """Attendance-specific voice notifications."""
    
    # Predefined messages
    MESSAGES = {
        'present': "Attendance marked. You are present.",
        'late': "Attendance marked. You are late.",
        'already_recorded': "Your attendance is already recorded.",
        'duplicate_entry': "Duplicate entry detected. Please wait before checking in again.",
        'face_not_registered': "Face not registered. Please register your face first.",
        'face_not_recognized': "Face not recognized. Please try again.",
        'multiple_faces': "Multiple faces detected. Please show only your face.",
        'liveness_failed': "Liveness check failed. Please show your live face.",
        'error': "An error occurred. Please try again.",
        'welcome': "Welcome. Please stand in front of the camera.",
    }
    
    def __init__(self, voice_service: Optional[VoiceNotificationService] = None):
        """Initialize attendance notifier."""
        self.voice_service = voice_service or PyTTSX3VoiceNotifier()
    
    def notify_present(self, wait: bool = False) -> bool:
        """Notify that student is marked present."""
        return self.voice_service.speak(self.MESSAGES['present'], wait=wait)
    
    def notify_late(self, wait: bool = False) -> bool:
        """Notify that student is marked late."""
        return self.voice_service.speak(self.MESSAGES['late'], wait=wait)
    
    def notify_already_recorded(self, wait: bool = False) -> bool:
        """Notify that attendance is already recorded."""
        return self.voice_service.speak(
            self.MESSAGES['already_recorded'],
            wait=wait
        )
    
    def notify_face_not_registered(self, wait: bool = False) -> bool:
        """Notify that face is not registered."""
        return self.voice_service.speak(
            self.MESSAGES['face_not_registered'],
            wait=wait
        )
    
    def notify_face_not_recognized(self, wait: bool = False) -> bool:
        """Notify that face was not recognized."""
        return self.voice_service.speak(
            self.MESSAGES['face_not_recognized'],
            wait=wait
        )
    
    def notify_multiple_faces(self, wait: bool = False) -> bool:
        """Notify that multiple faces detected."""
        return self.voice_service.speak(
            self.MESSAGES['multiple_faces'],
            wait=wait
        )
    
    def notify_error(self, wait: bool = False) -> bool:
        """Notify generic error."""
        return self.voice_service.speak(self.MESSAGES['error'], wait=wait)
    
    def notify_welcome(self, wait: bool = False) -> bool:
        """Notify welcome message."""
        return self.voice_service.speak(self.MESSAGES['welcome'], wait=wait)
    
    def notify_custom(self, message: str, wait: bool = False) -> bool:
        """Notify with custom message."""
        return self.voice_service.speak(message, wait=wait)
