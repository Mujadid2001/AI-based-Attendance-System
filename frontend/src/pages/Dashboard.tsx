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
} from 'react-icons/io5'
import { Card, LoadingSpinner } from '@components/ui'
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
    late: number
  }
}

const Dashboard = () => {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    totalStudents: 0,
    totalCourses: 0,
    totalSessions: 0,
    attendanceRate: 0,
    todayAttendance: { present: 0, absent: 0, late: 0 },
  })

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [studentsRes, coursesRes, sessionsRes, todayRes] = await Promise.all([
        studentService.getStudents().catch(() => ({ count: 0, results: [] })),
        courseService.getCourses().catch(() => ({ count: 0, results: [] })),
        attendanceService.getSessions().catch(() => ({ count: 0, results: [] })),
        attendanceService.getTodayAttendance().catch(() => ({ total: 0, marked: 0, percentage: 0 })),
      ])

      // Handle todayRes as object with stats, not array
      const todayStats = Array.isArray(todayRes) ? { total: 0, marked: 0, percentage: 0 } : todayRes
      const present = todayStats.marked || 0
      const total = todayStats.total || 0
      const absent = total - present
      const rate = todayStats.percentage || 0

      setStats({
        totalStudents: studentsRes.count || 0,
        totalCourses: coursesRes.count || 0,
        totalSessions: sessionsRes.count || 0,
        attendanceRate: Math.round(rate),
        todayAttendance: { present, absent, late: 0 },
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      toast.error('Failed to load dashboard data')
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

  const statCards = [
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

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 text-white shadow-xl"
      >
        <h1 className="text-4xl font-bold mb-2">
          Welcome back, {user?.first_name}! 👋
        </h1>
        <p className="text-primary-100 text-lg">
          Here's what's happening with your attendance system today.
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

      {/* Today's Attendance */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <h2 className="text-2xl font-bold mb-6">Today's Attendance</h2>
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
                <p className="text-yellow-600 font-semibold text-sm">Late</p>
                <p className="text-3xl font-bold text-yellow-700">
                  {stats.todayAttendance.late}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Quick Actions */}
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
    </div>
  )
}

export default Dashboard
