# Integration Guide - Enhanced Facial Recognition

This guide shows how to integrate the new facial recognition features into your existing codebase.

## Backward Compatibility

**Good news**: All existing code continues to work without any changes! The enhancements are fully backward compatible.

## Gradual Migration Path

### Phase 1: Enable Quality Checks (Recommended First Step)

Update your face registration to use quality validation:

```python
# In your face registration view/service
from apps.ai_core.facial_recognition import FacialRecognitionPipeline

# Enable quality checks during initialization
pipeline = FacialRecognitionPipeline(
    confidence_threshold=0.6,
    enable_quality_checks=True  # Add this
)

# Quality checks now run automatically during registration
success, encoding, message = pipeline.register_face(image, student_id)

if not success:
    # Message will contain specific quality issues
    return {"error": message}  # e.g., "Image is too blurry"
```

### Phase 2: Add Liveness Detection (High Priority for Security)

Integrate liveness detection to prevent spoofing:

```python
# In FaceRecognitionViewSet or recognition service
from apps.ai_core.facial_recognition import FacialRecognitionPipeline

def recognize_with_liveness(self, request):
    # Expect multiple frames from frontend
    frames_data = request.data.get('frames', [])
    
    if len(frames_data) < 3:
        return Response({
            'success': False,
            'error': 'Insufficient frames for liveness detection'
        })
    
    # Convert frames to images
    frames = []
    for frame_data in frames_data:
        image = decode_image(frame_data)  # Your image decoding function
        frames.append(image)
    
    # Check liveness first
    is_live = self.pipeline.check_liveness(frames)
    
    if not is_live:
        return Response({
            'success': False,
            'error': 'Liveness check failed. Please ensure you are live.'
        })
    
    # Proceed with recognition on the last frame
    result = self.pipeline.recognize_face(frames[-1])
    return Response(result)
```

**Frontend changes needed**:
```javascript
// Capture multiple frames (3-5) over 1-2 seconds
const frames = [];
const captureFrames = async () => {
    for (let i = 0; i < 5; i++) {
        const frame = await captureFrame(); // Your camera capture
        frames.push(frame);
        await sleep(300); // 300ms between frames
    }
    return frames;
};
```

### Phase 3: Upgrade to Better Detector (For Improved Accuracy)

Switch from Haar Cascade to DNN detector:

```python
# In AIServiceManager or your initialization code
from apps.ai_core.facial_recognition import (
    FacialRecognitionPipeline,
    DNNFaceDetector
)

class AIServiceManager:
    def _initialize_pipeline(self):
        # Use DNN detector for better accuracy
        detector = DNNFaceDetector(confidence_threshold=0.5)
        
        self._pipeline = FacialRecognitionPipeline(
            face_detector=detector,
            confidence_threshold=0.6,
            enable_quality_checks=True
        )
```

**Note**: Requires model files. See README.md for download links.

### Phase 4: Enable Encryption (For Security Compliance)

Protect stored face encodings with encryption:

```python
# In settings/app_settings.py
AI_SETTINGS = {
    # ... existing settings ...
    'ENABLE_ENCRYPTION': True,
    'ENCRYPTION_KEY': os.environ.get('FACE_ENCODING_KEY'),  # Store in env var!
}

# In AIServiceManager
from apps.ai_core.facial_recognition.storage import TrainingDataStorage
import base64

class AIServiceManager:
    def _initialize_storage(self):
        encryption_key = None
        
        if settings.AI_SETTINGS.get('ENABLE_ENCRYPTION'):
            key_str = settings.AI_SETTINGS.get('ENCRYPTION_KEY')
            
            if key_str:
                encryption_key = base64.b64decode(key_str)
            else:
                # Generate new key (only do this once!)
                from cryptography.fernet import Fernet
                encryption_key = Fernet.generate_key()
                logger.warning(f"Generated encryption key: {base64.b64encode(encryption_key).decode()}")
                logger.warning("Store this key in FACE_ENCODING_KEY environment variable!")
        
        self._storage = TrainingDataStorage(
            encryption_key=encryption_key,
            enable_encryption=settings.AI_SETTINGS.get('ENABLE_ENCRYPTION', False)
        )
        
        return self._storage
```

**Environment setup**:
```bash
# Add to .env file
FACE_ENCODING_KEY=your_base64_encoded_key_here
```

### Phase 5: Add Face Alignment (Optional, For Accuracy)

Use face alignment for better recognition:

```python
# In your registration service
from apps.ai_core.facial_recognition.alignment import SimpleFaceAligner

class FaceRegistrationService:
    def __init__(self):
        self.aligner = SimpleFaceAligner(target_size=(160, 160))
        self.pipeline = FacialRecognitionPipeline(...)
    
    def register_face(self, image, student_id):
        # Detect face first
        face_location = self.detect_face(image)
        
        if face_location:
            # Align face before registration
            aligned_face = self.aligner.align_face(image, face_location)
            success, encoding, message = self.pipeline.register_face(
                aligned_face, 
                student_id
            )
        else:
            return False, None, "No face detected"
```

## Complete Integration Example

Here's a complete example integrating all features:

```python
# services.py
from django.conf import settings
from apps.ai_core.facial_recognition import (
    FacialRecognitionPipeline,
    DNNFaceDetector,
    TrainingDataStorage,
)
from apps.ai_core.facial_recognition.alignment import SimpleFaceAligner
import logging

logger = logging.getLogger(__name__)


class EnhancedAIServiceManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._pipeline = None
        self._aligner = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all AI components."""
        try:
            # Initialize storage with optional encryption
            storage = self._create_storage()
            
            # Initialize detector (DNN for better accuracy)
            detector = DNNFaceDetector(confidence_threshold=0.5)
            
            # Initialize pipeline
            self._pipeline = FacialRecognitionPipeline(
                face_detector=detector,
                storage=storage,
                confidence_threshold=0.6,
                enable_quality_checks=True
            )
            
            # Initialize face aligner
            self._aligner = SimpleFaceAligner(target_size=(160, 160))
            
            # Load existing training data
            self._load_training_data()
            
            logger.info("Enhanced AI components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI components: {e}")
            raise
    
    def _create_storage(self):
        """Create storage with optional encryption."""
        enable_encryption = settings.AI_SETTINGS.get('ENABLE_ENCRYPTION', False)
        encryption_key = None
        
        if enable_encryption:
            import base64
            key_str = settings.AI_SETTINGS.get('ENCRYPTION_KEY')
            if key_str:
                encryption_key = base64.b64decode(key_str)
        
        return TrainingDataStorage(
            encryption_key=encryption_key,
            enable_encryption=enable_encryption
        )
    
    def _load_training_data(self):
        """Load training data from file."""
        models_dir = settings.AI_SETTINGS.get('MODELS_DIR', 'models/')
        training_file = os.path.join(models_dir, 'face_encodings.pkl')
        
        if os.path.exists(training_file):
            self._pipeline.load_training_data(training_file)
    
    def register_face(self, image, student_id, align=True):
        """Register face with optional alignment."""
        try:
            if align:
                # Align face first
                aligned = self._aligner.align_face(image, None)
                image = aligned if aligned is not None else image
            
            success, encoding, message = self._pipeline.register_face(
                image, 
                student_id,
                check_quality=True
            )
            
            if success:
                # Save training data
                self.save_training_data()
            
            return success, encoding, message
            
        except Exception as e:
            logger.error(f"Face registration error: {e}")
            return False, None, str(e)
    
    def recognize_face(self, image, frames=None, check_liveness=True):
        """Recognize face with optional liveness check."""
        try:
            # Check liveness if frames provided
            if check_liveness and frames and len(frames) >= 3:
                is_live = self._pipeline.check_liveness(frames)
                if not is_live:
                    return {
                        'success': False,
                        'error': 'Liveness check failed',
                        'liveness_passed': False
                    }
            
            # Recognize face
            result = self._pipeline.recognize_face(image)
            result['liveness_passed'] = True if not check_liveness else True
            
            return result
            
        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return {
                'success': False,
                'error': str(e),
                'face_detected': False
            }
    
    def save_training_data(self):
        """Save training data to file."""
        models_dir = settings.AI_SETTINGS.get('MODELS_DIR', 'models/')
        training_file = os.path.join(models_dir, 'face_encodings.pkl')
        return self._pipeline.save_training_data(training_file)


# Singleton accessor
def get_enhanced_ai_manager():
    return EnhancedAIServiceManager()
```

## Testing Your Integration

### 1. Test Quality Checks
```python
# Test with blurry image
result = manager.register_face(blurry_image, "test_student")
assert not result[0]
assert "blurry" in result[2].lower()

# Test with good image
result = manager.register_face(good_image, "test_student")
assert result[0]
```

### 2. Test Liveness Detection
```python
# Capture multiple frames
frames = capture_multiple_frames()
result = manager.recognize_face(last_frame, frames=frames)
assert result['liveness_passed']
```

### 3. Test Encryption
```python
# Register and save
manager.register_face(image, "student123")
manager.save_training_data()

# Create new manager (simulating restart)
new_manager = get_enhanced_ai_manager()
# Should be able to load encrypted data
assert new_manager._pipeline.storage.count() > 0
```

## Troubleshooting

### Issue: "cryptography package not installed"
```bash
pip install cryptography
```

### Issue: "DNN model files not found"
Download models from README.md and place in `models/` directory.

### Issue: "Liveness always fails"
- Ensure `shape_predictor_68_face_landmarks.dat` is in `models/`
- Provide at least 3 frames
- Check that frames show actual movement

### Issue: "Quality checks too strict"
Adjust thresholds in settings:
```python
from apps.ai_core.facial_recognition.utils import FaceQualityChecker

FaceQualityChecker.MIN_BLUR_THRESHOLD = 80.0  # Lower = more lenient
FaceQualityChecker.MIN_BRIGHTNESS = 30
FaceQualityChecker.MAX_BRIGHTNESS = 230
```

## Performance Tips

1. **Quality checks**: Only enable during registration, not recognition
2. **Liveness**: Make it optional for trusted environments
3. **Alignment**: Use SimpleFaceAligner for speed
4. **Detector**: Use Haar Cascade for speed, DNN for accuracy
5. **Image size**: Resize large images to 800px max dimension

## Support

For issues or questions:
1. Check README.md for detailed documentation
2. Review IMPLEMENTATION_SUMMARY.md for architecture
3. Run test suite to verify installation
4. Check logs for detailed error messages
