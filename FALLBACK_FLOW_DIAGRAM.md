# Cascading Fallback Detection Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Face Recognition Pipeline                   │
│                    (FacialRecognitionPipeline)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ enable_fallback=True
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Fallback Detection Manager                    │
│                  (FallbackDetectionManager)                     │
│                                                                 │
│  Manages: - Detector initialization (lazy loading)             │
│           - Cascading detection logic                          │
│           - Statistics tracking                                │
│           - Method selection and fallback                      │
└─────────────────────────────────────────────────────────────────┘
```

## Detection Flow Diagram

```
                    ┌─────────────┐
                    │   Input     │
                    │   Image     │
                    └──────┬──────┘
                           │
                           ↓
                ┌──────────────────────┐
                │ Image Enhancement    │
                │ - Bilateral Filter   │
                │ - CLAHE              │
                │ - Sharpening         │
                └──────────┬───────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │    START FALLBACK CASCADE            │
        └──────────────────┬───────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │  Method 1: CNN (Most Accurate)       │
        │  - Best for frontal faces            │
        │  - GPU recommended                   │
        └──────────┬──────────────┬────────────┘
                   │              │
              SUCCESS ✓        FAIL ✗
                   │              │
                   │              ↓
                   │    ┌──────────────────────────┐
                   │    │  Method 2: DNN-SSD       │
                   │    │  - Good for angles       │
                   │    │  - ResNet-based          │
                   │    └────┬──────────────┬──────┘
                   │         │              │
                   │    SUCCESS ✓        FAIL ✗
                   │         │              │
                   │         │              ↓
                   │         │    ┌──────────────────────┐
                   │         │    │  Method 3: MTCNN     │
                   │         │    │  - Facial landmarks  │
                   │         │    │  - Multi-task CNN    │
                   │         │    └────┬──────────┬──────┘
                   │         │         │          │
                   │         │    SUCCESS ✓    FAIL ✗
                   │         │         │          │
                   │         │         │          ↓
                   │         │         │    ┌──────────────────┐
                   │         │         │    │  Method 4: Dlib  │
                   │         │         │    │  - HOG-based     │
                   │         │         │    │  - Balanced      │
                   │         │         │    └────┬──────┬──────┘
                   │         │         │         │      │
                   │         │         │    SUCCESS ✓ FAIL ✗
                   │         │         │         │      │
                   │         │         │         │      ↓
                   │         │         │         │ ┌─────────────────┐
                   │         │         │         │ │  Method 5: HOG  │
                   │         │         │         │ │  - Fast, CPU    │
                   │         │         │         │ │  - Traditional  │
                   │         │         │         │ └────┬──────┬─────┘
                   │         │         │         │      │      │
                   │         │         │         │ SUCCESS ✓ FAIL ✗
                   │         │         │         │      │      │
                   │         │         │         │      │      ↓
                   │         │         │         │      │ ┌─────────────────────┐
                   │         │         │         │      │ │  Method 6: Haar     │
                   │         │         │         │      │ │  - Last resort      │
                   │         │         │         │      │ │  - Most robust      │
                   │         │         │         │      │ └────┬──────┬─────────┘
                   │         │         │         │      │      │      │
                   │         │         │         │      │ SUCCESS ✓ FAIL ✗
                   │         │         │         │      │      │      │
                   └─────────┴─────────┴─────────┴──────┴──────┘      │
                                      │                                │
                                      ↓                                ↓
                        ┌──────────────────────┐        ┌─────────────────────┐
                        │  Face Location       │        │  All Methods Failed │
                        │  Detected            │        │  Return Error       │
                        └──────────┬───────────┘        └─────────────────────┘
                                   │
                                   ↓
                        ┌──────────────────────┐
                        │  Quality Checks      │
                        │  (if enabled)        │
                        └──────────┬───────────┘
                                   │
                                   ↓
                        ┌──────────────────────┐
                        │  Face Alignment      │
                        │  (if available)      │
                        └──────────┬───────────┘
                                   │
                                   ↓
                        ┌──────────────────────────────┐
                        │  ENCODING EXTRACTION         │
                        │  WITH MODEL FALLBACK         │
                        └──────────┬───────────────────┘
                                   │
                                   ↓
                        ┌──────────────────────┐
                        │  Model 1: Large      │
                        │  (Most Accurate)     │
                        └──────┬──────────┬────┘
                               │          │
                          SUCCESS ✓    FAIL ✗
                               │          │
                               │          ↓
                               │    ┌──────────────────┐
                               │    │  Model 2: Small  │
                               │    │  (Faster)        │
                               │    └────┬──────┬──────┘
                               │         │      │
                               │    SUCCESS ✓ FAIL ✗
                               │         │      │
                               └─────────┘      │
                                      │         │
                                      ↓         ↓
                        ┌──────────────────────────────┐
                        │  Face Encoding (128-d)       │
                        │  OR                          │
                        │  Encoding Failure Error      │
                        └──────────┬───────────────────┘
                                   │
                                   ↓
                        ┌──────────────────────┐
                        │  Return Results      │
                        │  with Metadata       │
                        └──────────────────────┘
```

## Statistics Tracking

```
┌────────────────────────────────────────┐
│      Detection Method Statistics      │
├────────────────────────────────────────┤
│                                        │
│  CNN:                                  │
│    Attempts:  150                      │
│    Successes: 120                      │
│    Rate:      80.0%                    │
│                                        │
│  DNN-SSD:                              │
│    Attempts:  30                       │
│    Successes: 20                       │
│    Rate:      66.7%                    │
│                                        │
│  HOG:                                  │
│    Attempts:  10                       │
│    Successes: 8                        │
│    Rate:      80.0%                    │
│                                        │
│  (etc...)                              │
│                                        │
└────────────────────────────────────────┘
```

## Response Structure

```javascript
// Success Response
{
  "success": true,
  "student_id": "12345",
  "confidence": 0.852,
  "distance": 0.148,
  "face_detected": true,
  "detection_metadata": {
    "method_used": "cnn",              // Which detector succeeded
    "attempts": ["cnn"],                // Methods tried before success
    "encoding_model": "large"           // Which encoding model worked
  }
}

// Failure After All Attempts
{
  "success": false,
  "error": "No face detected by any method (tried: cnn, dnn_ssd, mtcnn, dlib, hog, haar_cascade)",
  "face_detected": false,
  "confidence": 0.0,
  "detection_metadata": {
    "method_used": null,
    "attempts": [
      "cnn",
      "dnn_ssd", 
      "mtcnn",
      "dlib",
      "hog",
      "haar_cascade"
    ]
  }
}
```

## Code Flow Example

```python
# 1. User calls recognize_face
result = pipeline.recognize_face(image)

# 2. Pipeline calls _extract_face_encoding
encoding, error, location, metadata = pipeline._extract_face_encoding(image)

# 3. If fallback enabled, FallbackDetectionManager takes over
if pipeline.enable_fallback:
    # 4. Try each detector in order
    for method in [CNN, DNN_SSD, MTCNN, DLIB, HOG, HAAR]:
        detection_result = try_detector(method)
        if detection_result['success']:
            # 5. Success! Record statistics
            statistics[method]['successes'] += 1
            break
    
    # 6. If face found, try encoding extraction
    for model in [LARGE, SMALL]:
        encoding = try_extract_encoding(model)
        if encoding:
            break
    
    # 7. Return results with metadata
    return {
        'success': True,
        'encoding': encoding,
        'detection_metadata': {
            'method_used': 'cnn',
            'attempts': ['cnn'],
            'encoding_model': 'large'
        }
    }
```

## Performance Optimization

```
                    Detection Request
                           │
                           ↓
                ┌──────────────────────┐
                │  Check if detector   │
                │  already initialized │
                └──────────┬───────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
            YES (cached)          NO  │
                │                     │
                │                     ↓
                │          ┌──────────────────┐
                │          │  Lazy initialize │
                │          │  detector now    │
                │          └────────┬─────────┘
                │                   │
                └───────────┬───────┘
                            │
                            ↓
                    Use detector
                    
Memory Impact: Only used detectors consume RAM
Speed Impact: Initialization only happens once per detector
```

## Decision Tree

```
Is face visible? ─── NO ──→ Try all methods → Still no? → UNRECOGNIZED
    │
   YES
    │
    ↓
Good lighting? ─── YES ──→ CNN succeeds → RECOGNIZED
    │
    NO
    │
    ↓
Face at angle? ─── YES ──→ DNN-SSD succeeds → RECOGNIZED
    │
    NO
    │
    ↓
Very poor quality? ─── YES ──→ Haar Cascade succeeds → RECOGNIZED
    │
    NO
    │
    ↓
Try all methods → One succeeds? ─── YES ──→ RECOGNIZED
                                │
                                NO
                                │
                                ↓
                           UNRECOGNIZED
```

## Integration Points

```
┌────────────────────────────────────────────────────────┐
│                  Django Application                    │
│                                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │         AIServiceManager                     │    │
│  │  (apps.ai_core.services)                     │    │
│  └────────────────┬─────────────────────────────┘    │
│                   │                                    │
│                   ↓                                    │
│  ┌──────────────────────────────────────────────┐    │
│  │     FacialRecognitionPipeline                │    │
│  │  (with fallback enabled by default)          │    │
│  └────────────────┬─────────────────────────────┘    │
│                   │                                    │
│                   ↓                                    │
│  ┌──────────────────────────────────────────────┐    │
│  │     FallbackDetectionManager                 │    │
│  │  (handles all detector fallback)             │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Log Message Flow

```
[INFO] Attempting face detection with CNN model (most accurate)...
         │
         ↓
    [SUCCESS?] ─── YES ──→ [INFO] ✓ Face detected successfully using CNN
         │                         │
         NO                        ↓
         │                    Continue to encoding...
         ↓
[INFO] CNN model failed to detect face, falling back to DNN-SSD...
         │
         ↓
    [SUCCESS?] ─── YES ──→ [INFO] ✓ Face detected successfully using DNN_SSD
         │                         │
         NO                        ↓
         │                    Continue to encoding...
         ↓
    (Continue for all methods...)
         │
         ↓
[WARNING] ✗ No face detected by any method (tried: cnn, dnn_ssd, ...)
```
