# Facial Recognition Package

Comprehensive facial recognition system for the AI-based Attendance System with support for multiple detectors, liveness detection, quality validation, and encryption.

## Features

### Core Functionality
- **Face Detection**: Multiple detector implementations (Haar Cascade, DNN, MTCNN, Dlib)
- **Face Recognition**: High-accuracy face encoding and matching
- **Liveness Detection**: Anti-spoofing with blink and motion detection
- **Face Quality Validation**: Blur, brightness, and size checks
- **Face Alignment**: Landmark-based and simple alignment methods
- **Secure Storage**: Encrypted face encoding storage with Fernet encryption

### Architecture

The package follows the **Strategy Pattern** with abstract base classes:
- `FaceDetector` - Interface for face detection
- `FaceRecognizer` - Interface for face encoding
- `LivenessDetector` - Interface for liveness checking

## Installation

### Required Dependencies
```bash
pip install opencv-python face-recognition numpy Pillow
```

### Optional Dependencies
```bash
# For DNN-based detection (already included in opencv-python)
pip install opencv-contrib-python

# For MTCNN detector
pip install mtcnn

# For Dlib detector and facial landmarks
pip install dlib

# For encryption
pip install cryptography
```

### Download Models (Optional)

For advanced features, download these models:

1. **Facial Landmark Predictor** (for blink detection and alignment):
   - Download: [shape_predictor_68_face_landmarks.dat](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2)
   - Extract to: `models/shape_predictor_68_face_landmarks.dat`

2. **DNN Face Detector Models**:
   - [deploy.prototxt](https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt)
   - [res10_300x300_ssd_iter_140000.caffemodel](https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel)
   - Place in: `models/` directory

## Quick Start

### Basic Usage

```python
from apps.ai_core.facial_recognition import FacialRecognitionPipeline
import cv2

# Initialize pipeline
pipeline = FacialRecognitionPipeline(
    confidence_threshold=0.6,
    enable_quality_checks=True
)

# Register a face
image = cv2.imread('student_photo.jpg')
success, encoding, message = pipeline.register_face(image, "student123")

if success:
    print(f"Face registered: {message}")
    
    # Save training data
    pipeline.save_training_data('models/face_encodings.pkl')
else:
    print(f"Registration failed: {message}")

# Recognize a face
test_image = cv2.imread('test_photo.jpg')
result = pipeline.recognize_face(test_image)

if result['success']:
    print(f"Recognized: {result['student_id']}")
    print(f"Confidence: {result['confidence']:.2%}")
else:
    print(f"Recognition failed: {result['error']}")
```

### Using Different Detectors

```python
from apps.ai_core.facial_recognition import (
    FacialRecognitionPipeline,
    DNNFaceDetector,
    MTCNNFaceDetector
)

# Use DNN detector (more accurate)
dnn_detector = DNNFaceDetector(confidence_threshold=0.5)
pipeline = FacialRecognitionPipeline(face_detector=dnn_detector)

# Use MTCNN detector (highest accuracy)
mtcnn_detector = MTCNNFaceDetector(min_face_size=40)
pipeline = FacialRecognitionPipeline(face_detector=mtcnn_detector)
```

### Face Quality Validation

```python
from apps.ai_core.facial_recognition.utils import FaceQualityChecker
import cv2

image = cv2.imread('photo.jpg')

# Check all quality metrics
results = FaceQualityChecker.check_all(image)

if results['overall_pass']:
    print("Image quality is good")
else:
    print("Quality issues:")
    for msg in results['messages']:
        print(f"  - {msg}")

# Check individual metrics
is_sharp, blur_score, msg = FaceQualityChecker.check_blur(image)
is_bright, brightness, msg = FaceQualityChecker.check_brightness(image)
```

### Liveness Detection

```python
from apps.ai_core.facial_recognition.liveness import (
    BlinkLivenessDetector,
    MotionLivenessDetector
)

# Blink-based liveness
blink_detector = BlinkLivenessDetector(
    ear_threshold=0.21,
    min_blinks=2
)

# Capture multiple frames
frames = []  # List of cv2 images
is_live = blink_detector.check_liveness(frames)

# Motion-based liveness
motion_detector = MotionLivenessDetector(motion_threshold=0.02)
is_live = motion_detector.check_liveness(frames)
```

### Face Alignment

```python
from apps.ai_core.facial_recognition.alignment import (
    FaceAligner,
    SimpleFaceAligner
)

# Landmark-based alignment (more accurate)
aligner = FaceAligner(desired_face_width=256)
aligned_face = aligner.align_face(image, face_rect)

# Simple alignment (faster)
simple_aligner = SimpleFaceAligner(target_size=(160, 160))
aligned_face = simple_aligner.align_face(image, face_rect)
```

### Encrypted Storage

```python
from apps.ai_core.facial_recognition.storage import TrainingDataStorage

# Enable encryption
storage = TrainingDataStorage(enable_encryption=True)

# Get the encryption key (store securely!)
key = storage.get_encryption_key()
print(f"Store this key securely: {key.decode()}")

# Use with pipeline
pipeline = FacialRecognitionPipeline(storage=storage)

# All saved data will be encrypted
pipeline.save_training_data('models/encrypted_encodings.pkl')

# Load with same key
new_storage = TrainingDataStorage(
    encryption_key=key,
    enable_encryption=True
)
new_storage.load_from_file('models/encrypted_encodings.pkl')
```

## API Reference

### FacialRecognitionPipeline

Main orchestrator for facial recognition operations.

#### Methods

- `register_face(image, student_id, check_quality=True)` - Register a new face
- `recognize_face(image, return_all_matches=False)` - Recognize a face
- `check_liveness(frames)` - Check if face is live
- `save_training_data(path)` - Save encodings to file
- `load_training_data(path)` - Load encodings from file

### Face Detectors

#### CVFaceDetector
- OpenCV Haar Cascade detector
- Fast but less accurate
- Good for controlled environments

#### DNNFaceDetector
- ResNet SSD-based detector
- More accurate than Haar Cascade
- Better with varying angles

#### MTCNNFaceDetector
- Multi-task CNN detector
- Highest accuracy
- Also provides facial landmarks
- Requires `mtcnn` package

#### DlibFaceDetector
- HOG-based detector
- Good balance of speed and accuracy
- Requires `dlib` package

### Liveness Detectors

#### BlinkLivenessDetector
- Eye Aspect Ratio (EAR) based
- Detects natural eye blinks
- Requires facial landmark predictor
- Parameters:
  - `ear_threshold`: EAR threshold (default: 0.21)
  - `min_blinks`: Minimum blinks required (default: 1)

#### MotionLivenessDetector
- Frame difference based
- Detects face movement
- Simpler than blink detection
- Parameters:
  - `motion_threshold`: Motion ratio threshold (default: 0.02)
  - `min_motion_frames`: Minimum frames with motion (default: 2)

### Quality Checks

#### FaceQualityChecker

Static methods for quality validation:
- `check_blur(image, threshold)` - Check image sharpness
- `check_brightness(image, min_brightness, max_brightness)` - Check illumination
- `check_face_size(face_location, min_size, max_size)` - Check face dimensions
- `check_all(image, face_location)` - Run all checks

## Configuration

### Quality Thresholds

Adjust in your code or settings:

```python
from apps.ai_core.facial_recognition.utils import FaceQualityChecker

# Customize thresholds
FaceQualityChecker.MIN_BLUR_THRESHOLD = 150.0  # Higher = require sharper images
FaceQualityChecker.MIN_BRIGHTNESS = 50
FaceQualityChecker.MAX_BRIGHTNESS = 200
FaceQualityChecker.MIN_FACE_SIZE = (100, 100)
```

### Recognition Confidence

```python
pipeline = FacialRecognitionPipeline(confidence_threshold=0.7)  # 70% confidence
```

## Testing

Run the test suite:

```bash
# All tests
python -m pytest attendance_system/apps/ai_core/facial_recognition/tests/

# Specific test file
python -m pytest attendance_system/apps/ai_core/facial_recognition/tests/test_pipeline.py

# With coverage
python -m pytest --cov=apps.ai_core.facial_recognition tests/
```

## Performance Optimization

### Tips for Production

1. **Use DNN or MTCNN detectors** for better accuracy
2. **Enable quality checks** during registration only
3. **Use GPU acceleration** for DNN models (requires CUDA)
4. **Cache encodings in memory** for frequently accessed students
5. **Batch process** multiple faces when possible
6. **Resize large images** before processing

### Example Optimization

```python
# Resize large images before processing
import cv2

def preprocess_image(image, max_dimension=800):
    height, width = image.shape[:2]
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height))
    return image

# Use in pipeline
image = cv2.imread('large_photo.jpg')
image = preprocess_image(image)
result = pipeline.recognize_face(image)
```

## Security Considerations

1. **Always use encryption** for stored face encodings in production
2. **Store encryption keys securely** (use environment variables or key management systems)
3. **Implement rate limiting** on recognition endpoints
4. **Enable liveness detection** to prevent spoofing attacks
5. **Use HTTPS** for API endpoints
6. **Add audit logging** for all recognition attempts
7. **Implement access control** on training data files

## Troubleshooting

### Common Issues

**Issue**: "No face detected in image"
- Ensure good lighting
- Face should be front-facing
- Check image quality
- Try different detector

**Issue**: "Image is too blurry"
- Use higher resolution camera
- Ensure focus is correct
- Adjust `MIN_BLUR_THRESHOLD`

**Issue**: "Liveness detection always fails"
- Check if `shape_predictor_68_face_landmarks.dat` is present
- Ensure at least 3 frames are provided
- Adjust EAR threshold

**Issue**: Low recognition accuracy
- Register multiple images per person
- Use face alignment
- Increase confidence threshold
- Ensure consistent lighting

## Contributing

When contributing new detectors or recognizers:

1. Inherit from appropriate base class
2. Implement all abstract methods
3. Add conditional imports for optional dependencies
4. Handle errors gracefully
5. Add comprehensive tests
6. Update documentation

## License

This package is part of the AI-based Attendance System project.
