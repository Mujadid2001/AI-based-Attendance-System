import api from './api'
import type { FaceRecognitionResult } from '@/types'

export const aiService = {
  // Face Registration - sends images one by one
  registerFace: async (rollNumber: string, images: File[]): Promise<void> => {
    if (images.length === 0) {
      throw new Error('No images provided')
    }

    if (images.length < 3) {
      throw new Error('Minimum 3 images required')
    }

    if (images.length > 5) {
      throw new Error('Maximum 5 images allowed')
    }

    // Send first image (primary registration)
    const formData = new FormData()
    formData.append('student_id', rollNumber)
    formData.append('image', images[0])

    const response = await api.post('/ai/face-registration/register-face/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60 seconds for face processing
    })

    // Send remaining images for additional training data
    for (let i = 1; i < images.length; i++) {
      const additionalData = new FormData()
      additionalData.append('student_id', rollNumber)
      additionalData.append('image', images[i])

      await api.post('/ai/face-registration/register-face/', additionalData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000, // 60 seconds for face processing
      })
    }

    return response.data
  },

  // Update face registration - re-register with new images
  updateFace: async (rollNumber: string, images: File[]): Promise<void> => {
    if (images.length === 0) {
      throw new Error('No images provided')
    }

    if (images.length < 3) {
      throw new Error('Minimum 3 images required')
    }

    if (images.length > 5) {
      throw new Error('Maximum 5 images allowed')
    }

    // Send first image with clear_existing flag (clears old data)
    const formData = new FormData()
    formData.append('student_id', rollNumber)
    formData.append('image', images[0])
    formData.append('clear_existing', 'true')

    const response = await api.post('/ai/face-registration/update-face/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60 seconds for face processing
    })

    // Send remaining images for additional training data
    for (let i = 1; i < images.length; i++) {
      const additionalData = new FormData()
      additionalData.append('student_id', rollNumber)
      additionalData.append('image', images[i])
      additionalData.append('clear_existing', 'false')

      await api.post('/ai/face-registration/update-face/', additionalData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000, // 60 seconds for face processing
      })
    }

    return response.data
  },

  // Update face encoding
  updateFaceEncoding: async (studentId: number, images: File[]): Promise<void> => {
    const formData = new FormData()
    images.forEach((image, index) => {
      formData.append(`image_${index}`, image)
    })

    await api.patch(`/ai/face-registration/${studentId}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // Delete face encoding
  deleteFaceEncoding: async (studentId: number): Promise<void> => {
    await api.delete(`/ai/face-registration/${studentId}/`)
  },

  // Recognize face
  recognizeFace: async (imageFile: File): Promise<FaceRecognitionResult> => {
    const formData = new FormData()
    formData.append('image', imageFile)

    const response = await api.post<FaceRecognitionResult>(
      '/ai/face-recognition/recognize-only/',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },

  // Verify face
  verifyFace: async (studentId: number, imageFile: File): Promise<boolean> => {
    const formData = new FormData()
    formData.append('student_id', studentId.toString())
    formData.append('image', imageFile)

    const response = await api.post<{ verified: boolean }>(
      '/ai/face-recognition/verify/',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data.verified
  },

  // Get AI configuration
  getConfiguration: async () => {
    const response = await api.get('/ai/configuration/')
    return response.data
  },

  // Update AI configuration
  updateConfiguration: async (data: any) => {
    const response = await api.patch('/ai/configuration/', data)
    return response.data
  },

  // Bulk recognize and mark attendance
  bulkRecognizeAttendance: async (sessionId: number, images: File[]): Promise<{
    message: string
    summary: {
      total_enrolled: number
      marked_present: number
      marked_absent: number
      already_marked: number
      recognized_faces: number
    }
    recognized_students: Array<{
      student_id: number
      student_name: string
      confidence: number
      recognized: boolean
    }>
  }> => {
    const formData = new FormData()
    formData.append('session_id', sessionId.toString())
    images.forEach((image) => {
      formData.append('images', image)
    })

    const response = await api.post(
      '/ai/face-recognition/bulk-recognize-attendance/',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },

  // Test face detection
  testFaceDetection: async (imageFile: File): Promise<{
    faces_detected: number
    face_locations: number[][]
  }> => {
    const formData = new FormData()
    formData.append('image', imageFile)

    const response = await api.post('/ai/face-recognition/test-detection/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
}
