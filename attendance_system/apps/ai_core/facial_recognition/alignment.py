"""Face alignment and preprocessing utilities."""
import logging
from typing import Tuple, Optional
import math

logger = logging.getLogger(__name__)

# Conditional imports
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import dlib
    HAS_DLIB = True
except ImportError:
    HAS_DLIB = False


class FaceAligner:
    """Align faces using facial landmarks for improved recognition accuracy."""
    
    # Standard facial landmark indices for 68-point model
    LEFT_EYE_INDICES = list(range(36, 42))
    RIGHT_EYE_INDICES = list(range(42, 48))
    
    def __init__(self, predictor_path: Optional[str] = None, desired_face_width: int = 256,
                 desired_left_eye: Tuple[float, float] = (0.35, 0.35)):
        """Initialize face aligner.
        
        Args:
            predictor_path: Path to dlib facial landmark predictor
            desired_face_width: Target width for aligned face
            desired_left_eye: Desired position of left eye as ratio of face size
        """
        self.desired_face_width = desired_face_width
        self.desired_left_eye = desired_left_eye
        self.predictor = None
        self.detector = None
        
        if HAS_DLIB:
            try:
                import os
                if predictor_path is None:
                    predictor_path = os.path.join(
                        os.path.dirname(__file__),
                        '../../../../models/shape_predictor_68_face_landmarks.dat'
                    )
                
                if os.path.exists(predictor_path):
                    self.predictor = dlib.shape_predictor(predictor_path)
                    self.detector = dlib.get_frontal_face_detector()
                    logger.info("Face aligner initialized successfully")
                else:
                    logger.warning(f"Landmark predictor not found at {predictor_path}")
            except Exception as e:
                logger.error(f"Could not initialize face aligner: {e}")
    
    def _get_eye_center(self, eye_points: np.ndarray) -> Tuple[int, int]:
        """Calculate center point of eye from landmarks.
        
        Args:
            eye_points: Array of (x, y) coordinates for eye landmarks
            
        Returns:
            (x, y) center coordinates
        """
        x = int(eye_points[:, 0].mean())
        y = int(eye_points[:, 1].mean())
        return (x, y)
    
    def _extract_eye_centers(self, shape) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Extract left and right eye centers from facial landmarks.
        
        Args:
            shape: Dlib facial landmarks shape
            
        Returns:
            Tuple of (left_eye_center, right_eye_center)
        """
        left_eye_pts = np.array([(shape.part(i).x, shape.part(i).y) 
                                 for i in self.LEFT_EYE_INDICES])
        right_eye_pts = np.array([(shape.part(i).x, shape.part(i).y) 
                                  for i in self.RIGHT_EYE_INDICES])
        
        left_eye_center = self._get_eye_center(left_eye_pts)
        right_eye_center = self._get_eye_center(right_eye_pts)
        
        return left_eye_center, right_eye_center
    
    def align_face(self, image, face_rect=None) -> Optional[np.ndarray]:
        """Align face in image using eye positions.
        
        Args:
            image: Input image
            face_rect: Optional face bounding box (x, y, w, h)
            
        Returns:
            Aligned face image or None if alignment fails
        """
        if not HAS_OPENCV or not HAS_DLIB or self.predictor is None:
            logger.warning("Face alignment dependencies not available")
            return image
        
        try:
            # Convert to grayscale for detection
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Detect face if not provided
            if face_rect is None:
                faces = self.detector(gray, 1)
                if len(faces) == 0:
                    logger.warning("No face detected for alignment")
                    return image
                face_rect = faces[0]
            else:
                # Convert from (x, y, w, h) to dlib rectangle
                x, y, w, h = face_rect
                face_rect = dlib.rectangle(x, y, x + w, y + h)
            
            # Get facial landmarks
            shape = self.predictor(gray, face_rect)
            
            # Extract eye centers
            left_eye_center, right_eye_center = self._extract_eye_centers(shape)
            
            # Calculate angle between eyes
            dY = right_eye_center[1] - left_eye_center[1]
            dX = right_eye_center[0] - left_eye_center[0]
            angle = math.degrees(math.atan2(dY, dX))
            
            # Calculate desired right eye position
            desired_right_eye_x = 1.0 - self.desired_left_eye[0]
            
            # Calculate distance between eyes
            dist = math.sqrt((dX ** 2) + (dY ** 2))
            desired_dist = (desired_right_eye_x - self.desired_left_eye[0]) * self.desired_face_width
            scale = desired_dist / dist
            
            # Calculate center point between eyes
            eyes_center = (
                (left_eye_center[0] + right_eye_center[0]) // 2,
                (left_eye_center[1] + right_eye_center[1]) // 2
            )
            
            # Get rotation matrix
            M = cv2.getRotationMatrix2D(eyes_center, angle, scale)
            
            # Update translation component
            tX = self.desired_face_width * 0.5
            tY = self.desired_face_width * self.desired_left_eye[1]
            M[0, 2] += (tX - eyes_center[0])
            M[1, 2] += (tY - eyes_center[1])
            
            # Apply affine transformation
            output_size = (self.desired_face_width, self.desired_face_width)
            aligned_face = cv2.warpAffine(
                image, M, output_size,
                flags=cv2.INTER_CUBIC
            )
            
            return aligned_face
            
        except Exception as e:
            logger.error(f"Error aligning face: {e}")
            return image
    
    def align_faces_batch(self, images, face_rects=None):
        """Align multiple faces.
        
        Args:
            images: List of input images
            face_rects: Optional list of face bounding boxes
            
        Returns:
            List of aligned face images
        """
        if face_rects is None:
            face_rects = [None] * len(images)
        
        aligned_faces = []
        for image, face_rect in zip(images, face_rects):
            aligned = self.align_face(image, face_rect)
            aligned_faces.append(aligned)
        
        return aligned_faces


class SimpleFaceAligner:
    """Simple face alignment without facial landmarks.
    
    Uses only face bounding box to crop and resize faces.
    Faster but less accurate than landmark-based alignment.
    """
    
    def __init__(self, target_size: Tuple[int, int] = (160, 160), 
                 margin: float = 0.2):
        """Initialize simple aligner.
        
        Args:
            target_size: Target (width, height) for output
            margin: Margin to add around face bbox as ratio
        """
        self.target_size = target_size
        self.margin = margin
    
    def align_face(self, image, face_rect: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """Align face using simple crop and resize.
        
        Args:
            image: Input image
            face_rect: Face bounding box (x, y, w, h)
            
        Returns:
            Aligned (cropped and resized) face image
        """
        if not HAS_OPENCV:
            return image
        
        try:
            x, y, w, h = face_rect
            
            # Add margin
            margin_x = int(w * self.margin)
            margin_y = int(h * self.margin)
            
            # Calculate crop coordinates
            x1 = max(0, x - margin_x)
            y1 = max(0, y - margin_y)
            x2 = min(image.shape[1], x + w + margin_x)
            y2 = min(image.shape[0], y + h + margin_y)
            
            # Crop face
            face_crop = image[y1:y2, x1:x2]
            
            # Resize to target size
            if face_crop.size > 0:
                aligned = cv2.resize(face_crop, self.target_size, 
                                   interpolation=cv2.INTER_CUBIC)
                return aligned
            else:
                logger.warning("Empty face crop, returning original")
                return image
                
        except Exception as e:
            logger.error(f"Error in simple alignment: {e}")
            return image
