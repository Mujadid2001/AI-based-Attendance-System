import api from './api'
import type {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  User,
  AuthTokens,
} from '@/types'
import { sanitizeObject, removeRoleFields } from '@utils/security'

export const authService = {
  // Login
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/authentication/login/', credentials)
    return response.data
  },

  // Register
  register: async (data: RegisterData): Promise<AuthResponse> => {
    // Sanitize input and ensure only student/teacher roles are allowed
    const sanitizedData = sanitizeObject(data)
    // Ensure role is only student or teacher (never admin from registration)
    if (sanitizedData.role !== 'student' && sanitizedData.role !== 'teacher') {
      sanitizedData.role = 'student' // Default to student if invalid role
    }
    const response = await api.post<AuthResponse>('/auth/authentication/register/', sanitizedData)
    return response.data
  },

  // Logout
  logout: async (): Promise<void> => {
    const refreshToken = localStorage.getItem('refreshToken')
    if (refreshToken) {
      await api.post('/auth/authentication/logout/', { refresh: refreshToken })
    }
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
  },

  // Get current user
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/authentication/me/')
    return response.data
  },

  // Refresh token
  refreshToken: async (refresh: string): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/token/refresh/', { refresh })
    return response.data
  },

  // Verify email
  verifyEmail: async (data: { token: string }): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/authentication/verify-email/', data)
    return response.data
  },

  // Forgot password
  forgotPassword: async (email: string): Promise<void> => {
    await api.post('/auth/authentication/forgot-password/', { email })
  },

  // Reset password
  resetPassword: async (token: string, new_password: string, new_password_confirm: string): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/authentication/reset-password/', { 
      token, 
      new_password, 
      new_password_confirm 
    })
    return response.data
  },

  // Change password
  changePassword: async (passwordData: { old_password: string; new_password: string; new_password_confirm: string }): Promise<void> => {
    await api.post('/auth/authentication/change-password/', passwordData)
  },

  // Update profile
  updateProfile: async (data: Partial<User>): Promise<User> => {
    // Remove role-related fields to prevent privilege escalation
    const sanitizedData = removeRoleFields(sanitizeObject(data))
    const response = await api.put<User>('/auth/authentication/profile-update/', sanitizedData)
    return response.data
  },
}
