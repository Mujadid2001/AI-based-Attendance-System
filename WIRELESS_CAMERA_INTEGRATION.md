# Wireless/IP Camera Integration Guide

## Overview
The AI-Based Attendance System now supports external wireless cameras including IP cameras, RTSP streams, and HTTP/MJPEG streams in addition to mobile devices.

## Supported Camera Types

### 1. Mobile/Tablet Devices
- Upload frames via mobile web interface
- QR code pairing for easy setup
- Manual frame upload

### 2. IP Cameras
- Wired/wireless IP cameras with network access
- ONVIF-compatible cameras
- Custom IP camera solutions

### 3. RTSP Streams
- Real-Time Streaming Protocol
- Common format: `rtsp://192.168.1.100:554/stream`
- Supports authentication
- Low latency streaming

### 4. HTTP/MJPEG Streams
- Motion JPEG over HTTP/HTTPS
- Common format: `http://192.168.1.100/video`
- Web-based camera streams

## Backend Implementation

### New Model Fields
```python
# ExternalCameraSource model additions
stream_url = models.URLField()          # Camera stream URL
stream_username = models.CharField()     # Authentication username
stream_password = models.CharField()     # Authentication password
stream_protocol = models.CharField()     # rtsp, http, https, upload
stream_quality = models.CharField()      # high, medium, low
fps_limit = models.IntegerField()        # 1-30 FPS
```

### Stream Handler Service
- **Location**: `apps/camera_integration/stream_handler.py`
- **Features**:
  - Background thread streaming
  - OpenCV-based frame capture
  - Automatic reconnection
  - FPS limiting
  - Quality/resolution control
  - Authentication support

### New API Endpoints

#### Start Wireless Stream
```
POST /api/camera/sources/{id}/start-stream/
```
Starts continuous streaming from a wireless camera.

**Response**:
```json
{
  "message": "Stream started successfully",
  "camera_id": "uuid",
  "camera_name": "Office Camera",
  "fps_limit": 5
}
```

#### Stop Wireless Stream
```
POST /api/camera/sources/{id}/stop-stream/
```
Stops streaming from a wireless camera.

#### Stream Status
```
GET /api/camera/sources/{id}/stream-status/
```
Get current streaming status.

**Response**:
```json
{
  "camera_id": "uuid",
  "is_streaming": true,
  "device_type": "ip_camera",
  "stream_url": "rtsp://192.168.1.100:554/stream",
  "fps_limit": 5,
  "stream_quality": "medium"
}
```

#### Test Connection
```
POST /api/camera/sources/{id}/test-connection/
```
Test camera connection and capture a single frame.

**Response**:
```json
{
  "success": true,
  "message": "Connection successful",
  "frame": "base64_encoded_image",
  "camera_id": "uuid"
}
```

## Frontend Implementation

### Camera Creation Form
New fields for wireless cameras:
- **Stream URL**: Camera endpoint URL
- **Stream Protocol**: RTSP, HTTP, HTTPS
- **Stream Quality**: High/Medium/Low (resolution)
- **FPS Limit**: Frame rate (1-30 FPS)
- **Authentication**: Username/password (optional)

### Camera Types UI
- Mobile/Tablet: Shows QR code button
- Wireless cameras: Shows "Test" button
- Different icons for each type

### Integration with Face Recognition
- Wireless cameras stream directly to recognition page
- Same WebSocket/polling architecture
- Automatic frame broadcasting to connected clients

## Setup Examples

### Example 1: Basic IP Camera (No Auth)
```json
{
  "name": "Office IP Camera",
  "device_id": "office-cam-01",
  "device_type": "ip_camera",
  "stream_url": "http://192.168.1.100/video",
  "stream_protocol": "http",
  "stream_quality": "medium",
  "fps_limit": 5
}
```

### Example 2: RTSP Camera with Authentication
```json
{
  "name": "Entrance RTSP Camera",
  "device_id": "entrance-cam-01",
  "device_type": "rtsp",
  "stream_url": "rtsp://192.168.1.101:554/stream",
  "stream_username": "admin",
  "stream_password": "password123",
  "stream_protocol": "rtsp",
  "stream_quality": "high",
  "fps_limit": 10
}
```

### Example 3: HTTP/MJPEG Stream
```json
{
  "name": "Lab Webcam",
  "device_id": "lab-webcam-01",
  "device_type": "http_stream",
  "stream_url": "http://192.168.1.102:8080/video",
  "stream_protocol": "http",
  "stream_quality": "low",
  "fps_limit": 5
}
```

## Usage Workflow

### 1. Add Wireless Camera
1. Navigate to "External Cameras"
2. Click "Add Camera"
3. Select device type (IP Camera, RTSP, HTTP Stream)
4. Fill in stream URL and credentials
5. Configure quality and FPS settings
6. Click "Create Camera"

### 2. Test Connection
1. Click "Test" button on camera card
2. System attempts to capture a single frame
3. Success/failure message displayed
4. Verifies URL, credentials, and connectivity

### 3. Start Streaming
1. Navigate to "Face Recognition"
2. Select "Mobile Camera" source
3. Choose wireless camera from dropdown
4. System starts background streaming
5. Frames appear in real-time view

### 4. Face Recognition
- Streaming frames automatically available
- Same recognition workflow as mobile cameras
- Real-time results broadcast to all connected clients
- Supports auto-attendance marking

## Technical Details

### Stream Handler Architecture
```python
class WirelessCameraStreamHandler:
    - Runs in background thread (daemon)
    - Uses OpenCV VideoCapture for stream reading
    - Respects FPS limit via frame_interval
    - Automatic reconnection on failure (max 30 attempts)
    - Encodes frames to JPEG with quality control
    - Calls callback for each frame
    - Updates camera status in database
```

### Performance Optimization
- **FPS Limiting**: Prevents server overload (recommended 5-10 FPS)
- **Quality Control**: 
  - Low: 640x480
  - Medium: 1280x720
  - High: Original resolution
- **Buffer Size**: Minimized for low latency (buffer=1)
- **Frame Compression**: JPEG quality 85%

### Error Handling
- Consecutive failure tracking
- Automatic stream disconnection after 30 failures
- Status updates (active → disconnected)
- Detailed logging for debugging

## Dependencies

### Backend
```python
opencv-python>=4.8.1    # Video capture and processing
numpy>=1.26.4           # Frame manipulation
```

### System Requirements
- OpenCV with video support
- Network access to cameras
- Sufficient CPU for frame processing
- Recommended: 2+ CPU cores for multiple streams

## Security Considerations

1. **Credentials Storage**
   - Passwords stored in database (consider encryption)
   - Not exposed in API responses (write_only)

2. **Network Security**
   - Use HTTPS for HTTP streams when possible
   - Keep cameras on isolated VLAN
   - Regular firmware updates

3. **Access Control**
   - Only Admin/Teacher can add cameras
   - Camera access controlled by is_enabled flag
   - Stream sessions tracked for auditing

## Troubleshooting

### Connection Failures
- **Check URL format**: Ensure correct protocol and path
- **Test network access**: Ping camera IP from server
- **Verify credentials**: Test username/password manually
- **Check firewall**: Ensure port access (554 for RTSP, etc.)

### Stream Drops
- **Network stability**: Check WiFi signal strength
- **Camera settings**: Verify stream resolution/bitrate
- **FPS too high**: Reduce fps_limit to 5 or lower
- **Server load**: Monitor CPU usage, reduce concurrent streams

### Quality Issues
- **Resolution mismatch**: Adjust stream_quality setting
- **Bandwidth limitations**: Lower FPS or quality
- **Camera settings**: Configure camera for optimal output

## Future Enhancements

- [ ] Stream encryption support
- [ ] Multiple stream endpoints per camera
- [ ] PTZ (Pan-Tilt-Zoom) control
- [ ] Motion detection triggers
- [ ] Recording/playback functionality
- [ ] Camera groups for synchronized recognition
- [ ] Load balancing across servers
- [ ] Hardware acceleration (GPU/VPU)

## Migration

To apply database changes:
```bash
python manage.py migrate camera_integration
```

This adds the new fields for wireless camera support to existing installations.
