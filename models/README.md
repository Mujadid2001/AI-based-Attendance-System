# models/

Runtime AI assets. **Nothing in here is tracked by git** — see below for why,
and for how to restore each file.

This directory is created automatically on first start
(`config/settings/app_settings.py` makes `AI_SETTINGS['MODELS_DIR']` if it is
missing).

| File | Size | Purpose | Tracked? |
|---|---|---|---|
| `face_detection_yunet_2023mar.onnx` | 0.2 MB | YuNet face detector | no |
| `face_recognition_sface_2021dec.onnx` | 37 MB | SFace 128-d recogniser | no |
| `shape_predictor_68_face_landmarks.dat` | 96 MB | dlib alignment + blink liveness | no |
| `face_encodings.pkl` | ~12 KB | cached face encodings (biometric data) | no |

**The two ONNX files download automatically** the first time face recognition
is used. Nothing to do. They come from the official OpenCV model zoo:

- <https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet>
- <https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface>

`apps/ai_core/facial_recognition/opencv_backend.py` downloads them into
`AI_SETTINGS['MODELS_DIR']` and verifies the byte size, so a failed fetch that
saves an HTML error page as `.onnx` is detected rather than crashing later.

To install them ahead of time (useful offline, or to make the first request
faster):

```bash
mkdir -p models
curl -L -o models/face_detection_yunet_2023mar.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
curl -L -o models/face_recognition_sface_2021dec.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
ls -l models/*.onnx   # expect 232970 and 38713522 bytes
```

---

## Why nothing here is in git

**`shape_predictor_68_face_landmarks.dat`** is 96 MB. It is only read inside
`if HAS_DLIB:` blocks, and dlib cannot be installed on PythonAnywhere, so on
the server it was pure ballast — while single-handedly contributing to the
`OSError: [Errno 122] Disk quota exceeded` failure during a first deploy.
PythonAnywhere's shared and free tiers cap `/home/<username>` at 512 MB.

**`face_encodings.pkl` is biometric data**: 128-dimension face embeddings keyed
by user id. A face embedding is a biometric identifier and must never be in
version control, let alone a public repository. The app regenerates it.

If you want the landmark predictor for local dlib-based recognition:

```bash
curl -L -o models/shape_predictor_68_face_landmarks.dat \
  http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 models/shape_predictor_68_face_landmarks.dat
```

Verify it is the real file, not an error page: `ls -l` should report
`99,693,937` bytes.

---

## Which backend is in use

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://mujadid.pythonanywhere.com/api/ai/configuration/status/
```

```json
{
  "facial_recognition": {
    "available": true,
    "backend": "opencv",
    "reason": null,
    "threshold": 0.7,
    "match_distance_threshold": 1.13,
    "liveness_available": false
  },
  "voice_notifications": {"available": false}
}
```

| `backend` | Needs | Available on PythonAnywhere? |
|---|---|---|
| `opencv` | `opencv-contrib-python-headless` + these two ONNX models | **yes** |
| `dlib` | `face_recognition` + dlib + cmake + Boost | no |

The pipeline picks dlib automatically when it is importable, so existing
encodings keep working. `liveness_available: false` means blink-based
anti-spoofing is off, which needs dlib's landmark model.

**Switching backends invalidates existing encodings.** dlib and SFace produce
different vectors for the same face, so anyone whose face was registered under
one backend must re-register under the other.
