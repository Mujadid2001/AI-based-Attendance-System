import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  IoCamera, IoAdd, IoQrCode, IoTrash, IoToggle, 
  IoCheckmarkCircle, IoCloseCircle, IoPhonePortrait,
  IoDesktop, IoTabletPortrait, IoEllipsisHorizontal
} from 'react-icons/io5'
import { Card, Button, Badge, Modal } from '@components/ui'
import { cameraService, ExternalCamera } from '@services/index'
import toast from 'react-hot-toast'

const ExternalCameras = () => {
  const [cameras, setCameras] = useState<ExternalCamera[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedCamera, setSelectedCamera] = useState<ExternalCamera | null>(null)
  const [showQRModal, setShowQRModal] = useState(false)
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    device_id: '',
    device_type: 'mobile' as 'mobile' | 'tablet' | 'webcam' | 'ip_camera' | 'rtsp' | 'http_stream' | 'other',
    auto_mark_attendance: false,
    stream_url: '',
    stream_username: '',
    stream_password: '',
    stream_protocol: 'upload' as 'rtsp' | 'http' | 'https' | 'upload',
    stream_quality: 'medium' as 'high' | 'medium' | 'low',
    fps_limit: 5
  })
  
  const isWirelessCamera = ['ip_camera', 'rtsp', 'http_stream'].includes(formData.device_type)

  useEffect(() => {
    loadCameras()
  }, [])

  const loadCameras = async () => {
    try {
      setLoading(true)
      const data = await cameraService.getCameras()
      setCameras(Array.isArray(data) ? data : [])
    } catch (error: any) {
      toast.error('Failed to load cameras')
      console.error(error)
      setCameras([])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await cameraService.createCamera(formData)
      toast.success('Camera source created successfully')
      setShowAddModal(false)
      setFormData({
        name: '',
        device_id: '',
        device_type: 'mobile',
        auto_mark_attendance: false,
        stream_url: '',
        stream_username: '',
        stream_password: '',
        stream_protocol: 'upload',
        stream_quality: 'medium',
        fps_limit: 5
      })
      loadCameras()
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to create camera')
    }
  }

  const handleDelete = async (camera: ExternalCamera) => {
    if (!confirm(`Delete camera "${camera.name}"?`)) return
    
    try {
      await cameraService.deleteCamera(camera.id)
      toast.success('Camera deleted')
      loadCameras()
    } catch (error) {
      toast.error('Failed to delete camera')
    }
  }

  const handleToggle = async (camera: ExternalCamera) => {
    try {
      await cameraService.toggleCamera(camera.id)
      toast.success(camera.is_enabled ? 'Camera disabled' : 'Camera enabled')
      loadCameras()
    } catch (error) {
      toast.error('Failed to toggle camera')
    }
  }

  const showQRCode = (camera: ExternalCamera) => {
    setSelectedCamera(camera)
    setShowQRModal(true)
  }

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'ip_camera':
      case 'rtsp':
      case 'http_stream':
        return <IoCamera className="w-5 h-5" />
      default:
        return <IoCamera className="w-5 h-5" />
    }
  }
  
  const getDeviceTypeName = (type: string) => {
    const names: Record<string, string> = {
      mobile: 'Mobile',
      tablet: 'Tablet',
      webcam: 'Webcam',
      ip_camera: 'IP Camera',
      rtsp: 'RTSP Stream',
      http_stream: 'HTTP Stream',
      other: 'Other'
    }
    return names[type] || type case 'tablet':
        return <IoTabletPortrait className="w-5 h-5" />
      case 'webcam':
        return <IoDesktop className="w-5 h-5" />
      default:
        return <IoCamera className="w-5 h-5" />
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'error'> = {
      active: 'success',
      inactive: 'warning',
      disconnected: 'error'
    }
    return <Badge variant={variants[status] || 'warning'}>{status}</Badge>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">External Cameras</h1>
          <p className="text-gray-600 mt-1">
            Manage mobile and external camera sources for attendance
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <IoAdd className="w-5 h-5 mr-2" />
          Add Camera
        </Button>
      </div>

      {/* Camera Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : cameras.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <IoCamera className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No cameras yet</h3>
            <p className="text-gray-600 mb-4">
              Add an external camera to get started with mobile attendance marking
            </p>
            <Button onClick={() => setShowAddModal(true)}>
              <IoAdd className="w-5 h-5 mr-2" />
              Add First Camera
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cameras.map((camera) => (
            <motion.div
              key={camera.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-primary-100 rounded-lg">
                      {getDeviceIcon(camera.device_type)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{camera.name}</h3>
                      <p className="text-sm text-gray-600">{camera.device_id}</p>
                    </div>
                  </div>
                  {getStatusBadge(camera.status)}
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Device Type</span>
                    <span className="font-medium">{getDeviceTypeName(camera.device_type)}</span>
                  </div>
                  {camera.is_wireless_camera && camera.stream_url && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Stream</span>
                      <span className="font-medium text-xs truncate max-w-[150px]" title={camera.stream_url}>
                        {camera.stream_url.split('://')[0].toUpperCase()}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Status</span>
                    <div className="flex items-center gap-2">
                      {camera.is_enabled ? (
                        <IoCheckmarkCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <IoCloseCircle className="w-4 h-4 text-red-600" />
                      )}
                      <span className="font-medium">
                        {camera.is_enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Auto Mark</span>
                    <span className="font-medium">
                      {camera.auto_mark_attendance ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Sessions</span>
                    <span className="font-medium">{camera.session_count}</span>
                  </div>
                </div>

                {camera.last_connected && (
                  <p className="text-xs text-gray-500 mb-4">
                    Last connected: {new Date(camera.last_connected).toLocaleString()}
                  </p>
                )}

                <div className="flex gap-2">
                  {!camera.is_wireless_camera ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => showQRCode(camera)}
                      fullWidth
                    >
                      <IoQrCode className="w-4 h-4 mr-2" />
                      QR Code
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        try {
                          const result = await cameraService.testConnection(camera.id)
                          if (result.success) {
                            toast.success('Connection successful!')
                          }
                        } catch (error: any) {
                          toast.error(error.response?.data?.error || 'Connection failed')
                        }
                      }}
                      fullWidth
                    >
                      Test
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleToggle(camera)}
                  >
                    <IoToggle className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(camera)}
                  >
                    <IoTrash className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Add Camera Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add External Camera"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Camera Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              required
              placeholder="e.g., Teacher Mobile"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Device ID
            </label> Device</option>
              <option value="tablet">Tablet</option>
              <option value="webcam">External Webcam</option>
              <option value="ip_camera">IP Camera / Wireless Camera</option>
              <option value="rtsp">RTSP Stream</option>
              <option value="http_stream">HTTP/MJPEG Stream</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Wireless Camera Fields */}
          {isWirelessCamera && (
            <>
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Stream Configuration</h4>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Stream URL *
                    </label>
                    <input
                      type="url"
                      value={formData.stream_url}
                      onChange={(e) => setFormData({ ...formData, stream_url: e.target.value })}
                      className="input"
                      required={isWirelessCamera}
                      placeholder="rtsp://192.168.1.100:554/stream or http://camera-ip/video"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Examples: rtsp://192.168.1.100:554/stream, http://192.168.1.100/video
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Stream Protocol
                      </label>
                      <select
                        value={formData.stream_protocol}
                        onChange={(e) => setFormData({ ...formData, stream_protocol: e.target.value as any })}
                        className="input"
                      >
                        <option value="rtsp">RTSP</option>
                        <option value="http">HTTP/MJPEG</option>
                        <option value="https">HTTPS</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Stream Quality
                      </label>
                      <select
                        value={formData.stream_quality}
                        onChange={(e) => setFormData({ ...formData, stream_quality: e.target.value as any })}
                        className="input"
                      >
                        <option value="low">Low (640x480)</option>
                        <option value="medium">Medium (1280x720)</option>
                        <option value="high">High (Original)</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      FPS Limit (1-30)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="30"
                      value={formData.fps_limit}
                      onChange={(e) => setFormData({ ...formData, fps_limit: parseInt(e.target.value) || 5 })}
                      className="input"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Lower FPS reduces server load. Recommended: 5-10 FPS
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Username (optional)
                    </label>
                    <input
                      type="text"
                      value={formData.stream_username}
                      onChange={(e) => setFormData({ ...formData, stream_username: e.target.value })}
                      className="input"
                      placeholder="Camera username"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Password (optional)
                    </label>
                    <input
                      type="password"
                      value={formData.stream_password}
                      onChange={(e) => setFormData({ ...formData, stream_password: e.target.value })}
                      className="input"
                      placeholder="Camera password"
                    />
                  </div>
                </div>
              </div>
            </>
          )}assName="input"
              required
              placeholder="e.g., mobile-001"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Device Type
            </label>
            <select
              value={formData.device_type}
              onChange={(e) => setFormData({ ...formData, device_type: e.target.value as any })}
              className="input"
            >
              <option value="mobile">Mobile</option>
              <option value="tablet">Tablet</option>
              <option value="webcam">Webcam</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="auto_mark"
              checked={formData.auto_mark_attendance}
              onChange={(e) => setFormData({ ...formData, auto_mark_attendance: e.target.checked })}
              className="rounded border-gray-300"
            />
            <label htmlFor="auto_mark" className="text-sm text-gray-700">
              Automatically mark attendance when face is recognized
            </label>
          </div>

          <div className="flex gap-3">
            <Button type="submit" fullWidth>
              Create Camera
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowAddModal(false)}
              fullWidth
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>

      {/* QR Code Modal */}
      <Modal
        isOpen={showQRModal}
        onClose={() => setShowQRModal(false)}
        title="Camera QR Code"
      >
        {selectedCamera && (
          <div className="space-y-4">
            <p className="text-gray-600">
              Scan this QR code with your mobile device to connect the camera
            </p>
            <div className="flex justify-center p-4 bg-gray-50 rounded-lg">
              <img
                src={cameraService.getQRCodeUrl(selectedCamera.id)}
                alt="QR Code"
                className="w-64 h-64"
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ExternalCameras
