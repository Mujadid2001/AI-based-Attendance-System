import { useState, useRef, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { IoCamera, IoCheckmarkCircle, IoCloseCircle, IoCalendar } from 'react-icons/io5'
import { Card, Button, Badge } from '@components/ui'
import { aiService } from '@services/index'
import toast from 'react-hot-toast'
import Webcam from 'react-webcam'

const FaceRecognition = () => {
  const webcamRef = useRef<Webcam>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [recognitionResult, setRecognitionResult] = useState<any>(null)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)

  const captureAndRecognize = useCallback(async () => {
    const imageSrc = webcamRef.current?.getScreenshot()
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
  }, [])

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Camera View */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">Camera</h2>
          <div className="relative">
            {!capturedImage ? (
              <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  className="w-full h-full object-cover"
                  mirrored
                />
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
      </Card>
    </div>
  )
}

export default FaceRecognition
