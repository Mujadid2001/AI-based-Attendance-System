import api from './api'
import type { FaceRecognitionResult } from '@/types'

export const aiService = {
  // Face Registration - sends images one by one with enhanced error handling
  registerFace: async (rollNumber: string, images: File[]): Promise<void> => {
    if (images.length === 0) {
      throw new Error('No images provided')
    }

    if (images.length > 1) {
      throw new Error('Only one image is allowed')
    }

    let successCount = 0
    let lastError: Error | null = null

    // Send images one by one with enhanced error handling
    for (let i = 0; i < images.length; i++) {
      try {
        const formData = new FormData()
        formData.append('student_id', rollNumber)
        formData.append('image', images[i])

        const response = await api.post('/ai/face-registration/register-face/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 90000, // 90 seconds for enhanced processing
        })

        successCount++
        console.log(`Image ${i + 1} registered successfully:`, response.data)

        // If first image succeeds, continue with others for enhanced accuracy
        if (i === 0) {
          console.log('Primary image registration successful, processing additional images...')
        }

      } catch (error: any) {
        console.error(`Error registering image ${i + 1}:`, error)
        lastError = error

        // If this is the first image and it fails, try the next one
        if (i === 0 && images.length > 1) {
          console.warn(`First image failed, trying next image...`)
          continue
        }

        // For subsequent images, log the error but don't fail the entire process
        if (successCount > 0) {
          console.warn(`Image ${i + 1} failed but continuing since we have successful registrations`)
          continue
        }
      }
    }

    // Check if we have at least one successful registration
    if (successCount === 0) {
      throw lastError || new Error(`All ${images.length} images failed to register`)
    }

    console.log(`Face registration completed: ${successCount}/${images.length} images successful`)
  },

  // Update face registration with enhanced handling
  updateFace: async (rollNumber: string, images: File[]): Promise<void> => {
    if (images.length === 0) {
      throw new Error('No images provided')
    }

    if (images.length > 1) {
      throw new Error('Only one image is allowed')
    }

    let successCount = 0
    let lastError: Error | null = null

    // Send images one by one for update
    for (let i = 0; i < images.length; i++) {
      try {
        const formData = new FormData()
        formData.append('student_id', rollNumber)
        formData.append('image', images[i])
        
        // For first image, clear existing data
        if (i === 0) {
          formData.append('clear_existing', 'true')
        } else {
          formData.append('clear_existing', 'false')
        }

        const response = await api.post('/ai/face-registration/update-face/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 90000, // 90 seconds for enhanced processing
        })

        successCount++
        console.log(`Image ${i + 1} updated successfully:`, response.data)

      } catch (error: any) {
        console.error(`Error updating image ${i + 1}:`, error)
        lastError = error

        // For updates, try to continue with other images if we have at least one success
        if (successCount > 0 && i > 0) {
          console.warn(`Image ${i + 1} failed but continuing since we have successful updates`)
          continue
        }
      }
    }

    // Check if we have at least one successful update
    if (successCount === 0) {
      throw lastError || new Error(`All ${images.length} images failed to update`)
    }

    console.log(`Face update completed: ${successCount}/${images.length} images successful`)
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
