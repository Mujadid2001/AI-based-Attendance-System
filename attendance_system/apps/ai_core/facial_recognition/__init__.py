"""
Facial Recognition Package

Public API exports maintain backward compatibility with existing code.
"""

# Export abstract base classes
from .base import (
    FaceDetector,
    FaceRecognizer,
    LivenessDetector,
)

# Export concrete implementations - detectors
from .detectors import (
    CVFaceDetector,
    DNNFaceDetector,
    MTCNNFaceDetector,
    DlibFaceDetector,
)

# Export concrete implementations - recognizers
from .recognizers import FaceRecognitionLibRecognizer

# Export concrete implementations - liveness
from .liveness import (
    BlinkLivenessDetector,
    MotionLivenessDetector,
)

# Export utilities
from .utils import ImageProcessor, FaceQualityChecker

# Export alignment
from .alignment import FaceAligner, SimpleFaceAligner

# Export storage
from .storage import TrainingDataStorage

# Export preprocessing
from .preprocessing import ImagePreprocessor

# Export detection orchestrator
from .detection_orchestrator import (
    IntelligentDetectionOrchestrator,
    DetectionConfidenceCalculator,
    DetectionResult,
    DetectionConfidenceLevel,
)

# Export main pipeline
from .pipeline import FacialRecognitionPipeline


__all__ = [
    # Abstract base classes
    'FaceDetector',
    'FaceRecognizer',
    'LivenessDetector',
    
    # Concrete implementations - detectors
    'CVFaceDetector',
    'DNNFaceDetector',
    'MTCNNFaceDetector',
    'DlibFaceDetector',
    
    # Concrete implementations - recognizers
    'FaceRecognitionLibRecognizer',
    
    # Concrete implementations - liveness
    'BlinkLivenessDetector',
    'MotionLivenessDetector',
    
    # Utilities
    'ImageProcessor',
    'FaceQualityChecker',
    
    # Alignment
    'FaceAligner',
    'SimpleFaceAligner',
    
    # Storage
    'TrainingDataStorage',
    
    # Preprocessing
    'ImagePreprocessor',
    
    # Detection orchestration
    'IntelligentDetectionOrchestrator',
    'DetectionConfidenceCalculator',
    'DetectionResult',
    'DetectionConfidenceLevel',
    
    # Main pipeline
    'FacialRecognitionPipeline',
]
