import { useState, useRef, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useLocation, useNavigate } from 'react-router-dom'
import { IoCamera, IoCloudUpload, IoTrash, IoCheckmark, IoArrowBack } from 'react-icons/io5'
import { Card, Button, Input } from '@components/ui'
import { aiService } from '@services/index'
import toast from 'react-hot-toast'
import Webcam from 'react-webcam'

const MAX_IMAGES = 1

const FaceRegistration = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const prefilledRollNumber = location.state?.prefilledRollNumber || ''
  const studentEmail = location.state?.studentEmail || ''
  const studentName = location.state?.studentName || ''
  const isUpdate = location.state?.isUpdate || false // New prop to indicate update mode
  
  const webcamRef = useRef<Webcam>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [studentId, setStudentId] = useState(prefilledRollNumber)
  const [capturedImages, setCapturedImages] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const isPrefilledStudent = Boolean(prefilledRollNumber)

  useEffect(() => {
    if (prefilledRollNumber) {
      setStudentId(prefilledRollNumber)
    }
  }, [prefilledRollNumber])

  // Draw face guide overlay with enhanced guidance
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw enhanced face guides
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2.2  // Slightly higher for better positioning
    const radiusX = canvas.width * 0.25   // Good size for face positioning
    const radiusY = canvas.height * 0.35

    // Draw outer guide (recommended area)
    ctx.strokeStyle = '#10b981'
    ctx.lineWidth = 3
    ctx.setLineDash([])
    ctx.beginPath()
    ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI)
    ctx.stroke()

    // Draw inner guide (optimal area)
    ctx.strokeStyle = '#059669'
    ctx.lineWidth = 2
    ctx.setLineDash([5, 5])
    ctx.beginPath()
    ctx.ellipse(centerX, centerY, radiusX * 0.8, radiusY * 0.8, 0, 0, 2 * Math.PI)
    ctx.stroke()

    // Draw guidelines for facial feature positioning
    ctx.strokeStyle = '#10b981'
    ctx.lineWidth = 1
    ctx.setLineDash([3, 3])
    
    // Eye level line
    ctx.beginPath()
    ctx.moveTo(centerX - radiusX * 0.6, centerY - radiusY * 0.3)
    ctx.lineTo(centerX + radiusX * 0.6, centerY - radiusY * 0.3)
    ctx.stroke()
    
    // Nose level line  
    ctx.beginPath()
    ctx.moveTo(centerX - radiusX * 0.4, centerY)
    ctx.lineTo(centerX + radiusX * 0.4, centerY)
    ctx.stroke()

    // Enhanced instruction text
    ctx.fillStyle = '#10b981'
    ctx.font = 'bold 16px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Position your face in the green guides', centerX, 25)
    
    ctx.font = '12px sans-serif'
    ctx.fillStyle = '#059669'
    ctx.fillText('Keep eyes on top line, ensure good lighting', centerX, 45)
  }, [])

  const captureImage = useCallback(() => {
    if (capturedImages.length >= MAX_IMAGES) {
      toast.error(`Maximum ${MAX_IMAGES} images allowed`)
      return
    }

    const imageSrc = webcamRef.current?.getScreenshot()
    if (imageSrc) {
      setCapturedImages((prev) => [...prev, imageSrc])
      
      const nextImageCount = capturedImages.length + 1
      if (nextImageCount === 1) {
        toast.success('First image captured! Take 2-4 more from different angles')
      } else if (nextImageCount >= 3) {
        toast.success(`${nextImageCount} images captured - Ready to register!`)
      }
    } else {
      toast.error('Capture failed - Check lighting and try again')
    }
  }, [capturedImages.length])

  const removeImage = (index: number) => {
    setCapturedImages((prev) => prev.filter((_, i) => i !== index))
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    const remainingSlots = MAX_IMAGES - capturedImages.length
    if (remainingSlots <= 0) {
      toast.error(`Maximum ${MAX_IMAGES} images allowed`)
      return
    }

    const filesToProcess = Array.from(files).slice(0, remainingSlots)
    
    filesToProcess.forEach((file) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        if (e.target?.result) {
          setCapturedImages((prev) => {
            if (prev.length < MAX_IMAGES) {
              return [...prev, e.target!.result as string]
            }
            return prev
          })
        }
      }
      reader.readAsDataURL(file)
    })

    toast.success(`${filesToProcess.length} image(s) uploaded`)
    if (files.length > remainingSlots) {
      toast.error(`Only ${remainingSlots} slots available. Extra images ignored.`)
    }
  }

  const registerFace = async () => {
    if (!studentId) {
      toast.error('Please enter a roll number')
      return
    }

    if (capturedImages.length < 1) {
      toast.error('Please capture one image')
      return
    }

    setIsProcessing(true)
    toast.loading('Processing and checking for duplicates... This may take a moment')

    try {
      // Convert base64 images to files
      const files = await Promise.all(
        capturedImages.map(async (img, index) => {
          const blob = await fetch(img).then((res) => res.blob())
          return new File([blob], `face_${index}.jpg`, { type: 'image/jpeg' })
        })
      )

      // Since we only have 1 image now, simplify the logic
      const imageFile = files[0]
      
      // Call the appropriate API
      if (isUpdate) {
        await aiService.updateFace(studentId, [imageFile])
      } else {
        await aiService.registerFace(studentId, [imageFile])
      }
      
      // Success case - only reached if API call succeeds
      toast.dismiss()
      toast.success(`Face ${isUpdate ? 'updated' : 'registered'} successfully!`)
      setStudentId('')
      setCapturedImages([])
      
      if (prefilledRollNumber) {
        setTimeout(() => navigate(-1), 1000)
      }

    } catch (error: any) {
      // Handle all errors (file conversion or API errors)
      toast.dismiss()
      const errorMessage = error.response?.data?.error || error.message || 'Registration failed'
      
      // Check if it's a duplicate face error
      if (errorMessage.includes('already registered for another student')) {
        toast.error(`${errorMessage}`)
      } else {
        toast.error(`Registration failed: ${errorMessage}. Please try again with better lighting conditions.`)
      }
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isUpdate ? 'Update Face Registration' : 'Face Registration'}
          </h1>
          {isPrefilledStudent ? (
            <p className="text-gray-600 mt-1">
              {isUpdate ? 'Updating' : 'Registering'} face for: <span className="font-semibold text-gray-900">{studentName}</span> ({studentEmail})
            </p>
          ) : (
            <p className="text-gray-600 mt-1">
              {isUpdate ? 'Update student face for attendance recognition' : 'Register student faces for attendance recognition'}
            </p>
          )}
        </div>
        {isPrefilledStudent && (
          <Button variant="secondary" onClick={() => navigate(-1)}>
            <IoArrowBack className="w-5 h-5 mr-2" />
            Back to Student
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Camera View */}
        <Card className="lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">Camera</h2>
          <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden mb-4 relative">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              className="w-full h-full object-cover"
              mirrored
            />
            {/* Face guide overlay */}
            <canvas
              ref={canvasRef}
              width={640}
              height={480}
              className="absolute top-0 left-0 w-full h-full pointer-events-none"
            />
          </div>

          <div className="flex gap-4">
            <Button 
              onClick={captureImage} 
              fullWidth
              disabled={capturedImages.length >= MAX_IMAGES}
            >
              <IoCamera className="w-5 h-5 mr-2" />
              Capture Image ({capturedImages.length}/{MAX_IMAGES})
            </Button>
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              fullWidth
              disabled={capturedImages.length >= MAX_IMAGES}
            >
              <IoCloudUpload className="w-5 h-5 mr-2" />
              Upload Images
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        </Card>

        {/* Registration Form */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">Registration Info</h2>
          <div className="space-y-4">
            {isPrefilledStudent && studentEmail && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <span className="font-semibold">Student:</span> {studentName}
                </p>
                <p className="text-sm text-blue-800">
                  <span className="font-semibold">Email:</span> {studentEmail}
                </p>
              </div>
            )}
            <Input
              label="Roll Number"
              type="text"
              placeholder="Enter roll number"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              disabled={isPrefilledStudent}
              className={isPrefilledStudent ? 'bg-gray-100 cursor-not-allowed' : ''}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Images Captured
              </label>
              <div className="text-3xl font-bold text-primary-600">
                {capturedImages.length}/{MAX_IMAGES}
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {capturedImages.length < 1 
                  ? 'Capture one image to proceed'
                  : capturedImages.length >= MAX_IMAGES
                  ? 'Image captured - ready to register'
                  : 'Ready to register'}
              </p>
            </div>

            <Button
              onClick={registerFace}
              isLoading={isProcessing}
              fullWidth
              size="lg"
              disabled={capturedImages.length < 1 || capturedImages.length > MAX_IMAGES || !studentId}
            >
              <IoCheckmark className="w-5 h-5 mr-2" />
              {isUpdate ? 'Update Face' : 'Register Face'}
            </Button>
          </div>
        </Card>
      </div>

      {/* Captured Images Gallery */}
      {capturedImages.length > 0 && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Captured Images</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {capturedImages.map((img, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="relative group"
              >
                <img
                  src={img}
                  alt={`Capture ${index + 1}`}
                  className="w-full aspect-square object-cover rounded-lg"
                />
                <button
                  onClick={() => removeImage(index)}
                  className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <IoTrash className="w-4 h-4" />
                </button>
                <div className="absolute bottom-2 left-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                  #{index + 1}
                </div>
              </motion.div>
            ))}
          </div>
        </Card>
      )}

      {/* Simplified Instructions */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">📋 Quick Guide</h2>
        <div className="space-y-3">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-800 mb-2">How to Register:</h3>
            <ol className="text-blue-700 space-y-1">
              <li><strong>1.</strong> Enter roll number</li>
              <li><strong>2.</strong> Position face in green guide</li>
              <li><strong>3.</strong> Take one clear photo</li>
              <li><strong>4.</strong> Click register when done</li>
            </ol>
          </div>
          
          <div className="bg-green-50 p-3 rounded-lg">
            <h4 className="font-semibold text-green-800 mb-1">✅ Tips for Success:</h4>
            <ul className="text-green-700 text-sm space-y-1">
              <li>• Ensure good lighting on your face</li>
              <li>• Look directly at camera</li>
              <li>• Remove glasses/masks if possible</li>
              <li>• System adapts to different conditions automatically</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default FaceRegistration
