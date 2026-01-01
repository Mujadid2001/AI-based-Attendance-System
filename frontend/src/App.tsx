import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import RoleBasedRoute from '@/components/RoleBasedRoute'

// Pages
import Login from '@pages/auth/Login'
import Register from '@pages/auth/Register'
import VerifyEmail from '@pages/auth/VerifyEmail'
import ForgotPassword from '@pages/auth/ForgotPassword'
import Dashboard from '@pages/Dashboard'
import Students from '@pages/students/Students'
import StudentDetail from '@pages/students/StudentDetail'
import AddStudent from '@pages/students/AddStudent'
import EditStudent from '@pages/students/EditStudent'
import Courses from '@pages/courses/Courses'
import CourseDetail from '@pages/courses/CourseDetail'
import EditCourse from '@pages/courses/EditCourse'
import Attendance from '@pages/attendance/Attendance'
import AttendanceSession from '@pages/attendance/AttendanceSession'
import FaceRecognition from '@pages/ai/FaceRecognition'
import FaceRegistration from '@pages/ai/FaceRegistration'
import ExternalCameras from '@pages/ai/ExternalCameras'
import Reports from '@pages/reports/Reports'
import Profile from '@pages/Profile'
import EditProfile from '@pages/EditProfile'
import Settings from '@pages/Settings'
import NotFound from '@pages/NotFound'

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />

        {/* Protected Routes */}
        <Route path="/" element={<ProtectedRoute />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          
          {/* Student Management - Admin/Teacher Only */}
          <Route path="students" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><Students /></RoleBasedRoute>} />
          <Route path="students/add" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><AddStudent /></RoleBasedRoute>} />
          <Route path="students/:id" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><StudentDetail /></RoleBasedRoute>} />
          <Route path="students/:id/edit" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><EditStudent /></RoleBasedRoute>} />
          
          {/* Course Management - Admin/Teacher Only */}
          <Route path="courses" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><Courses /></RoleBasedRoute>} />
          <Route path="courses/:id" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><CourseDetail /></RoleBasedRoute>} />
          <Route path="courses/:id/edit" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><EditCourse /></RoleBasedRoute>} />
          
          {/* Attendance - Admin/Teacher Only */}
          <Route path="attendance" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><Attendance /></RoleBasedRoute>} />
          <Route path="attendance/session/:id" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><AttendanceSession /></RoleBasedRoute>} />
          
          {/* AI Features - Admin/Teacher Only */}
          <Route path="face-recognition" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><FaceRecognition /></RoleBasedRoute>} />
          <Route path="face-registration" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><FaceRegistration /></RoleBasedRoute>} />
          <Route path="external-cameras" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><ExternalCameras /></RoleBasedRoute>} />
          
          {/* Reports - Admin/Teacher Only */}
          <Route path="reports" element={<RoleBasedRoute allowedRoles={['admin', 'teacher']}><Reports /></RoleBasedRoute>} />
          
          {/* User */}
          <Route path="profile" element={<Profile />} />
          <Route path="profile/edit" element={<EditProfile />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
