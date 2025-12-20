import api from './api'
import type {
  AttendanceSession,
  AttendanceRecord,
  AttendanceStats,
  PaginatedResponse,
} from '@/types'

export const attendanceService = {
  // Sessions
  getSessions: async (params?: {
    page?: number
    course?: number
    is_active?: boolean
    date?: string
    ordering?: string
  }): Promise<PaginatedResponse<AttendanceSession>> => {
    const response = await api.get<PaginatedResponse<AttendanceSession>>(
      '/attendance/sessions/',
      { params }
    )
    return response.data
  },

  getSession: async (id: number): Promise<AttendanceSession> => {
    const response = await api.get<AttendanceSession>(`/attendance/sessions/${id}/`)
    return response.data
  },

  createSession: async (data: Partial<AttendanceSession>): Promise<AttendanceSession> => {
    const response = await api.post<AttendanceSession>('/attendance/sessions/', data)
    return response.data
  },

  updateSession: async (
    id: number,
    data: Partial<AttendanceSession>
  ): Promise<AttendanceSession> => {
    const response = await api.patch<AttendanceSession>(`/attendance/sessions/${id}/`, data)
    return response.data
  },

  deleteSession: async (id: number): Promise<void> => {
    await api.delete(`/attendance/sessions/${id}/`)
  },

  closeSession: async (id: number): Promise<AttendanceSession> => {
    const response = await api.post<AttendanceSession>(`/attendance/sessions/${id}/close_session/`)
    return response.data
  },

  // Get active session
  getActiveSession: async (): Promise<AttendanceSession | null> => {
    const response = await api.get<AttendanceSession>('/attendance/active_session/')
    return response.data
  },

  // Attendance Records
  getRecords: async (params?: {
    page?: number
    session?: number
    student?: number
    status?: string
    ordering?: string
  }): Promise<PaginatedResponse<AttendanceRecord>> => {
    const response = await api.get<PaginatedResponse<AttendanceRecord>>(
      '/attendance/records/',
      { params }
    )
    return response.data
  },

  getSessionRecords: async (sessionId: number): Promise<AttendanceRecord[]> => {
    const response = await api.get<AttendanceRecord[]>(
      `/attendance/session_records/${sessionId}/`
    )
    return response.data
  },

  markAttendance: async (data: {
    session: number
    student: number
    status: string
    verification_method?: string
    notes?: string
  }): Promise<AttendanceRecord> => {
    const response = await api.post<AttendanceRecord>('/attendance/records/', data)
    return response.data
  },

  updateAttendance: async (
    id: number,
    data: Partial<AttendanceRecord>
  ): Promise<AttendanceRecord> => {
    const response = await api.patch<AttendanceRecord>(`/attendance/records/${id}/`, data)
    return response.data
  },

  deleteAttendance: async (id: number): Promise<void> => {
    await api.delete(`/attendance/records/${id}/`)
  },

  // Mark attendance by face
  markAttendanceByFace: async (sessionId: number, imageFile: File) => {
    const formData = new FormData()
    formData.append('session_id', sessionId.toString())
    formData.append('image', imageFile)

    const response = await api.post('/attendance/mark_by_face/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  // Get today's attendance
  getTodayAttendance: async (): Promise<{
    date: string
    total: number
    marked: number
    present: number
    leave: number
    absent: number
    sessions: number
    percentage: number
  }> => {
    const response = await api.get('/attendance/today/')
    return response.data
  },

  // Get attendance stats
  getAttendanceStats: async (params?: {
    student?: number
    course?: number
    start_date?: string
    end_date?: string
  }): Promise<AttendanceStats> => {
    const response = await api.get<AttendanceStats>('/attendance/stats/', { params })
    return response.data
  },

  // Get student's own attendance (for student role)
  getMyAttendance: async (): Promise<{
    student: {
      roll_number: string
      name: string
      department: string
    }
    overall_stats: {
      total: number
      present: number
      leave: number
      absent: number
      percentage: number
    }
    courses: Array<{
      course_id: number
      course_code: string
      course_name: string
      total_sessions: number
      present: number
      leave: number
      absent: number
      percentage: number
    }>
    recent_records: AttendanceRecord[]
  }> => {
    const response = await api.get('/attendance/records/my_attendance/')
    return response.data
  },

  // Reports
  getAttendanceReport: async (params: {
    course?: number
    student?: number
    start_date?: string
    end_date?: string
  }) => {
    const response = await api.get('/attendance/reports/', { params })
    return response.data
  },

  exportAttendanceReport: async (params: {
    course?: number
    start_date?: string
    end_date?: string
    format?: 'csv' | 'excel' | 'pdf'
  }): Promise<Blob> => {
    const response = await api.get('/attendance/reports/export/', {
      params,
      responseType: 'blob',
    })
    return response.data
  },
}
