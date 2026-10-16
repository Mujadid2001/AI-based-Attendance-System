"""
AI Core and Application-specific settings.
Used by both development and production environments.
"""
import os
from .base import BASE_DIR, PROJECT_ROOT

# AI Core settings
AI_SETTINGS = {
    'FACE_DETECTION_CONFIDENCE': 0.4,
    'FACE_RECOGNITION_THRESHOLD': 0.4,
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

# Ensure required directories exist.
#
# These must never be able to take the whole app down: some PaaS filesystems
# are read-only outside your home directory, and an unhandled OSError while
# importing settings means every single request returns a 500.
import logging

logger = logging.getLogger(__name__)

for _path in (
    os.path.join(BASE_DIR, 'logs'),
    AI_SETTINGS['TRAINING_DATA_DIR'],
    AI_SETTINGS['MODELS_DIR'],
):
    try:
        os.makedirs(_path, exist_ok=True)
    except OSError as exc:
        logger.warning('Could not create directory %s: %s', _path, exc)

