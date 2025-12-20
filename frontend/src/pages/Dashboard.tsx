import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  IoPeople,
  IoBook,
  IoCalendar,
  IoCheckmarkCircle,
  IoCloseCircle,
  IoTime,
  IoTrendingUp,
  IoSchool,
  IoRefresh,
} from 'react-icons/io5'
import { Card, LoadingSpinner, Button } from '@components/ui'
import { useAuthStore } from '@store/authStore'
import { attendanceService, studentService, courseService } from '@services/index'
import toast from 'react-hot-toast'

interface DashboardStats {
  totalStudents: number
  totalCourses: number
  totalSessions: number
  attendanceRate: number
  todayAttendance: {
    present: number
    absent: number
    leave: number
  }
}

interface StudentAttendanceData {
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
  recent_records: any[]
}

const Dashboard = () => {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [stats, setStats] = useState<DashboardStats>({
    totalStudents: 0,
    totalCourses: 0,
    totalSessions: 0,
    attendanceRate: 0,
    todayAttendance: { present: 0, absent: 0, leave: 0 },
  })
  const [studentData, setStudentData] = useState<StudentAttendanceData | null>(null)

  const isStudent = user?.role === 'student'

  useEffect(() => {
    fetchDashboardData()
  }, [user])

  const fetchDashboardData = async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true)
    }
    try {
      if (isStudent) {
        // For students, fetch their personal attendance data
        const data = await attendanceService.getMyAttendance()
        setStudentData(data)
        setStats({
          totalStudents: 0,
          totalCourses: data.courses.length,
          totalSessions: data.overall_stats.total,
          attendanceRate: Math.round(data.overall_stats.percentage),
          todayAttendance: {
            present: data.overall_stats.present,
            absent: data.overall_stats.absent,
            leave: data.overall_stats.leave,
          },
        })
      } else {
        // For teachers/admins, fetch system-wide stats
        const [studentsRes, coursesRes, sessionsRes, todayRes] = await Promise.all([
          studentService.getStudents().catch(() => ({ count: 0, results: [] })),
          courseService.getCourses().catch(() => ({ count: 0, results: [] })),
          attendanceService.getSessions().catch(() => ({ count: 0, results: [] })),
          attendanceService.getTodayAttendance().catch(() => ({ 
            total: 0, 
            marked: 0, 
            present: 0, 
            leave: 0, 
            absent: 0, 
            percentage: 0 
          })),
        ])

        // Handle todayRes properly
        const todayStats = Array.isArray(todayRes) ? { 
          total: 0, 
          marked: 0, 
          present: 0, 
          leave: 0, 
          absent: 0, 
          percentage: 0 
        } : todayRes
        
        const present = todayStats.present || 0
        const leave = todayStats.leave || 0
        const absent = todayStats.absent || 0
        const rate = todayStats.percentage || 0

        setStats({
          totalStudents: studentsRes.count || 0,
          totalCourses: coursesRes.count || 0,
          totalSessions: sessionsRes.count || 0,
          attendanceRate: Math.round(rate),
          todayAttendance: { present, absent, leave },
        })
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    fetchDashboardData(true)
    toast.success('Dashboard refreshed!')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // Different stat cards for students
  const studentStatCards = [
    {
      title: 'Attendance Rate',
      value: `${stats.attendanceRate}%`,
      icon: IoTrendingUp,
      color: stats.attendanceRate >= 75 ? 'from-green-500 to-green-600' : 'from-red-500 to-red-600',
      link: '/profile',
    },
    {
      title: 'Enrolled Courses',
      value: stats.totalCourses,
      icon: IoBook,
      color: 'from-blue-500 to-blue-600',
      link: '/profile',
    },
    {
      title: 'Present',
      value: stats.todayAttendance.present,
      icon: IoCheckmarkCircle,
      color: 'from-emerald-500 to-emerald-600',
      link: '/profile',
    },
    {
      title: 'Total Classes',
      value: stats.totalSessions,
      icon: IoCalendar,
      color: 'from-purple-500 to-purple-600',
      link: '/profile',
    },
  ]

  // Teacher/Admin stat cards
  const teacherStatCards = [
    {
      title: 'Total Students',
      value: stats.totalStudents,
      icon: IoPeople,
      color: 'from-blue-500 to-blue-600',
      link: '/students',
    },
    {
      title: 'Total Courses',
      value: stats.totalCourses,
      icon: IoBook,
      color: 'from-purple-500 to-purple-600',
      link: '/courses',
    },
    {
      title: 'Total Sessions',
      value: stats.totalSessions,
      icon: IoCalendar,
      color: 'from-green-500 to-green-600',
      link: '/attendance',
    },
    {
      title: 'Attendance Rate',
      value: `${stats.attendanceRate}%`,
      icon: IoTrendingUp,
      color: 'from-orange-500 to-orange-600',
      link: '/reports',
    },
  ]

  const statCards = isStudent ? studentStatCards : teacherStatCards

  return (
    <div className="space-y-8">
      {/*div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">
              Welcome back, {user?.first_name}! 👋
            </h1>
            <p className="text-primary-100 text-lg">
              {isStudent 
                ? "Track your attendance and stay updated with your classes."
                : "Here's what's happening with your attendance system today."}
            </p>
          </div>
          <Button
            variant="secondary"
            onClick={handleRefresh}
            disabled={refreshing}
            className="bg-white/20 hover:bg-white/30 text-white border-white/30"
          >
            <IoRefresh className={`w-5 h-5 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </divelcome back, {user?.first_name}! 👋
        </h1>
        <p className="text-primary-100 text-lg">
          {isStudent 
            ? "Track your attendance and stay updated with your classes."
            : "Here's what's happening with your attendance system today."}
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Link to={stat.link}>
              <Card hoverable className="h-full">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm font-medium mb-1">
                      {stat.title}
                    </p>
                    <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                  <div
                    className={`w-16 h-16 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center`}
                  >
                    <stat.icon className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Course-wise Attendance for Students OR Quick Actions for Teachers */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <h2 className="text-2xl font-bold mb-6">
            {isStudent ? "Course-wise Attendance" : "Today's Attendance"}
          </h2>
          
          {isStudent ? (
            // Student Course-wise Attendance
            <div className="space-y-4">
              {studentData && studentData.courses && studentData.courses.length > 0 ? (
                studentData.courses.map((course) => (
                  <div
                    key={course.course_id}
                    className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-bold text-lg text-gray-900">{course.course_name}</h3>
                        <p className="text-gray-600 text-sm">{course.course_code}</p>
                      </div>
                      <div className="text-right">
                        <p
                          className={`text-2xl font-bold ${
                            course.percentage >= 75
                              ? 'text-green-600'
                              : course.percentage >= 60
                              ? 'text-yellow-600'
                              : 'text-red-600'
                          }`}
                        >
                          {course.percentage.toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-500">Attendance</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-4 mt-4">
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Total</p>
                        <p className="text-xl font-bold text-gray-900">{course.total_sessions}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Present</p>
                        <p className="text-xl font-bold text-green-600">{course.present}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Leave</p>
                        <p className="text-xl font-bold text-yellow-600">{course.leave}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Absent</p>
                        <p className="text-xl font-bold text-red-600">{course.absent}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <IoSchool className="w-16 h-16 mx-auto mb-3 text-gray-300" />
                  <p>No course enrollments found</p>
                </div>
              )}
            </div>
          ) : (
            // Teacher/Admin Today's Attendance Stats
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex items-center gap-4 p-4 bg-green-50 rounded-xl">
                <IoCheckmarkCircle className="w-12 h-12 text-green-600" />
                <div>
                  <p className="text-green-600 font-semibold text-sm">Present</p>
                  <p className="text-3xl font-bold text-green-700">
                    {stats.todayAttendance.present}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 p-4 bg-red-50 rounded-xl">
                <IoCloseCircle className="w-12 h-12 text-red-600" />
                <div>
                  <p className="text-red-600 font-semibold text-sm">Absent</p>
                  <p className="text-3xl font-bold text-red-700">
                    {stats.todayAttendance.absent}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 p-4 bg-yellow-50 rounded-xl">
                <IoTime className="w-12 h-12 text-yellow-600" />
                <div>
                  <p className="text-yellow-600 font-semibold text-sm">On Leave</p>
                  <p className="text-3xl font-bold text-yellow-700">
                    {stats.todayAttendance.leave}
                  </p>
                </div>
              </div>
            </div>
          )}
        </Card>
      </motion.div>

      {/* Quick Actions for Teachers Only */}
      {!isStudent && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <h2 className="text-2xl font-bold mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link
                to="/face-recognition"
                className="p-6 border-2 border-gray-200 rounded-xl hover:border-primary-500 hover:bg-primary-50 transition-all text-center group"
              >
                <div className="text-4xl mb-2">📸</div>
                <h3 className="font-semibold text-gray-900 group-hover:text-primary-600">
                  Face Recognition
                </h3>
                <p className="text-sm text-gray-600 mt-1">Mark attendance with AI</p>
              </Link>

              <Link
                to="/students"
                className="p-6 border-2 border-gray-200 rounded-xl hover:border-primary-500 hover:bg-primary-50 transition-all text-center group"
              >
                <div className="text-4xl mb-2">👥</div>
                <h3 className="font-semibold text-gray-900 group-hover:text-primary-600">
                  Manage Students
                </h3>
                <p className="text-sm text-gray-600 mt-1">View and edit student profiles</p>
              </Link>

              <Link
                to="/reports"
                className="p-6 border-2 border-gray-200 rounded-xl hover:border-primary-500 hover:bg-primary-50 transition-all text-center group"
              >
                <div className="text-4xl mb-2">📊</div>
                <h3 className="font-semibold text-gray-900 group-hover:text-primary-600">
                  View Reports
                </h3>
                <p className="text-sm text-gray-600 mt-1">Generate attendance reports</p>
              </Link>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Recent Attendance for Students */}
      {isStudent && studentData && studentData.recent_records && studentData.recent_records.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <h2 className="text-2xl font-bold mb-6">Recent Attendance Records</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Course
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Method
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {studentData.recent_records.map((record: any, index: number) => (
                    <tr key={record.id || index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(record.session_date || record.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.course_code || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.session_time || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            record.status === 'present'
                              ? 'bg-green-100 text-green-800'
                              : record.status === 'leave'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {record.status?.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.check_in_method_display || record.check_in_method || 'Manual'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  )
}

export default Dashboard
