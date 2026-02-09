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
    """Utility class for checking face image quality with environment adaptation."""
    
    # Base quality thresholds - Further reduced for better success rates
    MIN_BLUR_THRESHOLD = 2.5  # Further reduced from 3.0
    MIN_BRIGHTNESS = 15  # Further reduced from 20
    MAX_BRIGHTNESS = 250  # Further increased from 245
    MIN_FACE_SIZE = (40, 40)  # Further reduced from (48, 48)
    MAX_FACE_SIZE = (1200, 1200)  # Further increased from (1000, 1000)
    
    # Environment-adaptive thresholds
    INDOOR_BLUR_MIN = 1.5  # Very lenient for indoor/artificial lighting
    OUTDOOR_BLUR_MIN = 2.0  # Slightly less lenient for outdoor/natural lighting
    LOW_LIGHT_THRESHOLD = (10, 255)  # Very wide range for low light
    HIGH_CONTRAST_THRESHOLD = (5, 255)  # Maximum range for high contrast scenes
    
    @staticmethod
    def detect_environment(image) -> str:
        """Detect image environment characteristics for adaptive processing."""
        if not HAS_CV2:
            return "unknown"
        
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Analyze image characteristics
            avg_brightness = np.mean(gray)
            brightness_std = np.std(gray)
            
            # Environment classification
            if avg_brightness < 40:
                return "low_light"
            elif avg_brightness > 180 and brightness_std < 30:
                return "bright_uniform"  # Possibly overexposed
            elif brightness_std > 60:
                return "high_contrast"  # Mixed lighting
            elif 40 <= avg_brightness <= 180:
                return "normal"
            else:
                return "challenging"
                
        except Exception as e:
            logger.error(f"Error detecting environment: {e}")
            return "unknown"
    
    @staticmethod
    def check_blur(image, threshold: float = None, adaptive: bool = True) -> Tuple[bool, float, str]:
        """Check if image is blurry with environment-aware adaptive thresholds.
        
        Args:
            image: Input image in OpenCV format
            threshold: Blur threshold (if None, uses environment-adaptive thresholds)
            adaptive: Whether to use environment-adaptive thresholds
            
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
            
            # Multiple blur detection methods
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            blur_score = laplacian.var()
            
            # Sobel gradient method for validation
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_score = np.mean(np.sqrt(sobelx**2 + sobely**2))
            
            # Environment-aware threshold selection
            if adaptive and threshold is None:
                environment = FaceQualityChecker.detect_environment(image)
                
                if environment == "low_light":
                    threshold = FaceQualityChecker.INDOOR_BLUR_MIN
                elif environment == "bright_uniform":
                    threshold = FaceQualityChecker.INDOOR_BLUR_MIN  # Overexposed images often appear soft
                elif environment == "high_contrast":
                    threshold = FaceQualityChecker.OUTDOOR_BLUR_MIN
                else:
                    threshold = FaceQualityChecker.MIN_BLUR_THRESHOLD
            elif threshold is None:
                threshold = FaceQualityChecker.MIN_BLUR_THRESHOLD
            
            # Multi-method assessment - accept if either passes
            is_sharp_laplacian = blur_score >= threshold
            is_sharp_gradient = gradient_score >= (threshold * 1.5)  # Lower threshold for gradient
            
            # Very lenient acceptance - pass if either method suggests sharpness
            is_sharp = is_sharp_laplacian or is_sharp_gradient
            
            # If still fails, try with even lower threshold
            if not is_sharp and adaptive:
                emergency_threshold = threshold * 0.5  # 50% lower emergency threshold
                is_sharp = blur_score >= emergency_threshold or gradient_score >= emergency_threshold
                
                if is_sharp:
                    message = f"Image acceptable with emergency threshold (blur: {blur_score:.1f})"
                else:
                    message = f"Image quality poor (blur: {blur_score:.1f}, gradient: {gradient_score:.1f})"
            else:
                message = f"Image quality {'good' if is_sharp else 'fair'} (blur: {blur_score:.1f}, gradient: {gradient_score:.1f})"
            
            return is_sharp, blur_score, message
            
        except Exception as e:
            logger.error(f"Error checking blur: {e}")
            return True, 0.0, "Blur check failed - accepting image"
    
    @staticmethod
    def check_brightness(image, min_brightness: int = None, 
                        max_brightness: int = None, adaptive: bool = True) -> Tuple[bool, float, str]:
        """Check brightness with environment-aware adaptive thresholds.
        
        Args:
            image: Input image in OpenCV format
            min_brightness: Minimum acceptable average brightness
            max_brightness: Maximum acceptable average brightness
            adaptive: Whether to use environment-adaptive thresholds
            
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
            
            # Multiple brightness metrics
            avg_brightness = np.mean(gray)
            median_brightness = np.median(gray)
            std_brightness = np.std(gray)
            
            # Environment-aware threshold adaptation
            if adaptive:
                environment = FaceQualityChecker.detect_environment(image)
                
                if environment == "low_light":
                    min_thresh, max_thresh = FaceQualityChecker.LOW_LIGHT_THRESHOLD
                elif environment == "bright_uniform":
                    min_thresh, max_thresh = (10, 255)  # Accept almost anything for overexposed
                elif environment == "high_contrast":
                    min_thresh, max_thresh = FaceQualityChecker.HIGH_CONTRAST_THRESHOLD
                else:
                    min_thresh = min_brightness or FaceQualityChecker.MIN_BRIGHTNESS
                    max_thresh = max_brightness or FaceQualityChecker.MAX_BRIGHTNESS
            else:
                min_thresh = min_brightness or FaceQualityChecker.MIN_BRIGHTNESS
                max_thresh = max_brightness or FaceQualityChecker.MAX_BRIGHTNESS
            
            # Use median for robustness, fallback to average
            primary_brightness = median_brightness if std_brightness > 40 else avg_brightness
            
            is_good = min_thresh <= primary_brightness <= max_thresh
            
            # Emergency acceptance for challenging conditions
            if not is_good and adaptive:
                # Very generous emergency range
                emergency_range = (5, 255)
                is_good = emergency_range[0] <= primary_brightness <= emergency_range[1]
                
                # Accept if there's any reasonable contrast
                if not is_good and std_brightness > 20:
                    is_good = True
                    message = f"Accepted due to good contrast (brightness: {primary_brightness:.1f}, contrast: {std_brightness:.1f})"
                elif is_good:
                    message = f"Accepted with emergency thresholds (brightness: {primary_brightness:.1f})"
                else:
                    message = f"Brightness too extreme (brightness: {primary_brightness:.1f})"
            else:
                if primary_brightness < min_thresh:
                    message = f"Image is dark (brightness: {primary_brightness:.1f}, min: {min_thresh})"
                elif primary_brightness > max_thresh:
                    message = f"Image is bright (brightness: {primary_brightness:.1f}, max: {max_thresh})"
                else:
                    message = f"Brightness is good (brightness: {primary_brightness:.1f})"
            
            return is_good, primary_brightness, message
            
        except Exception as e:
            logger.error(f"Error checking brightness: {e}")
            return True, 0.0, "Brightness check failed - accepting image"
    
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
    def check_all(image, face_location: Optional[Tuple[int, int, int, int]] = None, adaptive: bool = True) -> Dict:
        """Perform all quality checks on image with adaptive thresholds.
        
        Args:
            image: Input image in OpenCV format
            face_location: Optional face bounding box
            adaptive: Whether to use adaptive thresholds
            
        Returns:
            Dictionary with all check results
        """
        results = {
            'overall_pass': True,
            'checks': {},
            'messages': [],
            'adaptive_used': adaptive
        }
        
        # Check blur with adaptive thresholds
        is_sharp, blur_score, blur_msg = FaceQualityChecker.check_blur(image, adaptive=adaptive)
        results['checks']['blur'] = {'pass': is_sharp, 'score': blur_score}
        if not is_sharp:
            results['overall_pass'] = False
            results['messages'].append(blur_msg)
        
        # Check brightness with adaptive thresholds
        is_bright, brightness, bright_msg = FaceQualityChecker.check_brightness(image, adaptive=adaptive)
        results['checks']['brightness'] = {'pass': is_bright, 'value': brightness}
        if not is_bright:
            results['overall_pass'] = False
            results['messages'].append(bright_msg)
        
        # Check face size if location provided (more lenient)
        if face_location:
            is_size_ok, size, size_msg = FaceQualityChecker.check_face_size(face_location)
            results['checks']['face_size'] = {'pass': is_size_ok, 'size': size}
            if not is_size_ok:
                results['overall_pass'] = False
                results['messages'].append(size_msg)
        
        # Enhanced overall assessment - be more forgiving if most checks pass
        passed_checks = sum(1 for check in results['checks'].values() if check['pass'])
        total_checks = len(results['checks'])
        
        # If at least 2/3 checks pass, consider it acceptable for registration
        if passed_checks >= (total_checks * 0.67) and not results['overall_pass']:
            results['overall_pass'] = True
            results['messages'] = [f"Image acceptable despite minor quality issues ({passed_checks}/{total_checks} checks passed)"]
        
        return results
    
    @staticmethod
    def enhance_image(image):
        """Enhance image quality for better face recognition.
        
        Args:
            image: Input image in OpenCV format
            
        Returns:
            Enhanced image
        """
        if not HAS_CV2:
            return image
            
        try:
            enhanced = image.copy()
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            if len(enhanced.shape) == 3:
                # Convert to LAB color space
                lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                l = clahe.apply(l)
                
                # Merge and convert back
                enhanced = cv2.merge([l, a, b])
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            else:
                # Apply CLAHE to grayscale
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(enhanced)
            
            # Apply slight Gaussian blur to reduce noise
            enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0.5)
            
            # Gamma correction for better exposure
            gamma = 1.2
            enhanced = np.power(enhanced / 255.0, 1.0 / gamma)
            enhanced = (enhanced * 255).astype(np.uint8)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image


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


class DataAugmentation:
    """Data augmentation utilities for face images."""
    
    @staticmethod
    def rotate_image(image, angle: float):
        """Rotate image by given angle."""
        if not HAS_CV2:
            return image
        
        try:
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, rotation_matrix, (width, height))
            return rotated
        except Exception as e:
            logger.error(f"Error rotating image: {e}")
            return image
    
    @staticmethod
    def adjust_brightness(image, factor: float):
        """Adjust image brightness."""
        if not HAS_CV2:
            return image
        
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        except Exception as e:
            logger.error(f"Error adjusting brightness: {e}")
            return image
    
    @staticmethod
    def add_noise(image, intensity: float = 0.05):
        """Add random noise to image."""
        if not HAS_NUMPY:
            return image
        
        try:
            noise = np.random.normal(0, intensity * 255, image.shape).astype(np.uint8)
            noisy_image = cv2.add(image, noise)
            return noisy_image
        except Exception as e:
            logger.error(f"Error adding noise: {e}")
            return image
    
    @staticmethod
    def generate_augmentations(image, num_augmentations: int = 3):
        """Generate augmented versions of the image."""
        augmentations = []
        
        for i in range(num_augmentations):
            augmented = image.copy()
            
            # Apply random rotation (-10 to 10 degrees)
            angle = np.random.uniform(-10, 10)
            augmented = DataAugmentation.rotate_image(augmented, angle)
            
            # Apply random brightness adjustment (0.8 to 1.2)
            brightness_factor = np.random.uniform(0.8, 1.2)
            augmented = DataAugmentation.adjust_brightness(augmented, brightness_factor)
            
            # Optionally add noise
            if np.random.random() > 0.5:
                augmented = DataAugmentation.add_noise(augmented, 0.02)
            
            augmentations.append(augmented)
        
        return augmentations
