"""Advanced image preprocessing pipeline for facial recognition."""
import logging
from typing import Tuple, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class PreprocessingStage(Enum):
    """Preprocessing stages in optimal order."""
    DENOISE = "denoise"
    NORMALIZE_LIGHTING = "normalize_lighting"
    ENHANCE_CONTRAST = "enhance_contrast"
    SHARPEN = "sharpen"


class ImagePreprocessor:
    """Production-grade image preprocessing for facial recognition.
    
    Applies preprocessing techniques intelligently based on image characteristics
    to optimize face detection and recognition accuracy while maintaining speed.
    """
    
    def __init__(self, enable_adaptive_preprocessing: bool = True):
        """Initialize preprocessor.
        
        Args:
            enable_adaptive_preprocessing: Whether to adapt preprocessing based on image analysis
        """
        self.enable_adaptive_preprocessing = enable_adaptive_preprocessing
        self.preprocessing_profile = None
    
    def _analyze_image_characteristics(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze image characteristics to determine preprocessing strategy.
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Dict with analysis results
        """
        if not HAS_OPENCV:
            return {'noise_level': 'unknown', 'lighting': 'unknown', 'contrast': 'unknown'}
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Noise estimation using Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            noise_level = laplacian.var()
            
            # Lighting analysis
            brightness = np.mean(gray)
            brightness_std = np.std(gray)
            
            # Contrast analysis
            histogram = cv2.calcHist([gray], [0], None, [256], [0, 256])
            contrast = np.std(histogram)
            
            return {
                'noise_level': 'high' if noise_level < 100 else 'normal' if noise_level < 500 else 'low',
                'brightness': brightness,
                'brightness_std': brightness_std,
                'contrast': contrast,
                'requires_denoise': noise_level < 100,
                'requires_brightening': brightness < 60,
                'requires_darkening': brightness > 200,
                'requires_contrast_enhancement': contrast < 50,
                'lighting_condition': self._classify_lighting(brightness, brightness_std)
            }
        except Exception as e:
            logger.warning(f"Image analysis failed: {e}")
            return {}
    
    def _classify_lighting(self, brightness: float, brightness_std: float) -> str:
        """Classify lighting conditions."""
        if brightness < 50:
            return 'very_dark'
        elif brightness < 100:
            return 'dark'
        elif brightness > 200:
            return 'bright'
        elif brightness_std > 80:
            return 'high_variance'
        else:
            return 'normal'
    
    def _denoise(self, image: np.ndarray, strength: int = 9) -> np.ndarray:
        """Apply denoising using bilateral filtering.
        
        Preserves edges while reducing noise - optimal for face detection.
        """
        if not HAS_OPENCV:
            return image
        
        try:
            # Bilateral filter: preserves edges, reduces noise
            return cv2.bilateralFilter(image, strength, 75, 75)
        except Exception as e:
            logger.warning(f"Denoising failed: {e}")
            return image
    
    def _normalize_lighting(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Normalizes lighting conditions across the image for better face detection
        under varying lighting conditions.
        """
        if not HAS_OPENCV:
            return image
        
        try:
            if len(image.shape) == 3:
                # Convert to LAB color space
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                # Apply CLAHE only to L (lightness) channel
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                
                # Merge channels back
                lab = cv2.merge([l, a, b])
                return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            else:
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                return clahe.apply(image)
        except Exception as e:
            logger.warning(f"Lighting normalization failed: {e}")
            return image
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using unsharp masking.
        
        Improves facial features visibility for better detection accuracy.
        """
        if not HAS_OPENCV:
            return image
        
        try:
            # Gaussian blur for unsharp masking
            gaussian = cv2.GaussianBlur(image, (0, 0), 1.0)
            # Unsharp mask: enhance edges and details
            enhanced = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
            # Clip values to valid range
            return np.clip(enhanced, 0, 255).astype(np.uint8)
        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {e}")
            return image
    
    def _adjust_gamma(self, image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """Apply gamma correction for brightness adjustment.
        
        Gamma < 1.0: Brightens image
        Gamma > 1.0: Darkens image
        """
        if gamma == 1.0 or not HAS_OPENCV:
            return image
        
        try:
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(np.uint8)
            return cv2.LUT(image, table)
        except Exception as e:
            logger.warning(f"Gamma correction failed: {e}")
            return image
    
    def sharpen(self, image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """Apply sharpening filter to enhance facial features.
        
        Args:
            image: Input image
            kernel_size: Size of sharpening kernel
            
        Returns:
            Sharpened image
        """
        if not HAS_OPENCV:
            return image
        
        try:
            # Unsharp masking for edge enhancement
            gaussian = cv2.GaussianBlur(image, (0, 0), 1.0)
            sharpened = cv2.addWeighted(image, 2.0, gaussian, -1.0, 0)
            return np.clip(sharpened, 0, 255).astype(np.uint8)
        except Exception as e:
            logger.warning(f"Sharpening failed: {e}")
            return image
    
    def preprocess(self, image: np.ndarray, aggressive: bool = False) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Apply intelligent preprocessing pipeline.
        
        Args:
            image: Input image (BGR format)
            aggressive: If True, apply all preprocessing steps; if False, apply only necessary ones
            
        Returns:
            Tuple of (preprocessed_image, metadata)
        """
        if not HAS_OPENCV:
            return image, {'skipped': True, 'reason': 'OpenCV not available'}
        
        try:
            metadata = {}
            processed = image.copy()
            
            # Analyze image characteristics
            if self.enable_adaptive_preprocessing:
                characteristics = self._analyze_image_characteristics(image)
                metadata['analysis'] = characteristics
            else:
                characteristics = {}
            
            # Stage 1: Denoising
            if aggressive or characteristics.get('requires_denoise', False):
                processed = self._denoise(processed)
                metadata['denoise_applied'] = True
            
            # Stage 2: Lighting normalization
            if aggressive or characteristics.get('brightness_std', 50) > 40:
                processed = self._normalize_lighting(processed)
                metadata['lighting_normalization_applied'] = True
            
            # Gamma correction based on brightness
            if characteristics.get('requires_brightening', False):
                processed = self._adjust_gamma(processed, gamma=1.3)
                metadata['gamma_correction'] = 'brightened (1.3)'
            elif characteristics.get('requires_darkening', False):
                processed = self._adjust_gamma(processed, gamma=0.7)
                metadata['gamma_correction'] = 'darkened (0.7)'
            
            # Stage 3: Contrast enhancement
            if aggressive or characteristics.get('requires_contrast_enhancement', False):
                processed = self._enhance_contrast(processed)
                metadata['contrast_enhancement_applied'] = True
            
            # Stage 4: Sharpening
            if aggressive:
                processed = self.sharpen(processed)
                metadata['sharpening_applied'] = True
            
            metadata['preprocessing_successful'] = True
            return processed, metadata
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return image, {'error': str(e), 'preprocessing_successful': False}
