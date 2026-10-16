"""
OpenCV ONNX backend for face detection and recognition.

Why this exists
---------------
The original backend is ``face_recognition``, which depends on ``dlib``. dlib is
a C++ extension that needs cmake, Boost and a 10-20 minute compile, so it
cannot be installed on PythonAnywhere's shared hosting. The previous
consequence was that facial recognition simply never worked in production:
``GET /api/ai/configuration/status/`` reported ``"available": false`` and every
AI endpoint returned 503.

OpenCV ships the same functionality as ONNX neural networks, and those are
published as prebuilt wheels - no compiler at all:

* **YuNet** (detector, 0.2 MB)
* **SFace** (recogniser, 37 MB, emits a 128-dimension embedding)

37 MB instead of 96 MB plus a compiler, which fits comfortably inside
PythonAnywhere's 512 MB disk quota.

What this backend does NOT provide
---------------------------------
Blink-based liveness detection. That needs dlib's 68-point landmark predictor,
which needs dlib. ``SFaceRecognizer`` performs its own geometric alignment via
``FaceRecognizerSF.alignCrop``, so recognition accuracy is preserved, but the
anti-spoofing blink check is unavailable on this backend.

Embeddings are NOT interchangeable with the dlib backend
----------------------------------------------------------
SFace and dlib produce different vectors for the same face, and SFace operates
in a cosine-similarity space while dlib's ``face_distance`` is Euclidean. Any
faces registered with the dlib backend must be registered again after switching.
:attr:`SFaceRecognizer.default_distance_threshold` reflects the different
scale so the same ``recognize_face()`` call works for either backend.
"""

import logging
import os
import urllib.request

import numpy as np

from .base import FaceDetector, FaceRecognizer

logger = logging.getLogger(__name__)

# Conditional imports. FaceDetectorYN and FaceRecognizerSF live in
# opencv-contrib-python; plain opencv-python does not have them.
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    cv2 = None
    HAS_OPENCV = False

HAS_YUNET = HAS_OPENCV and hasattr(cv2, 'FaceDetectorYN')
HAS_SFACE = HAS_OPENCV and hasattr(cv2, 'FaceRecognizerSF')
HAS_OPENCV_FACE = HAS_YUNET and HAS_SFACE


# =============================================================================
# Model bootstrap
# =============================================================================
# Served from opencv_zoo, the official OpenCV model repository. These files are
# not committed to git; they are downloaded on first use into
# AI_SETTINGS['MODELS_DIR'].

MODEL_SOURCES = {
    'face_detection_yunet_2023mar.onnx': (
        'https://github.com/opencv/opencv_zoo/raw/main/models/'
        'face_detection_yunet/face_detection_yunet_2023mar.onnx'
    ),
    'face_recognition_sface_2021dec.onnx': (
        'https://github.com/opencv/opencv_zoo/raw/main/models/'
        'face_recognition_sface/face_recognition_sface_2021dec.onnx'
    ),
}

# A truncated download (GitHub HTML error page saved as .onnx) must not be
# mistaken for a valid model, so sizes are verified.
EXPECTED_SIZES = {
    'face_detection_yunet_2023mar.onnx': 232_970,
    'face_recognition_sface_2021dec.onnx': 38_713_522,
}

_download_lock_status = {}


def ensure_models(models_dir):
    """
    Make sure both ONNX models are present in `models_dir`, downloading any
    that are missing or the wrong size.

    Returns True when everything is in place. Never raises: a network problem
    must surface as "face recognition unavailable", not a 500.
    """
    if not HAS_OPENCV_FACE:
        return False

    try:
        os.makedirs(models_dir, exist_ok=True)
    except OSError as exc:
        logger.warning('Could not create models directory %s: %s', models_dir, exc)
        return False

    for filename, url in MODEL_SOURCES.items():
        destination = os.path.join(models_dir, filename)
        expected = EXPECTED_SIZES.get(filename, 0)

        if os.path.isfile(destination):
            actual = os.path.getsize(destination)
            if expected and actual < expected * 0.9:
                logger.warning(
                    '%s is %d bytes, expected about %d - re-downloading',
                    filename, actual, expected,
                )
                try:
                    os.remove(destination)
                except OSError:
                    pass
            else:
                continue

        logger.info('Downloading %s (~%.1f MB)', filename, expected / 1_048_576)
        try:
            urllib.request.urlretrieve(url, destination)
        except Exception as exc:
            logger.error('Failed to download %s: %s', filename, exc)
            _download_lock_status[filename] = str(exc)
            return False

        actual = os.path.getsize(destination)
        if expected and actual < expected * 0.9:
            logger.error(
                '%s downloaded only %d bytes - the URL probably returned an '
                'error page instead of the model', filename, actual,
            )
            try:
                os.remove(destination)
            except OSError:
                pass
            _download_lock_status[filename] = 'incomplete download'
            return False

    return True


def models_available(models_dir):
    """Whether both models are already on disk (no download attempted)."""
    if not HAS_OPENCV_FACE:
        return False
    return all(
        os.path.isfile(os.path.join(models_dir, name))
        for name in MODEL_SOURCES
    )


# =============================================================================
# Detector
# =============================================================================
class YuNetFaceDetector(FaceDetector):
    """
    Face detector backed by YuNet, a lightweight ONNX CNN.

    YuNet reports the five facial landmarks alongside each box, which is what
    makes SFace's alignment possible without the 96 MB dlib landmark model.
    """

    def __init__(self, models_dir, score_threshold=0.6, nms_threshold=0.3,
                 top_k=5000):
        self.models_dir = models_dir
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k
        self._detector = None
        self._last_faces = None

    def _get_detector(self, width, height):
        """Create (once) the YuNet detector sized for this image."""
        if self._detector is None:
            model_path = os.path.join(
                self.models_dir, 'face_detection_yunet_2023mar.onnx'
            )
            if not os.path.isfile(model_path):
                raise FileNotFoundError(model_path)
            self._detector = cv2.FaceDetectorYN.create(
                model_path,
                '',
                (width, height),
                self.score_threshold,
                self.nms_threshold,
                self.top_k,
            )
        else:
            # YuNet's input size is fixed at construction time.
            self._detector.setInputSize((width, height))
        return self._detector

    def _as_bgr_u8(self, image):
        """Coerce whatever the caller passed into a BGR uint8 array."""
        array = np.asarray(image)
        if array.dtype != np.uint8:
            array = np.clip(array, 0, 255).astype(np.uint8)
        if array.ndim == 2:
            array = cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
        return array

    def detect_raw(self, image):
        """
        Detect faces and return the raw YuNet rows.

        Each row is a 15-element array:
        ``[x, y, w, h, right_eye_x, right_eye_y, left_eye_x, left_eye_y,
        nose_x, nose_y, right_mouth_x, right_mouth_y, left_mouth_x,
        left_mouth_y, score]``

        The landmarks are required by :meth:`SFaceRecognizer.align_and_encode`;
        the FaceDetector interface alone only needs the boxes.
        """
        array = self._as_bgr_u8(image)
        if array.size == 0:
            return []

        height, width = array.shape[:2]
        detector = self._get_detector(width, height)
        _, faces = detector.detect(array)

        self._last_faces = faces
        if faces is None:
            return []
        return faces

    def detect_faces(self, image):
        """
        Detect faces, returning ``[(x, y, w, h), ...]``.

        Sorted by descending score so callers taking the first result get the
        most confident face.
        """
        faces = self.detect_raw(image)
        results = []
        for row in faces:
            x, y, w, h = (float(v) for v in row[:4])
            results.append((int(x), int(y), int(w), int(h)))
        results.sort(key=lambda box: -box[2] * box[3])
        return results

    def best_face_row(self, image):
        """The single highest-scoring YuNet row, or None."""
        faces = self.detect_raw(image)
        if len(faces) == 0:
            return None
        # Row index 14 is the detection score.
        return faces[int(np.argmax(faces[:, 14]))]


# =============================================================================
# Recogniser
# =============================================================================
class SFaceRecognizer(FaceRecognizer):
    """
    Face recogniser backed by SFace, a 128-dimension ONNX embedding model.

    Embeddings are L2-normalised before comparison, which makes Euclidean
    distance and cosine similarity equivalent up to a monotonic transform:
    ``distance = sqrt(2 - 2 * cosine)``.
    """

    # SFace's published cosine threshold is 0.363, which is
    # sqrt(2 - 2 * 0.363) ~= 1.13 in Euclidean terms. dlib's equivalent is
    # 0.6, so the two backends need different defaults for the same
    # strictness. Callers that do not pass a threshold get the right one for
    # whichever backend is active.
    #
    # Overridable via FACE_MATCH_THRESHOLD in .env, because the correct value
    # depends on the real roster: raise it to reject near-misses more
    # aggressively, lower it if genuine matches are being refused.
    DEFAULT_DISTANCE_THRESHOLD = 1.13

    def __init__(self, models_dir, detector=None):
        self.models_dir = models_dir
        self._recognizer = None
        self._detector = detector or YuNetFaceDetector(models_dir)
        self._configured_threshold = None

    @property
    def default_distance_threshold(self):
        if self._configured_threshold is not None:
            return self._configured_threshold
        try:
            from django.conf import settings

            value = getattr(settings, 'AI_SETTINGS', {}).get('FACE_MATCH_THRESHOLD')
            if value:
                return float(value)
        except Exception:
            pass
        return self.DEFAULT_DISTANCE_THRESHOLD

    @default_distance_threshold.setter
    def default_distance_threshold(self, value):
        self._configured_threshold = float(value)

    @property
    def detector(self):
        return self._detector

    def _get_recognizer(self):
        if self._recognizer is None:
            model_path = os.path.join(
                self.models_dir, 'face_recognition_sface_2021dec.onnx'
            )
            if not os.path.isfile(model_path):
                raise FileNotFoundError(model_path)
            self._recognizer = cv2.FaceRecognizerSF.create(model_path, '')
        return self._recognizer

    @staticmethod
    def _normalise(embedding):
        vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            return vector
        return vector / norm

    def get_face_encoding(self, image, face_locations=None):
        """
        Produce a 128-dimension embedding for the most prominent face.

        Args:
            image: BGR uint8 image.
            face_locations: Unused by this backend - SFace aligns from YuNet's
                landmarks, which are more accurate than a bounding box. Accepted
                so the signature matches the FaceDetector/FaceRecognizer
                interface.

        Returns:
            A 128-dimension float32 array, or None when no face was found.
        """
        try:
            row = self._detector.best_face_row(image)
            if row is None:
                return None

            array = self._detector._as_bgr_u8(image)
            aligned = self._get_recognizer().alignCrop(array, row)
            feature = self._get_recognizer().feature(aligned)
            return np.asarray(feature, dtype=np.float32).reshape(-1)
        except FileNotFoundError:
            raise
        except Exception as exc:
            logger.error('SFace encoding failed: %s', exc)
            return None

    def distance(self, known_encodings, candidate):
        """
        Euclidean distance from `candidate` to each known encoding.

        Args:
            known_encodings: Iterable of 128-dimension encodings.
            candidate: A single 128-dimension encoding.

        Returns:
            A float32 array of distances, same length and order as
            `known_encodings`.
        """
        candidate = self._normalise(candidate)
        distances = []
        for known in known_encodings:
            known = self._normalise(known)
            distances.append(float(np.linalg.norm(known - candidate)))
        return np.asarray(distances, dtype=np.float32)


def backend_status(models_dir):
    """Human-readable availability report for this backend."""
    if not HAS_OPENCV:
        return {
            'available': False,
            'reason': 'opencv-python is not installed',
        }
    if not HAS_OPENCV_FACE:
        return {
            'available': False,
            'reason': (
                'this OpenCV build has no FaceDetectorYN/FaceRecognizerSF; '
                'install opencv-contrib-python-headless'
            ),
        }
    if not models_available(models_dir):
        return {
            'available': False,
            'reason': 'ONNX models not downloaded yet',
            'will_download_on_demand': True,
        }
    return {'available': True, 'reason': None}
