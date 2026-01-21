import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import toast from 'react-hot-toast'

// Backend API base URL - configured via environment variable
// This allows complete decoupling from backend
const BASE_URL = (import.meta.env.VITE_API_URL as string) || 'https://localhost:8000/api'
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT as string) || 30000

// Validate API URL on initialization
if (!BASE_URL) {
  console.error('VITE_API_URL is not configured. Please set it in .env file')
}

// Create axios instance with complete decoupling
const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: API_TIMEOUT,
  withCredentials: true, // Enable credentials for CORS
})

// Helper function to get CSRF token from cookies
function getCsrfToken(): string | null {
  const name = 'csrftoken'
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

// Request interceptor - add JWT token and CSRF token to requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add JWT token if available
    const token = localStorage.getItem('accessToken')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add CSRF token for POST/PUT/PATCH/DELETE requests
    if (['post', 'put', 'patch', 'delete'].includes((config.method || '').toLowerCase())) {
      const csrfToken = getCsrfToken()
      if (csrfToken && config.headers) {
        config.headers['X-CSRFToken'] = csrfToken
      }
    }
    
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle token refresh and errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (!refreshToken) {
          throw new Error('No refresh token available')
        }

        // Try to refresh the token using the backend API
        const response = await axios.post(`${BASE_URL}/token/refresh/`, {
          refresh: refreshToken,
        })

        const { access } = response.data
        localStorage.setItem('accessToken', access)

        // Retry the original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`
        }
        
        // Return the retry promise directly (this prevents the 401 from propagating)
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh token failed - logout user
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        
        // Only show error if not already on login page
        if (!window.location.pathname.includes('/login')) {
          toast.error('Session expired. Please login again.')
          // Redirect to login page
          window.location.href = '/login'
        }
        
        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    const errorMessage = getErrorMessage(error)
    
    // Don't show toast for 401 errors (handled above) or 404 (handled in components)
    const silentErrors = [401, 404]
    if (!silentErrors.includes(error.response?.status || 0)) {
      toast.error(errorMessage)
    }

    return Promise.reject(error)
  }
)

// Helper function to extract error messages from API responses
function getErrorMessage(error: AxiosError): string {
  if (error.response?.data) {
    const data = error.response.data as any
    
    // Handle Django REST Framework error format
    if (data.detail) return data.detail
    if (data.message) return data.message
    if (data.error) return data.error
    
    // Handle field errors
    if (typeof data === 'object') {
      const firstError = Object.values(data)[0]
      if (Array.isArray(firstError)) {
        return firstError[0] as string
      }
      if (typeof firstError === 'string') {
        return firstError
      }
    }
  }

  // Handle network errors
  if (error.code === 'ECONNABORTED') {
    return 'Request timeout. Please check your connection.'
  }
  
  if (error.message === 'Network Error') {
    return 'Cannot connect to server. Please check if backend is running.'
  }

  if (error.message) return error.message
  
  return 'An unexpected error occurred'
}

export default api
