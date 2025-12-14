import { useState, useRef, useCallback } from 'react'
import { motion } from 'framer-motion'
import { IoCamera, IoCloudUpload, IoTrash, IoCheckmark } from 'react-icons/io5'
import { Card, Button, Input } from '@components/ui'
import { aiService } from '@services/index'
import toast from 'react-hot-toast'
import Webcam from 'react-webcam'

const FaceRegistration = () => {
  const webcamRef = useRef<Webcam>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [studentId, setStudentId] = useState('')
  const [capturedImages, setCapturedImages] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)

  const captureImage = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot()
    if (imageSrc) {
      setCapturedImages((prev) => [...prev, imageSrc])
      toast.success(`Image ${capturedImages.length + 1} captured`)
    }
  }, [capturedImages.length])

  const removeImage = (index: number) => {
    setCapturedImages((prev) => prev.filter((_, i) => i !== index))
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    Array.from(files).forEach((file) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        if (e.target?.result) {
          setCapturedImages((prev) => [...prev, e.target!.result as string])
        }
      }
      reader.readAsDataURL(file)
    })

    toast.success(`${files.length} image(s) uploaded`)
  }

  const registerFace = async () => {
    if (!studentId) {
      toast.error('Please enter a student ID')
      return
    }

    if (capturedImages.length < 3) {
      toast.error('Please capture at least 3 images for better accuracy')
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

      await aiService.registerFace(parseInt(studentId), files)
      toast.success('Face registered successfully!')
      
      // Reset form
      setStudentId('')
      setCapturedImages([])
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Registration failed')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Face Registration</h1>
        <p className="text-gray-600 mt-1">Register student faces for attendance recognition</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Camera View */}
        <Card className="lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">Camera</h2>
          <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden mb-4">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              className="w-full h-full object-cover"
              mirrored
            />
          </div>

          <div className="flex gap-4">
            <Button onClick={captureImage} fullWidth>
              <IoCamera className="w-5 h-5 mr-2" />
              Capture Image ({capturedImages.length})
            </Button>
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              fullWidth
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
            <Input
              label="Student ID"
              type="number"
              placeholder="Enter student ID"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Images Captured
              </label>
              <div className="text-3xl font-bold text-primary-600">
                {capturedImages.length}
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Minimum 3 images recommended
              </p>
            </div>

            <Button
              onClick={registerFace}
              isLoading={isProcessing}
              fullWidth
              size="lg"
              disabled={capturedImages.length === 0 || !studentId}
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
            <span>Enter the student ID in the form</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">2.</span>
            <span>Capture at least 3-5 images from different angles</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">3.</span>
            <span>Ensure good lighting and clear face visibility</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">4.</span>
            <span>Click "Register Face" to complete the registration</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">5.</span>
            <span>The student can now use face recognition for attendance</span>
          </li>
        </ul>
      </Card>
    </div>
  )
}

export default FaceRegistration
