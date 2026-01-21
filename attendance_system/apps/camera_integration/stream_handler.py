"""
Wireless/IP Camera Stream Handler
Handles RTSP, HTTP/MJPEG stream connections and frame extraction
"""
import logging
import threading
import time
import base64
from typing import Optional, Callable
from io import BytesIO

logger = logging.getLogger(__name__)

# Optional imports for stream handling
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("OpenCV not available - wireless camera streaming disabled")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class WirelessCameraStreamHandler:
    """
    Handles streaming from wireless/IP cameras with RTSP, HTTP/MJPEG protocols.
    Runs in background thread and calls callback with frames.
    """
    
    def __init__(self, camera_source, on_frame_callback: Optional[Callable] = None):
        """
        Initialize stream handler.
        
        Args:
            camera_source: ExternalCameraSource model instance
            on_frame_callback: Function called with each frame (frame_base64, timestamp)
        """
        self.camera_source = camera_source
        self.on_frame_callback = on_frame_callback
        self.is_running = False
        self.thread = None
        self.capture = None
        self.last_frame_time = 0
        self.frame_interval = 1.0 / camera_source.fps_limit  # Convert FPS to seconds
        
    def start(self):
        """Start streaming in background thread."""
        if not HAS_CV2:
            logger.error("Cannot start stream - OpenCV not available")
            return False
        
        if self.is_running:
            logger.warning(f"Stream already running for camera {self.camera_source.id}")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started stream for camera {self.camera_source.name} ({self.camera_source.id})")
        return True
    
    def stop(self):
        """Stop streaming thread."""
        self.is_running = False
        if self.capture:
            try:
                self.capture.release()
            except:
                pass
            self.capture = None
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info(f"Stopped stream for camera {self.camera_source.name}")
    
    def _build_stream_url(self) -> str:
        """Build authenticated stream URL."""
        url = self.camera_source.stream_url
        
        # Add authentication if provided
        if self.camera_source.stream_username and self.camera_source.stream_password:
            # For RTSP: rtsp://username:password@host:port/path
            protocol = url.split('://')[0]
            rest = url.split('://', 1)[1]
            url = f"{protocol}://{self.camera_source.stream_username}:{self.camera_source.stream_password}@{rest}"
        
        return url
    
    def _stream_loop(self):
        """Main streaming loop running in background thread."""
        stream_url = self._build_stream_url()
        logger.info(f"Connecting to stream: {stream_url.split('@')[-1] if '@' in stream_url else stream_url}")
        
        # Try to open stream
        try:
            self.capture = cv2.VideoCapture(stream_url)
            
            # Set buffer size to 1 to minimize latency
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.capture.isOpened():
                logger.error(f"Failed to open stream: {stream_url}")
                self.is_running = False
                return
            
            logger.info(f"Stream opened successfully for camera {self.camera_source.name}")
            
            # Update camera status
            from django.utils import timezone
            self.camera_source.status = 'active'
            self.camera_source.last_connected = timezone.now()
            self.camera_source.save()
            
            consecutive_failures = 0
            max_failures = 30  # Stop after 30 consecutive failures
            
            while self.is_running:
                # Respect FPS limit
                current_time = time.time()
                time_since_last_frame = current_time - self.last_frame_time
                
                if time_since_last_frame < self.frame_interval:
                    time.sleep(self.frame_interval - time_since_last_frame)
                    continue
                
                # Read frame
                ret, frame = self.capture.read()
                
                if not ret or frame is None:
                    consecutive_failures += 1
                    logger.warning(f"Failed to read frame from camera {self.camera_source.name} (attempt {consecutive_failures})")
                    
                    if consecutive_failures >= max_failures:
                        logger.error(f"Too many failures, stopping stream for camera {self.camera_source.name}")
                        break
                    
                    time.sleep(1)  # Wait before retry
                    continue
                
                # Reset failure counter on success
                consecutive_failures = 0
                self.last_frame_time = current_time
                
                # Process and callback with frame
                try:
                    # Resize frame if needed (for quality setting)
                    if self.camera_source.stream_quality == 'low':
                        frame = cv2.resize(frame, (640, 480))
                    elif self.camera_source.stream_quality == 'medium':
                        frame = cv2.resize(frame, (1280, 720))
                    # high quality - keep original
                    
                    # Encode frame to JPEG
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Call callback with frame
                    if self.on_frame_callback:
                        from django.utils import timezone
                        self.on_frame_callback(frame_base64, timezone.now().isoformat())
                    
                except Exception as e:
                    logger.error(f"Error processing frame: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Stream error for camera {self.camera_source.name}: {e}")
        
        finally:
            # Cleanup
            if self.capture:
                self.capture.release()
            
            # Update camera status
            from django.utils import timezone
            self.camera_source.status = 'disconnected'
            self.camera_source.save()
            
            self.is_running = False
            logger.info(f"Stream loop ended for camera {self.camera_source.name}")
    
    def get_single_frame(self) -> Optional[bytes]:
        """
        Capture a single frame without starting continuous stream.
        Useful for testing or one-shot recognition.
        
        Returns:
            Frame as JPEG bytes or None if failed
        """
        if not HAS_CV2:
            return None
        
        stream_url = self._build_stream_url()
        
        try:
            cap = cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                return buffer.tobytes()
            
        except Exception as e:
            logger.error(f"Error capturing single frame: {e}")
        
        return None


# Global registry of active streams
_active_streams = {}


def start_wireless_camera_stream(camera_source, on_frame_callback: Optional[Callable] = None):
    """
    Start streaming from a wireless camera.
    
    Args:
        camera_source: ExternalCameraSource instance
        on_frame_callback: Optional callback for frames
        
    Returns:
        WirelessCameraStreamHandler instance or None if failed
    """
    camera_id = str(camera_source.id)
    
    # Stop existing stream if running
    if camera_id in _active_streams:
        logger.info(f"Stopping existing stream for camera {camera_id}")
        stop_wireless_camera_stream(camera_id)
    
    # Create and start new stream
    handler = WirelessCameraStreamHandler(camera_source, on_frame_callback)
    
    if handler.start():
        _active_streams[camera_id] = handler
        return handler
    
    return None


def stop_wireless_camera_stream(camera_id: str):
    """Stop streaming for a camera."""
    if camera_id in _active_streams:
        handler = _active_streams[camera_id]
        handler.stop()
        del _active_streams[camera_id]
        return True
    return False


def get_active_stream(camera_id: str) -> Optional[WirelessCameraStreamHandler]:
    """Get active stream handler for a camera."""
    return _active_streams.get(camera_id)


def stop_all_streams():
    """Stop all active streams (cleanup on shutdown)."""
    for camera_id in list(_active_streams.keys()):
        stop_wireless_camera_stream(camera_id)
