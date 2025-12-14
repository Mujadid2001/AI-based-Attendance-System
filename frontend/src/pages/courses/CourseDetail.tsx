import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  IoArrowBack,
  IoBook,
  IoPeople,
  IoCalendar,
  IoTime,
  IoCheckmarkCircle,
  IoCloseCircle,
  IoPersonAdd,
} from 'react-icons/io5'
import { Card, Button, LoadingSpinner, Badge } from '@components/ui'
import { courseService, studentService } from '@services/index'
import { useAuthStore } from '@store/authStore'
import type { Course, StudentProfile } from '@/types'
import toast from 'react-hot-toast'

const CourseDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [course, setCourse] = useState<Course | null>(null)
  const [students, setStudents] = useState<StudentProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [isUpdating, setIsUpdating] = useState(false)

  useEffect(() => {
    if (id) {
      fetchCourseDetails()
    }
  }, [id])

  const handleToggleActive = async () => {
    if (!course) return
    
    // Confirmation dialog
    const message = course.is_active 
      ? 'Are you sure you want to deactivate this course? No new students can be enrolled while inactive.'
      : 'Are you sure you want to activate this course?'
    
    if (!window.confirm(message)) {
      return
    }
    
    setIsUpdating(true)
    try {
      const updatedCourse = await courseService.updateCourse(course.id, {
        is_active: !course.is_active,
      })
      setCourse(updatedCourse)
      toast.success(`Course ${updatedCourse.is_active ? 'activated' : 'deactivated'} successfully`)
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update course')
    } finally {
      setIsUpdating(false)
    }
  }

  const handleEdit = () => {
    navigate(`/courses/${id}/edit`);
  }

  const fetchCourseDetails = async () => {
    try {
      // Fetch course details
      const courseData = await courseService.getCourse(Number(id))
      setCourse(courseData)

      // Fetch enrolled students if available
      try {
        const enrollments = await courseService.getCourseEnrollments(Number(id))
        // Get student details for each enrollment
        if (enrollments && enrollments.length > 0) {
          const studentIds = enrollments.map((e: any) => e.student)
          if (studentIds.length > 0) {
            const studentsData = await studentService.getStudents()
            const enrolledStudents = studentsData.results.filter((s: StudentProfile) =>
              studentIds.includes(s.id)
            )
            setStudents(enrolledStudents)
          }
        }
      } catch (error) {
        // Enrollments endpoint might not exist, just continue
        console.log('Could not fetch enrollments:', error)
      }
    } catch (error: any) {
      console.error('Failed to load course:', error)
      toast.error(error.response?.data?.message || 'Failed to load course details')
      navigate('/courses')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!course) {
    return (
      <Card>
        <p className="text-gray-600">Course not found</p>
      </Card>
    )
  }

  // Check if course is in the future (coming soon)
  const currentDate = new Date()
  const courseYear = course.year
  const currentYear = currentDate.getFullYear()
  const currentMonth = currentDate.getMonth() + 1 // 0-indexed

  let isComingSoon = false
  
  // If course year is in the future, it's coming soon
  if (courseYear > currentYear) {
    isComingSoon = true
  } else if (courseYear === currentYear) {
    // Check semester timing for current year
    if (course.semester === 'Spring' && currentMonth < 1) {
      isComingSoon = true // Spring hasn't started
    } else if (course.semester === 'Summer' && currentMonth < 6) {
      isComingSoon = true // Summer hasn't started
    } else if (course.semester === 'Fall' && currentMonth < 9) {
      isComingSoon = true // Fall hasn't started
    }
  }

  if (isComingSoon) {
    return (
      <div className="space-y-6">
        <Button variant="secondary" onClick={() => navigate('/courses')}>
          <IoArrowBack className="w-5 h-5 mr-2" />
          Back to Courses
        </Button>

        <Card className="text-center py-12">
          <IoCalendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{course.name}</h2>
          <p className="text-lg text-gray-600 mb-4">{course.code}</p>
          <Badge variant="warning" size="lg">
            Coming Soon - {course.semester} {course.year}
          </Badge>
          <p className="text-gray-600 mt-4">
            This course will be available in {course.semester} {course.year}
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="secondary" onClick={() => navigate('/courses')}>
          <IoArrowBack className="w-5 h-5 mr-2" />
          Back to Courses
        </Button>
        {(user?.role === 'admin' || user?.role === 'teacher') && (
          <div className="flex gap-3">
            <Button variant="secondary" onClick={handleEdit}>Edit Course</Button>
            {course.is_active ? (
              <Button variant="danger" onClick={handleToggleActive} isLoading={isUpdating}>
                Deactivate
              </Button>
            ) : (
              <Button onClick={handleToggleActive} isLoading={isUpdating}>
                Activate
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Course Info Card */}
      <Card>
        <div className="flex items-start gap-6">
          <div className="w-20 h-20 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
            <IoBook className="w-10 h-10 text-white" />
          </div>
          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{course.name}</h1>
                <p className="text-xl text-gray-600 mb-4">{course.code}</p>
              </div>
              {course.is_active ? (
                <Badge variant="success">
                  <IoCheckmarkCircle className="w-4 h-4 mr-1" />
                  Active
                </Badge>
              ) : (
                <Badge variant="default">
                  <IoCloseCircle className="w-4 h-4 mr-1" />
                  Inactive
                </Badge>
              )}
            </div>
            <p className="text-gray-700 mb-4">
              {course.description || 'No description available'}
            </p>
            <div className="flex flex-wrap gap-4 text-sm text-gray-600">
              <div className="flex items-center">
                <IoCalendar className="w-4 h-4 mr-2" />
                {course.semester} {course.year}
              </div>
              <div className="flex items-center">
                <IoPeople className="w-4 h-4 mr-2" />
                {students.length} Students Enrolled
              </div>
              {course.instructor && (
                <div className="flex items-center">
                  <IoPersonAdd className="w-4 h-4 mr-2" />
                  Instructor: {course.instructor.first_name} {course.instructor.last_name}
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="text-center">
            <IoPeople className="w-8 h-8 text-blue-500 mx-auto mb-2" />
            <p className="text-3xl font-bold text-gray-900">{students.length}</p>
            <p className="text-gray-600">Total Students</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <IoTime className="w-8 h-8 text-purple-500 mx-auto mb-2" />
            <p className="text-3xl font-bold text-gray-900">0</p>
            <p className="text-gray-600">Total Sessions</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <IoCheckmarkCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
            <p className="text-3xl font-bold text-gray-900">0%</p>
            <p className="text-gray-600">Attendance Rate</p>
          </div>
        </Card>
      </div>

      {/* Enrolled Students */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Enrolled Students</h2>
          {(user?.role === 'admin' || user?.role === 'teacher') && (
            <Button size="sm">
              <IoPersonAdd className="w-4 h-4 mr-2" />
              Add Student
            </Button>
          )}
        </div>

        {students.length === 0 ? (
          <div className="text-center py-8">
            <IoPeople className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">No students enrolled yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Roll Number</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Name</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Email</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student) => (
                  <tr key={student.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">{student.roll_number}</td>
                    <td className="py-3 px-4">
                      <Link
                        to={`/students/${student.id}`}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        {student.user.first_name} {student.user.last_name}
                      </Link>
                    </td>
                    <td className="py-3 px-4 text-gray-600">{student.user.email}</td>
                    <td className="py-3 px-4">
                      <Badge variant="success" size="sm">
                        Active
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

export default CourseDetail
