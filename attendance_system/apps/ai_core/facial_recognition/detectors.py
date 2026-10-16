"""Face detection implementations."""
import logging
from typing import Optional, List, Tuple
import os

from .base import FaceDetector


logger = logging.getLogger(__name__)

# Conditional imports for optional dependencies
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    cv2 = None
    HAS_CV2 = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False


class CVFaceDetector(FaceDetector):
    """OpenCV Cascade Classifier based face detector."""
    
    def __init__(self, cascade_path: Optional[str] = None):
        """Initialize face detector."""
        if not HAS_CV2:
            raise RuntimeError("OpenCV not installed")
        
        if cascade_path is None:
            cascade_path = f"{cv2.data.haarcascades}haarcascade_frontalface_default.xml"
        
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
    
    def detect_faces(self, image):
        """Detect faces using Haar Cascade."""
        if not HAS_CV2:
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        return faces


class DNNFaceDetector(FaceDetector):
    """OpenCV DNN-based face detector using ResNet SSD model.
    
    More accurate than Haar Cascade, works better with varying angles and lighting.
    """
    
    def __init__(self, model_path: Optional[str] = None, config_path: Optional[str] = None, 
                 confidence_threshold: float = 0.5):
        """Initialize DNN face detector.
        
        Args:
            model_path: Path to .caffemodel file
            config_path: Path to .prototxt file
            confidence_threshold: Minimum confidence for detection
        """
        if not HAS_CV2:
            raise RuntimeError("OpenCV not installed")
        
        self.confidence_threshold = confidence_threshold
        
        # Default paths for ResNet SSD model
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), 
                                     '../../../../models/res10_300x300_ssd_iter_140000.caffemodel')
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__),
                                      '../../../../models/deploy.prototxt')
        
        try:
            if os.path.exists(model_path) and os.path.exists(config_path):
                self.net = cv2.dnn.readNetFromCaffe(config_path, model_path)
                logger.info("DNN face detector initialized successfully")
            else:
                logger.warning(f"DNN model files not found. Using default detector.")
                logger.warning(f"Model: {model_path}")
                logger.warning(f"Config: {config_path}")
                self.net = None
        except Exception as e:
            logger.error(f"Could not load DNN model: {e}")
            self.net = None
    
    def detect_faces(self, image) -> List[Tuple[int, int, int, int]]:
        """Detect faces using DNN model.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            List of face bounding boxes as (x, y, w, h)
        """
        if not HAS_CV2 or self.net is None:
            return []
        
        try:
            h, w = image.shape[:2]
            
            # Create blob from image
            blob = cv2.dnn.blobFromImage(
                cv2.resize(image, (300, 300)), 
                1.0, 
                (300, 300), 
                (104.0, 177.0, 123.0)
            )
            
            # Forward pass
            self.net.setInput(blob)
            detections = self.net.forward()
            
            faces = []
            
            # Process detections
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                if confidence > self.confidence_threshold:
                    # Get bounding box coordinates
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (x1, y1, x2, y2) = box.astype("int")
                    
                    # Convert to (x, y, w, h) format
                    x = max(0, x1)
                    y = max(0, y1)
                    width = min(w - x, x2 - x1)
                    height = min(h - y, y2 - y1)
                    
                    faces.append((x, y, width, height))
            
            return faces
            
        except Exception as e:
            logger.error(f"Error in DNN face detection: {e}")
            return []


class MTCNNFaceDetector(FaceDetector):
    """MTCNN (Multi-task Cascaded Convolutional Networks) face detector.
    
    High accuracy detector that also provides facial landmarks.
    Requires mtcnn package: pip install mtcnn
    """
    
    def __init__(self, min_face_size: int = 20, scale_factor: float = 0.709, 
                 confidence_threshold: float = 0.7):
        """Initialize MTCNN detector.
        
        Args:
            min_face_size: Minimum face size to detect
            scale_factor: Scale factor for image pyramid
            confidence_threshold: Minimum confidence for detection
        """
        try:
            from mtcnn import MTCNN
            self.detector = MTCNN(
                min_face_size=min_face_size,
                scale_factor=scale_factor
            )
            self.confidence_threshold = confidence_threshold
            logger.info("MTCNN face detector initialized successfully")
        except ImportError:
            logger.warning("MTCNN not installed. Install with: pip install mtcnn")
            self.detector = None
        except Exception as e:
            logger.error(f"Could not initialize MTCNN: {e}")
            self.detector = None
    
    def detect_faces(self, image) -> List[Tuple[int, int, int, int]]:
        """Detect faces using MTCNN.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            List of face bounding boxes as (x, y, w, h)
        """
        if self.detector is None:
            return []
        
        try:
            # MTCNN expects RGB
            if HAS_CV2 and len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            # Detect faces
            detections = self.detector.detect_faces(rgb_image)
            
            faces = []
            for detection in detections:
                if detection['confidence'] >= self.confidence_threshold:
                    box = detection['box']
                    # box format: [x, y, width, height]
                    x, y, w, h = box
                    # Ensure non-negative coordinates
                    x = max(0, x)
                    y = max(0, y)
                    faces.append((x, y, w, h))
            
            return faces
            
        except Exception as e:
            logger.error(f"Error in MTCNN face detection: {e}")
            return []


class DlibFaceDetector(FaceDetector):
    """Dlib HOG-based face detector.
    
    Good balance between speed and accuracy.
    """
    
    def __init__(self, upsample_times: int = 0):
        """Initialize dlib detector.
        
        Args:
            upsample_times: Number of times to upsample image before detection
        """
        try:
            import dlib
            self.detector = dlib.get_frontal_face_detector()
            self.upsample_times = upsample_times
            logger.info("Dlib face detector initialized successfully")
        except ImportError:
            logger.warning("Dlib not installed. Install with: pip install dlib")
            self.detector = None
        except Exception as e:
            logger.error(f"Could not initialize dlib detector: {e}")
            self.detector = None
    
    def detect_faces(self, image) -> List[Tuple[int, int, int, int]]:
        """Detect faces using dlib HOG detector.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            List of face bounding boxes as (x, y, w, h)
        """
        if self.detector is None:
            return []
        
        try:
            # Convert to grayscale if needed
            if HAS_CV2 and len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Detect faces
            dets = self.detector(gray, self.upsample_times)
            
            faces = []
            for det in dets:
                x = det.left()
                y = det.top()
                w = det.right() - x
                h = det.bottom() - y
                faces.append((x, y, w, h))
            
            return faces
            
        except Exception as e:
            logger.error(f"Error in dlib face detection: {e}")
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return self.face_cascade.detectMultiScale(gray, 1.1, 5)
