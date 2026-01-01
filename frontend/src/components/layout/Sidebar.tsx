import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { useAuthStore } from '@store/authStore'
import {
  IoGrid,
  IoPeople,
  IoBook,
  IoCalendar,
  IoCamera,
  IoStatsChart,
  IoSettings,
  IoChevronBack,
  IoPersonAdd,
  IoPhonePortrait,
} from 'react-icons/io5'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

const Sidebar = ({ isOpen, onToggle }: SidebarProps) => {
  const location = useLocation()
  const { user } = useAuthStore()

  const menuItems = [
    { path: '/dashboard', icon: IoGrid, label: 'Dashboard', roles: ['admin', 'teacher', 'student'] },
    { path: '/students', icon: IoPeople, label: 'Students', roles: ['admin', 'teacher'] },
    { path: '/courses', icon: IoBook, label: 'Courses', roles: ['admin', 'teacher'] },
    { path: '/attendance', icon: IoCalendar, label: 'Attendance', roles: ['admin', 'teacher'] },
    { path: '/face-recognition', icon: IoCamera, label: 'Face Recognition', roles: ['admin', 'teacher'] },
    { path: '/face-registration', icon: IoPersonAdd, label: 'Face Registration', roles: ['admin', 'teacher'] },
    { path: '/external-cameras', icon: IoPhonePortrait, label: 'External Cameras', roles: ['admin', 'teacher'] },
    { path: '/reports', icon: IoStatsChart, label: 'Reports', roles: ['admin', 'teacher'] },
    { path: '/settings', icon: IoSettings, label: 'Settings', roles: ['admin', 'teacher', 'student'] },
  ]

  // Filter menu items based on user role
  const filteredMenuItems = menuItems.filter(item => 
    user && item.roles.includes(user.role)
  )

  return (
    <motion.aside
      initial={false}
      animate={{ width: isOpen ? 280 : 80 }}
      transition={{ duration: 0.3 }}
      className="bg-gradient-to-b from-primary-900 to-primary-800 text-white shadow-2xl relative"
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-6 border-b border-primary-700">
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="font-bold text-xl"
          >
            AI Attendance
          </motion.div>
        )}
        <button
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-primary-700 transition-colors"
        >
          <motion.div
            animate={{ rotate: isOpen ? 0 : 180 }}
            transition={{ duration: 0.3 }}
          >
            <IoChevronBack className="w-5 h-5" />
          </motion.div>
        </button>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2">
        {filteredMenuItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/')

          return (
            <Link key={item.path} to={item.path}>
              <motion.div
                whileHover={{ x: 4 }}
                className={clsx(
                  'flex items-center gap-4 px-4 py-3 rounded-lg transition-colors relative',
                  isActive
                    ? 'bg-primary-700 text-white shadow-lg'
                    : 'text-primary-100 hover:bg-primary-700/50'
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute inset-0 bg-primary-700 rounded-lg"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Icon className="w-6 h-6 relative z-10 flex-shrink-0" />
                {isOpen && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="font-medium relative z-10"
                  >
                    {item.label}
                  </motion.span>
                )}
              </motion.div>
            </Link>
          )
        })}
      </nav>
    </motion.aside>
  )
}

export default Sidebar
