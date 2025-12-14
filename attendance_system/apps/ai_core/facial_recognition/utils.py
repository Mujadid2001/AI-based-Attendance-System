"""Utility functions for image processing."""
import logging
from io import BytesIO
from typing import Tuple, Optional, Dict

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

try:
    from PIL import Image
except ImportError:
    Image = None

logger = logging.getLogger(__name__)


class FaceQualityChecker:
    """Utility class for checking face image quality."""
    
    # Quality thresholds
    MIN_BLUR_THRESHOLD = 100.0  # Laplacian variance threshold
    MIN_BRIGHTNESS = 40  # Minimum average brightness
    MAX_BRIGHTNESS = 220  # Maximum average brightness
    MIN_FACE_SIZE = (80, 80)  # Minimum face dimensions
    MAX_FACE_SIZE = (800, 800)  # Maximum face dimensions
    
    @staticmethod
    def check_blur(image, threshold: float = MIN_BLUR_THRESHOLD) -> Tuple[bool, float, str]:
        """Check if image is blurry using Laplacian variance.
        
        Args:
            image: Input image in OpenCV format
            threshold: Blur threshold (higher = sharper)
            
        Returns:
            Tuple of (is_sharp, blur_score, message)
        """
        if not HAS_CV2:
            return True, 0.0, "OpenCV not available, skipping blur check"
        
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            blur_score = laplacian.var()
            
            is_sharp = blur_score >= threshold
            message = "Image is sharp" if is_sharp else f"Image is too blurry (score: {blur_score:.1f}, required: {threshold})"
            
            logger.debug(f"Blur check: score={blur_score:.1f}, threshold={threshold}, sharp={is_sharp}")
            return is_sharp, blur_score, message
            
        except Exception as e:
            logger.error(f"Error checking blur: {e}")
            return True, 0.0, f"Error checking blur: {e}"
    
    @staticmethod
    def check_brightness(image, min_brightness: int = MIN_BRIGHTNESS, 
                        max_brightness: int = MAX_BRIGHTNESS) -> Tuple[bool, float, str]:
        """Check if image has adequate brightness/illumination.
        
        Args:
            image: Input image in OpenCV format
            min_brightness: Minimum acceptable average brightness
            max_brightness: Maximum acceptable average brightness
            
        Returns:
            Tuple of (is_good, brightness, message)
        """
        if not HAS_CV2:
            return True, 0.0, "OpenCV not available, skipping brightness check"
        
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate average brightness
            brightness = np.mean(gray)
            
            is_good = min_brightness <= brightness <= max_brightness
            
            if brightness < min_brightness:
                message = f"Image is too dark (brightness: {brightness:.1f}, min: {min_brightness})"
            elif brightness > max_brightness:
                message = f"Image is too bright (brightness: {brightness:.1f}, max: {max_brightness})"
            else:
                message = "Brightness is adequate"
            
            logger.debug(f"Brightness check: value={brightness:.1f}, range=[{min_brightness}, {max_brightness}], good={is_good}")
            return is_good, brightness, message
            
        except Exception as e:
            logger.error(f"Error checking brightness: {e}")
            return True, 0.0, f"Error checking brightness: {e}"
    
    @staticmethod
    def check_face_size(face_location: Tuple[int, int, int, int], 
                       min_size: Tuple[int, int] = MIN_FACE_SIZE,
                       max_size: Tuple[int, int] = MAX_FACE_SIZE) -> Tuple[bool, Tuple[int, int], str]:
        """Check if detected face has acceptable size.
        
        Args:
            face_location: Face bounding box (top, right, bottom, left)
            min_size: Minimum (width, height) in pixels
            max_size: Maximum (width, height) in pixels
            
        Returns:
            Tuple of (is_good, (width, height), message)
        """
        try:
            top, right, bottom, left = face_location
            width = right - left
            height = bottom - top
            
            is_good = (min_size[0] <= width <= max_size[0] and 
                      min_size[1] <= height <= max_size[1])
            
            if width < min_size[0] or height < min_size[1]:
                message = f"Face is too small ({width}x{height}, min: {min_size[0]}x{min_size[1]})"
            elif width > max_size[0] or height > max_size[1]:
                message = f"Face is too large ({width}x{height}, max: {max_size[0]}x{max_size[1]})"
            else:
                message = f"Face size is acceptable ({width}x{height})"
            
            logger.debug(f"Face size check: {width}x{height}, min={min_size}, max={max_size}, good={is_good}")
            return is_good, (width, height), message
            
        except Exception as e:
            logger.error(f"Error checking face size: {e}")
            return True, (0, 0), f"Error checking face size: {e}"
    
    @staticmethod
    def check_all(image, face_location: Optional[Tuple[int, int, int, int]] = None) -> Dict:
        """Perform all quality checks on image.
        
        Args:
            image: Input image in OpenCV format
            face_location: Optional face bounding box
            
        Returns:
            Dictionary with all check results
        """
        results = {
            'overall_pass': True,
            'checks': {},
            'messages': []
        }
        
        # Check blur
        is_sharp, blur_score, blur_msg = FaceQualityChecker.check_blur(image)
        results['checks']['blur'] = {'pass': is_sharp, 'score': blur_score}
        if not is_sharp:
            results['overall_pass'] = False
            results['messages'].append(blur_msg)
        
        # Check brightness
        is_bright, brightness, bright_msg = FaceQualityChecker.check_brightness(image)
        results['checks']['brightness'] = {'pass': is_bright, 'value': brightness}
        if not is_bright:
            results['overall_pass'] = False
            results['messages'].append(bright_msg)
        
        # Check face size if location provided
        if face_location:
            is_size_ok, size, size_msg = FaceQualityChecker.check_face_size(face_location)
            results['checks']['face_size'] = {'pass': is_size_ok, 'size': size}
            if not is_size_ok:
                results['overall_pass'] = False
                results['messages'].append(size_msg)
        
        return results


class ImageProcessor:
    """Utility class for image processing."""
    
    @staticmethod
    def convert_pil_to_cv2(pil_image):
        """Convert PIL image to OpenCV format."""
        if not HAS_CV2 or Image is None:
            return None
        
        import numpy as np
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def convert_cv2_to_pil(cv2_image):
        """Convert OpenCV image to PIL format."""
        if not HAS_CV2 or Image is None:
            return None
        
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

    @staticmethod
    def convert_image_bytes_to_cv2(image_bytes):
        """Convert image bytes to cv2 image."""
        if not HAS_CV2 or not HAS_NUMPY:
            return None

        image_stream = BytesIO(image_bytes)
        image_array = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
