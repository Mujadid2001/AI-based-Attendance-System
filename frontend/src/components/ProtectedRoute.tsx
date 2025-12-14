import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@store/authStore'
import MainLayout from '@components/layout/MainLayout'

const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuthStore()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return (
    <MainLayout>
      <Outlet />
    </MainLayout>
  )
}

export default ProtectedRoute
