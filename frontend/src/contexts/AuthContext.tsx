import { createContext, useContext, useEffect, ReactNode } from 'react'
import { useAuthStore } from '@store/authStore'
import { authService } from '@services/authService'

interface AuthContextType {
  // Auth state is managed by zustand store
}

const AuthContext = createContext<AuthContextType>({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const { setAuth, logout, setLoading } = useAuthStore()

  useEffect(() => {
    const initAuth = async () => {
      const accessToken = localStorage.getItem('accessToken')
      const refreshToken = localStorage.getItem('refreshToken')

      if (accessToken && refreshToken) {
        try {
          // Verify token and get current user
          const user = await authService.getCurrentUser()
          setAuth(user, { access: accessToken, refresh: refreshToken })
        } catch (error) {
          console.error('Auth initialization failed:', error)
          logout()
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  return (
    <AuthContext.Provider value={{}}>
      {children}
    </AuthContext.Provider>
  )
}
