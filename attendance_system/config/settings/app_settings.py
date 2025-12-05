"""
AI Core and Application-specific settings.
Used by both development and production environments.
"""
import os
from .base import BASE_DIR, PROJECT_ROOT

# AI Core settings
AI_SETTINGS = {
    'FACE_DETECTION_CONFIDENCE': 0.5,
    'FACE_RECOGNITION_THRESHOLD': 0.6,
    'LIVENESS_THRESHOLD': 0.5,
    'MIN_FACE_SIZE': (20, 20),
    'MAX_FACE_SIZE': (500, 500),
    'MODELS_DIR': os.path.join(PROJECT_ROOT, 'models'),
    'TRAINING_DATA_DIR': os.path.join(BASE_DIR, 'media', 'training_data'),
}

# Attendance settings
ATTENDANCE_SETTINGS = {
    'LATE_ARRIVAL_MINUTES': 15,
    'DUPLICATE_ENTRY_TIMEOUT_MINUTES': 5,
}

# Voice settings
VOICE_SETTINGS = {
    'ENGINE': 'pyttsx3',
    'RATE': 150,
    'VOICE_ID': 0,
}

# Ensure required directories exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
os.makedirs(AI_SETTINGS['TRAINING_DATA_DIR'], exist_ok=True)
os.makedirs(AI_SETTINGS['MODELS_DIR'], exist_ok=True)
