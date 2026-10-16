"""Liveness detection implementations."""
import logging
from typing import List, Tuple, Optional

from .base import LivenessDetector


logger = logging.getLogger(__name__)

# Conditional imports
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    cv2 = None
    HAS_OPENCV = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    # Must always be bound: the annotations below are evaluated when this
    # module is imported, and a missing name here is a hard ImportError.
    np = None
    HAS_NUMPY = False

try:
    import dlib
    HAS_DLIB = True
except ImportError:
    dlib = None
    HAS_DLIB = False


class BlinkLivenessDetector(LivenessDetector):
    """Blink detection based liveness checker using Eye Aspect Ratio (EAR)."""
    
    # Eye landmarks indices for dlib 68-point model
    LEFT_EYE_INDICES = list(range(36, 42))
    RIGHT_EYE_INDICES = list(range(42, 48))
    
    # EAR threshold and consecutive frames
    EAR_THRESHOLD = 0.21
    CONSECUTIVE_FRAMES = 2
    MIN_BLINKS = 1
    
    def __init__(self, ear_threshold: float = 0.21, consecutive_frames: int = 2, min_blinks: int = 1):
        """Initialize liveness detector.
        
        Args:
            ear_threshold: Eye Aspect Ratio threshold for blink detection
            consecutive_frames: Number of consecutive frames below threshold to count as blink
            min_blinks: Minimum number of blinks required for liveness
        """
        self.ear_threshold = ear_threshold
        self.consecutive_frames = consecutive_frames
        self.min_blinks = min_blinks
        self._predictor = None
        self._detector = None
        
        if HAS_DLIB:
            try:
                # Try to load dlib's facial landmark predictor
                import os
                predictor_path = os.path.join(os.path.dirname(__file__), 
                                             '../../../../models/shape_predictor_68_face_landmarks.dat')
                if os.path.exists(predictor_path):
                    self._predictor = dlib.shape_predictor(predictor_path)
                    self._detector = dlib.get_frontal_face_detector()
                    logger.info("Dlib facial landmark predictor loaded successfully")
                else:
                    logger.warning(f"Facial landmark predictor not found at {predictor_path}")
            except Exception as e:
                logger.warning(f"Could not initialize dlib predictor: {e}")
    
    def _calculate_ear(self, eye_points) -> float:
        """Calculate Eye Aspect Ratio (EAR).
        
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        
        Args:
            eye_points: Array of 6 (x, y) coordinates for eye landmarks
            
        Returns:
            Eye aspect ratio
        """
        # Compute euclidean distances between vertical eye landmarks
        vertical1 = np.linalg.norm(eye_points[1] - eye_points[5])
        vertical2 = np.linalg.norm(eye_points[2] - eye_points[4])
        
        # Compute euclidean distance between horizontal eye landmarks
        horizontal = np.linalg.norm(eye_points[0] - eye_points[3])
        
        # Calculate EAR
        ear = (vertical1 + vertical2) / (2.0 * horizontal)
        return ear
    
    def _extract_eye_landmarks(self, frame, shape) -> Tuple[Optional[object], Optional[object]]:
        """Extract left and right eye landmarks from dlib shape.
        
        Args:
            frame: Input frame
            shape: Dlib facial landmarks shape
            
        Returns:
            Tuple of (left_eye_points, right_eye_points)
        """
        if not HAS_OPENCV:
            return None, None
            
        left_eye = np.array([(shape.part(i).x, shape.part(i).y) for i in self.LEFT_EYE_INDICES])
        right_eye = np.array([(shape.part(i).x, shape.part(i).y) for i in self.RIGHT_EYE_INDICES])
        
        return left_eye, right_eye
    
    def _detect_blinks_in_frames(self, frames: List) -> int:
        """Detect number of blinks in frame sequence.
        
        Args:
            frames: List of frames to analyze
            
        Returns:
            Number of blinks detected
        """
        if not HAS_OPENCV or not HAS_DLIB or not self._predictor or not self._detector:
            logger.warning("Liveness detection dependencies not available, skipping blink detection")
            return self.min_blinks  # Assume valid if can't check
        
        blink_count = 0
        consecutive_below_threshold = 0
        
        for frame in frames:
            try:
                # Convert to grayscale
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame
                
                # Detect faces
                faces = self._detector(gray, 0)
                
                if len(faces) == 0:
                    continue
                
                # Use first detected face
                face = faces[0]
                
                # Get facial landmarks
                shape = self._predictor(gray, face)
                
                # Extract eye landmarks
                left_eye, right_eye = self._extract_eye_landmarks(frame, shape)
                
                if left_eye is None or right_eye is None:
                    continue
                
                # Calculate EAR for both eyes
                left_ear = self._calculate_ear(left_eye)
                right_ear = self._calculate_ear(right_eye)
                ear = (left_ear + right_ear) / 2.0
                
                # Check if EAR is below threshold
                if ear < self.ear_threshold:
                    consecutive_below_threshold += 1
                else:
                    # If eyes were closed and now open, count as blink
                    if consecutive_below_threshold >= self.consecutive_frames:
                        blink_count += 1
                        logger.debug(f"Blink detected (EAR: {ear:.3f})")
                    consecutive_below_threshold = 0
                    
            except Exception as e:
                logger.error(f"Error processing frame for liveness: {e}")
                continue
        
        return blink_count
    
    def check_liveness(self, frames) -> bool:
        """Check liveness via blink detection.
        
        Args:
            frames: List of frames or single frame to analyze
            
        Returns:
            True if liveness detected, False otherwise
        """
        # Handle single frame
        if not isinstance(frames, list):
            frames = [frames]
        
        # Need minimum frames for blink detection
        if len(frames) < 3:
            logger.warning(f"Insufficient frames for liveness detection ({len(frames)} < 3)")
            return True  # Assume live if not enough frames
        
        # Detect blinks
        blink_count = self._detect_blinks_in_frames(frames)
        
        is_live = blink_count >= self.min_blinks
        logger.info(f"Liveness check: {blink_count} blinks detected, required: {self.min_blinks}, result: {is_live}")
        
        return is_live


class MotionLivenessDetector(LivenessDetector):
    """Motion-based liveness detection using frame differences."""
    
    def __init__(self, motion_threshold: float = 0.02, min_motion_frames: int = 2):
        """Initialize motion detector.
        
        Args:
            motion_threshold: Minimum motion ratio to consider as movement
            min_motion_frames: Minimum frames with motion required
        """
        self.motion_threshold = motion_threshold
        self.min_motion_frames = min_motion_frames
    
    def check_liveness(self, frames) -> bool:
        """Check liveness via motion detection.
        
        Args:
            frames: List of frames to analyze
            
        Returns:
            True if motion detected, False otherwise
        """
        if not HAS_OPENCV:
            logger.warning("OpenCV not available, skipping motion detection")
            return True
        
        if not isinstance(frames, list) or len(frames) < 2:
            logger.warning(f"Insufficient frames for motion detection")
            return True
        
        motion_count = 0
        
        for i in range(1, len(frames)):
            try:
                # Convert to grayscale
                prev_frame = frames[i-1]
                curr_frame = frames[i]
                
                if len(prev_frame.shape) == 3:
                    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                else:
                    prev_gray = prev_frame
                    
                if len(curr_frame.shape) == 3:
                    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
                else:
                    curr_gray = curr_frame
                
                # Calculate frame difference
                frame_diff = cv2.absdiff(prev_gray, curr_gray)
                
                # Calculate motion ratio
                motion_pixels = np.sum(frame_diff > 30)
                total_pixels = frame_diff.size
                motion_ratio = motion_pixels / total_pixels
                
                if motion_ratio > self.motion_threshold:
                    motion_count += 1
                    
            except Exception as e:
                logger.error(f"Error calculating motion: {e}")
                continue
        
        is_live = motion_count >= self.min_motion_frames
        logger.info(f"Motion detection: {motion_count} motion frames, required: {self.min_motion_frames}, result: {is_live}")
        
        return is_live
