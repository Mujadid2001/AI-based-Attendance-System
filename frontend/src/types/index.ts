// User & Authentication Types
export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  role: 'admin' | 'teacher' | 'student'
  is_email_verified: boolean
  profile_picture?: string
  created_at: string
  updated_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  password_confirm: string
  first_name: string
  last_name: string
  role: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface AuthResponse {
  user: User
  tokens: AuthTokens
}

// Student Types
export interface StudentProfile {
  id: number
  user: User
  student_id: string
  date_of_birth?: string
  phone_number?: string
  address?: string
  enrollment_date: string
  face_registered: boolean
  face_encoding?: string
  created_at: string
  updated_at: string
}

// Course Types
export interface Course {
  id: number
  code: string
  name: string
  description?: string
  instructor: User
  semester: string
  year: number
  credits: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Enrollment {
  id: number
  student: StudentProfile
  course: Course
  enrolled_date: string
  status: 'active' | 'completed' | 'dropped'
}

// Attendance Types
export interface AttendanceSession {
  id: number
  course: Course
  date: string
  start_time: string
  end_time?: string
  session_type: 'lecture' | 'lab' | 'tutorial'
  is_active: boolean
  location?: string
  notes?: string
  created_by: User
  created_at: string
}

export interface AttendanceRecord {
  id: number
  session: AttendanceSession
  student: StudentProfile
  status: 'present' | 'absent' | 'late' | 'excused'
  marked_at: string
  marked_by: User
  verification_method: 'manual' | 'face_recognition' | 'qr_code'
  confidence_score?: number
  notes?: string
}

export interface AttendanceStats {
  total_sessions: number
  attended: number
  absent: number
  late: number
  attendance_percentage: number
}

// AI Types
export interface FaceRegistrationData {
  student_id: number
  images: File[]
}

export interface FaceRecognitionResult {
  student_id?: number
  student_name?: string
  confidence: number
  recognized: boolean
  message: string
}

// Report Types
export interface AttendanceReport {
  student: StudentProfile
  course: Course
  stats: AttendanceStats
  records: AttendanceRecord[]
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  message?: string
  status: number
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiError {
  message: string
  errors?: Record<string, string[]>
  status: number
}
