import api from './api'
import type { StudentProfile, PaginatedResponse } from '@/types'

export const studentService = {
  // Get all students
  getStudents: async (params?: {
    page?: number
    search?: string
    ordering?: string
  }): Promise<PaginatedResponse<StudentProfile>> => {
    const response = await api.get<PaginatedResponse<StudentProfile>>(
      '/students/profiles/',
      { params }
    )
    return response.data
  },

  // Get student by ID
  getStudent: async (id: number): Promise<StudentProfile> => {
    const response = await api.get<StudentProfile>(`/students/profiles/${id}/`)
    return response.data
  },

  // Create student
  createStudent: async (data: any): Promise<StudentProfile> => {
    const response = await api.post<StudentProfile>('/students/profiles/register_student/', data)
    return response.data
  },

  // Update student
  updateStudent: async (id: number, data: Partial<StudentProfile>): Promise<StudentProfile> => {
    const response = await api.patch<StudentProfile>(`/students/profiles/${id}/`, data)
    return response.data
  },

  // Delete student
  deleteStudent: async (id: number): Promise<void> => {
    await api.delete(`/students/profiles/${id}/`)
  },

  // Get student attendance stats
  getStudentAttendanceStats: async (id: number, courseId?: number) => {
    const params = courseId ? { course_id: courseId } : {}
    const response = await api.get(`/students/profiles/${id}/attendance_stats/`, { params })
    return response.data
  },

  // Upload profile picture
  uploadProfilePicture: async (id: number, file: File): Promise<StudentProfile> => {
    const formData = new FormData()
    formData.append('profile_picture', file)
    const response = await api.patch<StudentProfile>(
      `/students/profiles/${id}/`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },
}
