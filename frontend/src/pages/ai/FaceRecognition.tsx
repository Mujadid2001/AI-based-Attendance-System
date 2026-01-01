import { useState, useRef, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { IoCamera, IoCheckmarkCircle, IoCloseCircle, IoCalendar, IoPhonePortrait, IoDesktop, IoQrCode } from 'react-icons/io5'
import { Card, Button, Badge, Modal } from '@components/ui'
import { aiService, cameraService, ExternalCamera } from '@services/index'
import toast from 'react-hot-toast'
import Webcam from 'react-webcam'

type CameraSource = 'webcam' | 'mobile'

const FaceRecognition = () => {
  const webcamRef = useRef<Webcam>(null)
  const mobileFrameRef = useRef<HTMLImageElement>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [recognitionResult, setRecognitionResult] = useState<any>(null)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [cameraSource, setCameraSource] = useState<CameraSource>('webcam')
  const [mobileCameras, setMobileCameras] = useState<ExternalCamera[]>([])
  const [selectedMobileCamera, setSelectedMobileCamera] = useState<ExternalCamera | null>(null)
  const [showQRModal, setShowQRModal] = useState(false)
  const [mobileFrameUrl, setMobileFrameUrl] = useState<string | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const websocketRef = useRef<WebSocket | null>(null)
  const [useWebSocket, setUseWebSocket] = useState(true) // Prefer WebSocket over polling

  useEffect(() => {
    loadMobileCameras()
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
      if (websocketRef.current) {
        websocketRef.current.close()
      }
    }
  }, [])

  const loadMobileCameras = async () => {
    try {
      const cameras = await cameraService.getCameras()
      const activeCameras = Array.isArray(cameras) ? cameras.filter(c => c.is_enabled) : []
      setMobileCameras(activeCameras)
    } catch (error) {
      console.error('Failed to load cameras:', error)
    }
  }

  const startMobileCameraPolling = (cameraId: string) => {
    // Stop any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
    }

    // Poll for latest frame every 500ms for smooth streaming
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const frameUrl = cameraService.getLatestFrameUrl(cameraId)
        
        // Fetch the frame/result
        const response = await fetch(frameUrl)
        
        // Check if response is JSON (recognition result) or image
        const contentType = response.headers.get('content-type')
        
        if (contentType?.includes('application/json')) {
          // Recognition result received via polling!
          const data = await response.json()
          
          // Stop processing state if it was set
          setIsProcessing(false)
          
          // Set captured image
          if (data.captured_image) {
            setCapturedImage(`data:image/jpeg;base64,${data.captured_image}`)
          }
          
          // Transform and display result
          const transformedResult = {
            recognized: data.success,
            student_name: data.student?.name || 'Unknown',
            student_id: data.student?.roll_number || 'N/A',
            confidence: Math.round((data.confidence || 0) * 100),
            message: data.message || (data.success ? 'Face recognized successfully' : 'Face not recognized')
          }
          
          setRecognitionResult(transformedResult)
          
          // Show toast notification on laptop
          if (data.success) {
            toast.success(`📱 Mobile: Recognized ${transformedResult.student_name}`)
          } else {
            toast.error(`📱 Mobile: ${data.error || 'Face not recognized'}`)
          }
        } else if (response.status === 200) {
          // Regular frame image
          setMobileFrameUrl(frameUrl)
        }
        // 204 = no content, just continue polling
      } catch (error) {
        console.error('Failed to fetch mobile frame:', error)
      }
    }, 500)
  }

  const stopMobileCameraPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    setMobileFrameUrl(null)
  }

  const connectWebSocket = (cameraId: string) => {
    // Close existing connection
    if (websocketRef.current) {
      websocketRef.current.close()
    }

    // Get WebSocket URL (convert http/https to ws/wss)
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const wsProtocol = apiUrl.startsWith('https') ? 'wss' : 'ws'
    const wsHost = apiUrl.replace(/^https?:\/\//, '')
    const wsUrl = `${wsProtocol}://${wsHost}/ws/camera/${cameraId}/`

    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      toast.success('Connected to mobile camera')
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        // Handle real-time frame updates
        if (data.type === 'frame' && data.frame) {
          setMobileFrameUrl(`data:image/jpeg;base64,${data.frame}`)
        }
        
        // Handle recognition results from mobile capture
        if (data.type === 'recognition_result') {
          // Stop processing state if it was set
          setIsProcessing(false)
          
          // Set captured image - this displays the captured photo on laptop
          if (data.captured_image) {
            setCapturedImage(`data:image/jpeg;base64,${data.captured_image}`)
          }
          
          // Transform and display result in the same format as webcam results
          const transformedResult = {
            recognized: data.success,
            student_name: data.student?.name || 'Unknown',
            student_id: data.student?.roll_number || 'N/A',
            confidence: Math.round((data.confidence || 0) * 100),
            message: data.message || (data.success ? 'Face recognized successfully' : 'Face not recognized')
          }
          
          setRecognitionResult(transformedResult)
          
          // Show toast notification on laptop
          if (data.success) {
            toast.success(`📱 Mobile: Recognized ${transformedResult.student_name}`)
          } else {
            toast.error(`📱 Mobile: ${data.error || 'Face not recognized'}`)
          }
        }
      } catch (error) {
        console.error('WebSocket message error:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      toast.error('Camera connection error. Falling back to polling...')
      // Fallback to HTTP polling
      setUseWebSocket(false)
      startMobileCameraPolling(cameraId)
    }
    
    ws.onclose = () => {
      // WebSocket disconnected
    }

    websocketRef.current = ws
  }

  const disconnectWebSocket = () => {
    if (websocketRef.current) {
      websocketRef.current.close()
      websocketRef.current = null
    }
    setMobileFrameUrl(null)
  }

  const handleCameraSourceChange = (source: CameraSource) => {
    setCameraSource(source)
    setCapturedImage(null)
    setRecognitionResult(null)
    
    if (source === 'mobile') {
      if (mobileCameras.length === 0) {
        toast.error('No mobile cameras available. Please add one first.')
        setCameraSource('webcam')
      } else if (mobileCameras.length === 1) {
        setSelectedMobileCamera(mobileCameras[0])
        // Try WebSocket first, fallback to polling if it fails
        if (useWebSocket) {
          connectWebSocket(mobileCameras[0].id)
        } else {
          startMobileCameraPolling(mobileCameras[0].id)
        }
      }
    } else {
      // Cleanup when switching away from mobile
      stopMobileCameraPolling()
      disconnectWebSocket()
      setSelectedMobileCamera(null)
    }
  }

  const handleMobileCameraSelect = (camera: ExternalCamera) => {
    setSelectedMobileCamera(camera)
    // Try WebSocket first, fallback to polling if it fails
    if (useWebSocket) {
      connectWebSocket(camera.id)
    } else {
      startMobileCameraPolling(camera.id)
    }
  }

  const captureAndRecognize = useCallback(async () => {
    // Only allow laptop-initiated capture for webcam source
    // For mobile camera, recognition is triggered from the mobile device
    if (cameraSource === 'mobile') {
      toast.info('📱 Please use the Capture button on your mobile device')
      return
    }

    let imageSrc: string | null = null

    if (cameraSource === 'webcam') {
      imageSrc = webcamRef.current?.getScreenshot() || null
    }

    if (!imageSrc) {
      toast.error('Failed to capture image')
      return
    }

    setCapturedImage(imageSrc)
    setIsProcessing(true)

    try {
      // Convert base64 to file
      const blob = await fetch(imageSrc).then((res) => res.blob())
      const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' })

      // Recognize face
      const result = await aiService.recognizeFace(file)
      
      // Transform API response to match UI expectations
      const transformedResult = {
        recognized: result.message === 'Face recognized successfully.',
        student_name: result.student?.name || 'Unknown',
        student_id: result.student?.roll_number || 'N/A',
        confidence: Math.round((result.confidence || 0) * 100),
        message: result.message || 'Recognition complete'
      }
      
      setRecognitionResult(transformedResult)

      if (transformedResult.recognized) {
        toast.success(`Recognized: ${transformedResult.student_name}`)
      } else {
        toast.error('Face not recognized')
      }
    } catch (error: any) {
      console.error('Recognition error:', error)
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Recognition failed'
      toast.error(errorMsg)
      setRecognitionResult({
        recognized: false,
        message: errorMsg,
        confidence: 0
      })
    } finally {
      setIsProcessing(false)
    }
  }, [cameraSource, mobileFrameUrl])

  const reset = () => {
    setCapturedImage(null)
    setRecognitionResult(null)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Face Recognition</h1>
          <p className="text-gray-600 mt-1">Mark attendance using AI-powered face recognition</p>
        </div>
        <Link to="/attendance">
          <Button variant="secondary">
            <IoCalendar className="w-5 h-5 mr-2" />
            View Sessions
          </Button>
        </Link>
      </div>

      {/* Camera Source Selector */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Camera Source</h2>
        <div className="flex gap-4">
          <Button
            variant={cameraSource === 'webcam' ? 'primary' : 'outline'}
            onClick={() => handleCameraSourceChange('webcam')}
            className="flex-1"
          >
            <IoDesktop className="w-5 h-5 mr-2" />
            Laptop Webcam
          </Button>
          <Button
            variant={cameraSource === 'mobile' ? 'primary' : 'outline'}
            onClick={() => handleCameraSourceChange('mobile')}
            className="flex-1"
          >
            <IoPhonePortrait className="w-5 h-5 mr-2" />
            Mobile Camera
          </Button>
        </div>

        {cameraSource === 'mobile' && mobileCameras.length > 1 && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Mobile Camera
            </label>
            <select
              value={selectedMobileCamera?.id || ''}
              onChange={(e) => {
                const camera = mobileCameras.find(c => c.id === e.target.value)
                if (camera) handleMobileCameraSelect(camera)
              }}
              className="input"
            >
              {mobileCameras.map(camera => (
                <option key={camera.id} value={camera.id}>
                  {camera.name} ({camera.status})
                </option>
              ))}
            </select>
          </div>
        )}

        {cameraSource === 'mobile' && selectedMobileCamera && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-900">
                  Connected: {selectedMobileCamera.name}
                </p>
                <p className="text-xs text-blue-700 mt-1">
                  {selectedMobileCamera.status === 'active' ? '🟢 Active' : '🔴 Inactive'}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowQRModal(true)}
              >
                <IoQrCode className="w-4 h-4 mr-2" />
                Show QR
              </Button>
            </div>
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Camera View */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">Camera</h2>
          <div className="relative">
            {!capturedImage ? (
              <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden">
                {cameraSource === 'webcam' ? (
                  <Webcam
                    ref={webcamRef}
                    audio={false}
                    screenshotFormat="image/jpeg"
                    className="w-full h-full object-cover"
                    mirrored
                  />
                ) : (
                  mobileFrameUrl ? (
                    <img
                      ref={mobileFrameRef}
                      src={mobileFrameUrl}
                      alt="Mobile Camera Feed"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-white">
                      <div className="text-center">
                        <IoPhonePortrait className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p>Waiting for mobile camera...</p>
                        <p className="text-sm mt-2 opacity-75">Open camera on your phone</p>
                      </div>
                    </div>
                  )
                )}
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="aspect-video bg-gray-900 rounded-lg overflow-hidden"
              >
                <img
                  src={capturedImage}
                  alt="Captured"
                  className="w-full h-full object-cover"
                />
              </motion.div>
            )}
          </div>

          <div className="mt-4 flex gap-4">
            {!capturedImage ? (
              <>
                {cameraSource === 'webcam' ? (
                  <Button
                    onClick={captureAndRecognize}
                    isLoading={isProcessing}
                    fullWidth
                    size="lg"
                  >
                    <IoCamera className="w-5 h-5 mr-2" />
                    Capture & Recognize
                  </Button>
                ) : (
                  <div className="w-full p-4 bg-blue-50 border-2 border-blue-300 rounded-lg text-center">
                    <IoPhonePortrait className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                    <p className="text-blue-900 font-semibold">Mobile Camera Mode</p>
                    <p className="text-blue-700 text-sm mt-1">
                      Use the "Capture & Recognize" button on your mobile device
                    </p>
                    <p className="text-blue-600 text-xs mt-2">
                      Results will appear here automatically
                    </p>
                  </div>
                )}
              </>
            ) : (
              <Button onClick={reset} variant="outline" fullWidth size="lg">
                Take Another Photo
              </Button>
            )}
          </div>
        </Card>

        {/* Recognition Result */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">Recognition Result</h2>
          
          {!recognitionResult ? (
            <div className="flex items-center justify-center h-64 text-gray-400">
              <div className="text-center">
                <IoCamera className="w-16 h-16 mx-auto mb-4" />
                <p>No recognition result yet</p>
                <p className="text-sm mt-2">Capture an image to start</p>
              </div>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-6"
            >
              {/* Status */}
              <div
                className={`p-6 rounded-xl ${
                  recognitionResult.recognized
                    ? 'bg-green-50 border-2 border-green-500'
                    : 'bg-red-50 border-2 border-red-500'
                }`}
              >
                <div className="flex items-center gap-4">
                  {recognitionResult.recognized ? (
                    <IoCheckmarkCircle className="w-12 h-12 text-green-600" />
                  ) : (
                    <IoCloseCircle className="w-12 h-12 text-red-600" />
                  )}
                  <div>
                    <h3
                      className={`text-2xl font-bold ${
                        recognitionResult.recognized ? 'text-green-900' : 'text-red-900'
                      }`}
                    >
                      {recognitionResult.recognized ? 'Recognized' : 'Not Recognized'}
                    </h3>
                    <p
                      className={
                        recognitionResult.recognized ? 'text-green-700' : 'text-red-700'
                      }
                    >
                      {recognitionResult.message}
                    </p>
                  </div>
                </div>
              </div>

              {/* Student Info */}
              {recognitionResult.recognized && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Student Name</label>
                    <p className="text-lg font-semibold text-gray-900">
                      {recognitionResult.student_name}
                    </p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-600">Roll Number</label>
                    <p className="text-lg font-semibold text-gray-900">
                      {recognitionResult.student_id}
                    </p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">Confidence</label>
                    <div className="flex items-center gap-3 mt-1">
                      <div className="flex-1 bg-gray-200 rounded-full h-3">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${recognitionResult.confidence}%` }}
                          className={`h-3 rounded-full ${
                            recognitionResult.confidence > 80
                              ? 'bg-green-500'
                              : recognitionResult.confidence > 60
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                        />
                      </div>
                      <span className="text-sm font-semibold">
                        {recognitionResult.confidence}%
                      </span>
                    </div>
                  </div>

                  <Badge
                    variant={recognitionResult.confidence > 80 ? 'success' : 'warning'}
                    size="lg"
                  >
                    {recognitionResult.confidence > 80 ? 'High Confidence' : 'Medium Confidence'}
                  </Badge>
                </div>
              )}
            </motion.div>
          )}
        </Card>
      </div>

      {/* Instructions */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Instructions</h2>
        {cameraSource === 'webcam' ? (
          <ul className="space-y-2 text-gray-600">
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">1.</span>
              <span>Position your face clearly in front of the camera</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">2.</span>
              <span>Ensure good lighting conditions</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">3.</span>
              <span>Look directly at the camera</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">4.</span>
              <span>Click "Capture & Recognize" to start face recognition</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary-600 font-bold">5.</span>
              <span>The system will automatically identify you and mark attendance</span>
            </li>
          </ul>
        ) : (
          <ul className="space-y-2 text-gray-600">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">📱</span>
              <span>
                <strong>Mobile Camera Mode:</strong> Your phone acts as an external camera
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">1.</span>
              <span>Open the camera interface on your mobile device (scan QR code)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">2.</span>
              <span>Position your face clearly and ensure good lighting</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">3.</span>
              <span>
                Click <strong>"Capture & Recognize"</strong> on your mobile device
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">4.</span>
              <span>
                Results will automatically appear on this laptop screen in real-time
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">✨</span>
              <span className="text-sm">
                Live video feed is streamed to laptop, but capture happens on mobile
              </span>
            </li>
          </ul>
        )}
      </Card>

      {/* QR Code Modal */}
      {selectedMobileCamera && (
        <Modal
          isOpen={showQRModal}
          onClose={() => setShowQRModal(false)}
          title="Mobile Camera QR Code"
        >
          <div className="space-y-4">
            <p className="text-gray-600">
              Scan this QR code with {selectedMobileCamera.name} to start streaming
            </p>
            <div className="flex justify-center p-4 bg-gray-50 rounded-lg">
              <img
                src={cameraService.getQRCodeUrl(selectedMobileCamera.id)}
                alt="QR Code"
                className="w-64 h-64"
              />
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

export default FaceRecognition
