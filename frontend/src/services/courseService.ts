import api from './api'
import type { Course, Enrollment, PaginatedResponse } from '@/types'

export const courseService = {
  // Get all courses
  getCourses: async (params?: {
    page?: number
    search?: string
    is_active?: boolean
    ordering?: string
  }): Promise<PaginatedResponse<Course>> => {
    const response = await api.get<PaginatedResponse<Course>>('/students/courses/', { params })
    return response.data
  },

  // Get course by ID
  getCourse: async (id: number): Promise<Course> => {
    const response = await api.get<Course>(`/students/courses/${id}/`)
    return response.data
  },

  // Create course
  createCourse: async (data: Partial<Course>): Promise<Course> => {
    const response = await api.post<Course>('/students/courses/', data)
    return response.data
  },

  // Update course
  updateCourse: async (id: number, data: Partial<Course>): Promise<Course> => {
    const response = await api.patch<Course>(`/students/courses/${id}/`, data)
    return response.data
  },

  // Delete course
  deleteCourse: async (id: number): Promise<void> => {
    await api.delete(`/students/courses/${id}/`)
  },

  // Get course enrollments
  getCourseEnrollments: async (courseId: number): Promise<Enrollment[]> => {
    const response = await api.get<Enrollment[]>(`/students/courses/${courseId}/students/`)
    return response.data
  },

  // Enroll student
  enrollStudent: async (courseId: number, studentId: number): Promise<Enrollment> => {
    const response = await api.post<Enrollment>('/students/enrollments/', {
      course: courseId,
      student: studentId,
    })
    return response.data
  },

  // Unenroll student
  unenrollStudent: async (enrollmentId: number): Promise<void> => {
    await api.delete(`/students/enrollments/${enrollmentId}/`)
  },

  // Get student enrollments
  getStudentEnrollments: async (studentId: number): Promise<Enrollment[]> => {
    const response = await api.get<Enrollment[]>('/students/enrollments/', {
      params: { student: studentId },
    })
    return response.data
  },
}
