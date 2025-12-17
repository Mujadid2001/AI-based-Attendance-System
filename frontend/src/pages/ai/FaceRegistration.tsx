import { useState, useRef, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useLocation, useNavigate } from 'react-router-dom'
import { IoCamera, IoCloudUpload, IoTrash, IoCheckmark, IoArrowBack } from 'react-icons/io5'
import { Card, Button, Input } from '@components/ui'
import { aiService } from '@services/index'
import toast from 'react-hot-toast'
import Webcam from 'react-webcam'

const MAX_IMAGES = 5

const FaceRegistration = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const prefilledRollNumber = location.state?.prefilledRollNumber || ''
  const studentEmail = location.state?.studentEmail || ''
  const studentName = location.state?.studentName || ''
  
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

  // Draw face guide overlay
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw oval guide
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    const radiusX = canvas.width * 0.25
    const radiusY = canvas.height * 0.35

    ctx.strokeStyle = '#10b981'
    ctx.lineWidth = 3
    ctx.setLineDash([10, 5])
    ctx.beginPath()
    ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI)
    ctx.stroke()

    // Draw text guide
    ctx.fillStyle = '#10b981'
    ctx.font = 'bold 18px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Position your face within this guide', centerX, 40)
  }, [])

  const captureImage = useCallback(() => {
    if (capturedImages.length >= MAX_IMAGES) {
      toast.error(`Maximum ${MAX_IMAGES} images allowed`)
      return
    }

    const imageSrc = webcamRef.current?.getScreenshot()
    if (imageSrc) {
      setCapturedImages((prev) => [...prev, imageSrc])
      toast.success(`Image ${capturedImages.length + 1} of ${MAX_IMAGES} captured`)
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

    if (capturedImages.length < 3) {
      toast.error('Please capture at least 3 images for better accuracy')
      return
    }

    if (capturedImages.length > MAX_IMAGES) {
      toast.error(`Maximum ${MAX_IMAGES} images allowed`)
      return
    }

    setIsProcessing(true)

    try {
      // Convert base64 images to files
      const files = await Promise.all(
        capturedImages.map(async (img, index) => {
          const blob = await fetch(img).then((res) => res.blob())
          return new File([blob], `face_${index}.jpg`, { type: 'image/jpeg' })
        })
      )

      await aiService.registerFace(studentId, files)
      toast.success('Face registered successfully!')
      
      // Reset form
      setStudentId('')
      setCapturedImages([])
      
      // Navigate back if came from student detail
      if (prefilledRollNumber) {
        setTimeout(() => navigate(-1), 1500)
      }
    } catch (error: any) {
      console.error('Face registration error:', error)
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Registration failed'
      toast.error(errorMsg)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Face Registration</h1>
          {isPrefilledStudent ? (
            <p className="text-gray-600 mt-1">
              Registering face for: <span className="font-semibold text-gray-900">{studentName}</span> ({studentEmail})
            </p>
          ) : (
            <p className="text-gray-600 mt-1">Register student faces for attendance recognition</p>
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
                {capturedImages.length < 3 
                  ? `Minimum 3 images required (${3 - capturedImages.length} more needed)`
                  : capturedImages.length >= MAX_IMAGES
                  ? 'Maximum images reached'
                  : 'Ready to register'}
              </p>
            </div>

            <Button
              onClick={registerFace}
              isLoading={isProcessing}
              fullWidth
              size="lg"
              disabled={capturedImages.length < 3 || capturedImages.length > MAX_IMAGES || !studentId}
            >
              <IoCheckmark className="w-5 h-5 mr-2" />
              Register Face
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

      {/* Instructions */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Instructions</h2>
        <ul className="space-y-2 text-gray-600">
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">1.</span>
            <span>Enter the roll number in the form</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">2.</span>
            <span>Position your face within the green guide overlay on the camera</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">3.</span>
            <span>Capture 3-5 images from different angles (straight, slight left, slight right)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">4.</span>
            <span>Ensure good lighting and clear face visibility without glasses or masks</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">5.</span>
            <span>Click "Register Face" when you have captured 3-5 quality images</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">6.</span>
            <span>Maximum {MAX_IMAGES} images allowed per registration</span>
          </li>
        </ul>
      </Card>
    </div>
  )
}

export default FaceRegistration
