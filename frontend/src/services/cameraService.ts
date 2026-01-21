import api from './api';

export interface ExternalCamera {
  id: string;
  name: string;
  device_id: string;
  device_type: 'mobile' | 'tablet' | 'webcam' | 'ip_camera' | 'rtsp' | 'http_stream' | 'other';
  status: 'active' | 'inactive' | 'disconnected';
  is_enabled: boolean;
  auto_mark_attendance: boolean;
  created_by: number;
  created_by_username: string;
  created_by_name: string;
  last_connected: string | null;
  created_at: string;
  updated_at: string;
  qr_code_url: string;
  camera_url: string;
  session_count: number;
  stream_url?: string;
  stream_username?: string;
  stream_protocol?: 'rtsp' | 'http' | 'https' | 'upload';
  stream_quality?: 'high' | 'medium' | 'low';
  fps_limit?: number;
  is_wireless_camera?: boolean;
}

export interface CameraStreamSession {
  id: string;
  camera_source: string;
  camera_name: string;
  attendance_session: number | null;
  attendance_session_name: string | null;
  started_at: string;
  ended_at: string | null;
  frames_received: number;
  faces_detected: number;
  faces_recognized: number;
  attendance_marked: number;
  duration: number | null;
}

export interface CreateCameraData {
  name: string;
  device_id: string;
  device_type: 'mobile' | 'tablet' | 'webcam' | 'ip_camera' | 'rtsp' | 'http_stream' | 'other';
  auto_mark_attendance?: boolean;
  stream_url?: string;
  stream_username?: string;
  stream_password?: string;
  stream_protocol?: 'rtsp' | 'http' | 'https' | 'upload';
  stream_quality?: 'high' | 'medium' | 'low';
  fps_limit?: number;
}

class CameraService {
  /**
   * Get all camera sources
   */
  async getCameras(): Promise<ExternalCamera[]> {
    const response = await api.get('/camera/sources/');
    // Handle paginated response
    return response.data.results || response.data;
  }

  /**
   * Get single camera source
   */
  async getCamera(id: string): Promise<ExternalCamera> {
    const response = await api.get(`/camera/sources/${id}/`);
    return response.data;
  }

  /**
   * Create new camera source
   */
  async createCamera(data: CreateCameraData): Promise<ExternalCamera> {
    const response = await api.post('/camera/sources/', data);
    return response.data;
  }

  /**
   * Update camera source
   */
  async updateCamera(id: string, data: Partial<CreateCameraData>): Promise<ExternalCamera> {
    const response = await api.patch(`/camera/sources/${id}/`, data);
    return response.data;
  }

  /**
   * Delete camera source
   */
  async deleteCamera(id: string): Promise<void> {
    await api.delete(`/camera/sources/${id}/`);
  }

  /**
   * Toggle camera enabled/disabled
   */
  async toggleCamera(id: string): Promise<{ message: string; is_enabled: boolean }> {
    const response = await api.post(`/camera/sources/${id}/toggle-status/`);
    return response.data;
  }

  /**
   * Get QR code for camera
   */
  getQRCodeUrl(id: string): string {
    return `${api.defaults.baseURL}/camera/sources/${id}/qr-code/`;
  }

  /**
   * Start camera session
   */
  async startSession(cameraId: string, attendanceSessionId?: number): Promise<CameraStreamSession> {
    const response = await api.post(`/camera/sources/${cameraId}/start-session/`, {
      attendance_session_id: attendanceSessionId
    });
    return response.data;
  }

  /**
   * End camera session
   */
  async endSession(cameraId: string, sessionId?: string): Promise<any> {
    const response = await api.post(`/camera/sources/${cameraId}/end-session/`, {
      session_id: sessionId
    });
    return response.data;
  }

  /**
   * Get camera sessions
   */
  async getSessions(cameraId?: string): Promise<CameraStreamSession[]> {
    const params = cameraId ? { camera_id: cameraId } : {};
    const response = await api.get('/camera/sources/sessions/', { params });
    return response.data;
  }

  /**
   * Upload frame from external camera
   */
  async uploadFrame(
    image: File, 
    accessToken: string, 
    sessionId?: string,
    attendanceSessionId?: number
  ): Promise<any> {
    const formData = new FormData();
    formData.append('image', image);
    formData.append('access_token', accessToken);
    if (sessionId) formData.append('session_id', sessionId);
    if (attendanceSessionId) formData.append('attendance_session_id', attendanceSessionId.toString());
    formData.append('timestamp', new Date().toISOString());

    const response = await api.post('/camera/sources/upload-frame/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * Get latest frame from mobile camera for live streaming

  /**
   * Start wireless camera stream
   */
  async startWirelessStream(cameraId: string): Promise<any> {
    const response = await api.post(`/camera/sources/${cameraId}/start-stream/`);
    return response.data;
  }

  /**
   * Stop wireless camera stream
   */
  async stopWirelessStream(cameraId: string): Promise<any> {
    const response = await api.post(`/camera/sources/${cameraId}/stop-stream/`);
    return response.data;
  }

  /**
   * Get wireless camera stream status
   */
  async getStreamStatus(cameraId: string): Promise<any> {
    const response = await api.get(`/camera/sources/${cameraId}/stream-status/`);
    return response.data;
  }

  /**
   * Test wireless camera connection
   */
  async testConnection(cameraId: string): Promise<any> {
    const response = await api.post(`/camera/sources/${cameraId}/test-connection/`);
    return response.data;
  }
   * Returns a URL that can be used as an image src
   */
  getLatestFrameUrl(cameraId: string): string {
    const token = localStorage.getItem('accessToken');
    return `${api.defaults.baseURL}/camera/sources/${cameraId}/latest-frame/?t=${Date.now()}&token=${token}`;
  }
}

export const cameraService = new CameraService();
