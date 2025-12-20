import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { IoAdd, IoSearch, IoPerson } from 'react-icons/io5'
import { Card, Button, Input, LoadingSpinner, Badge } from '@components/ui'
import { studentService, courseService } from '@services/index'
import type { StudentProfile, Course } from '@/types'
import toast from 'react-hot-toast'

const Students = () => {
  const [students, setStudents] = useState<StudentProfile[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCourse, setSelectedCourse] = useState<string>('')

  useEffect(() => {
    fetchCourses()
    fetchStudents()
  }, [])

  useEffect(() => {
    fetchStudents()
  }, [selectedCourse])

  const fetchCourses = async () => {
    try {
      const response = await courseService.getCourses()
      setCourses(response.results || response || [])
    } catch (error) {
      console.error('Failed to load courses:', error)
    }
  }

  const fetchStudents = async () => {
    try {
      const params: any = {}
      if (selectedCourse) {
        params.course = parseInt(selectedCourse)
      }
      const response = await studentService.getStudents(params)
      console.log('Students API response:', response)
      setStudents(response.results || response || [])
    } catch (error) {
      console.error('Failed to load students:', error)
      toast.error('Failed to load students')
    } finally {
      setLoading(false)
    }
  }

  const filteredStudents = students.filter(
    (student) =>
      student.user.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.user.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.roll_number.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Students</h1>
          <p className="text-gray-600 mt-1">Manage student profiles and information</p>
        </div>
        <Link to="/students/add">
          <Button>
            <IoAdd className="w-5 h-5 mr-2" />
            Add Student
          </Button>
        </Link>
      </div>

      {/* Search */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            placeholder="Search students by name or ID..."
            leftIcon={<IoSearch className="w-5 h-5 text-gray-400" />}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">All Students</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.code} - {course.name}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Students Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredStudents.map((student, index) => (
          <motion.div
            key={student.user.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Link to={`/students/${student.user.id}`}>
              <Card hoverable>
                <div className="flex items-center gap-4 mb-4">
                  {student.user.profile_picture ? (
                    <img
                      src={student.user.profile_picture}
                      alt={student.user.first_name}
                      className="w-16 h-16 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
                      <IoPerson className="w-8 h-8 text-white" />
                    </div>
                  )}
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {student.user.first_name} {student.user.last_name}
                    </h3>
                    <p className="text-sm text-gray-600">{student.roll_number}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <span className="text-sm text-gray-600">{student.user.email}</span>
                  <div className="flex items-center gap-2 flex-wrap">
                    {student.is_face_registered ? (
                      <Badge variant="success" size="sm">Face Registered</Badge>
                    ) : (
                      <Badge variant="warning" size="sm">No Face Data</Badge>
                    )}
                    {!student.user.is_verified && (
                      <Badge variant="danger" size="sm">Email Unverified</Badge>
                    )}
                  </div>
                </div>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

      {filteredStudents.length === 0 && (
        <Card className="text-center py-12">
          <p className="text-gray-600">No students found</p>
        </Card>
      )}
    </div>
  )
}

export default Students
