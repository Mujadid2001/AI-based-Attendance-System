import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'

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
import Reports from '@pages/reports/Reports'
import Profile from '@pages/Profile'
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
          
          {/* Student Management */}
          <Route path="students" element={<Students />} />
          <Route path="students/add" element={<AddStudent />} />
          <Route path="students/:id" element={<StudentDetail />} />
          <Route path="students/:id/edit" element={<EditStudent />} />
          
          {/* Course Management */}
          <Route path="courses" element={<Courses />} />
          <Route path="courses/:id" element={<CourseDetail />} />
          <Route path="courses/:id/edit" element={<EditCourse />} />
          
          {/* Attendance */}
          <Route path="attendance" element={<Attendance />} />
          <Route path="attendance/session/:id" element={<AttendanceSession />} />
          
          {/* AI Features */}
          <Route path="face-recognition" element={<FaceRecognition />} />
          <Route path="face-registration" element={<FaceRegistration />} />
          
          {/* Reports */}
          <Route path="reports" element={<Reports />} />
          
          {/* User */}
          <Route path="profile" element={<Profile />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
