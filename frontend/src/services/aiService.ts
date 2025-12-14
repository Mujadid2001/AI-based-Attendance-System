import api from './api'
import type { FaceRecognitionResult } from '@/types'

export const aiService = {
  // Face Registration
  registerFace: async (studentId: number, images: File[]): Promise<void> => {
    const formData = new FormData()
    formData.append('student_id', studentId.toString())
    images.forEach((image, index) => {
      formData.append(`image_${index}`, image)
    })

    await api.post('/ai/face-registration/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
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
      '/ai/face-recognition/recognize/',
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

  // Test face detection
  testFaceDetection: async (imageFile: File): Promise<{
    faces_detected: number
    face_locations: number[][]
  }> => {
    const formData = new FormData()
    formData.append('image', imageFile)

    const response = await api.post('/ai/face-recognition/test_detection/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
}
