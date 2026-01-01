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
    device_type: 'mobile' as 'mobile' | 'tablet' | 'webcam' | 'other',
    auto_mark_attendance: false
  })

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
        auto_mark_attendance: false
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
      case 'mobile':
        return <IoPhonePortrait className="w-5 h-5" />
      case 'tablet':
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
                    <span className="font-medium capitalize">{camera.device_type}</span>
                  </div>
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
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => showQRCode(camera)}
                    fullWidth
                  >
                    <IoQrCode className="w-4 h-4 mr-2" />
                    QR Code
                  </Button>
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
            </label>
            <input
              type="text"
              value={formData.device_id}
              onChange={(e) => setFormData({ ...formData, device_id: e.target.value })}
              className="input"
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
