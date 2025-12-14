import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { IoHome, IoSad } from 'react-icons/io5'
import { Button } from '@components/ui'

const NotFound = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <motion.div
          animate={{ y: [0, -20, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="text-9xl font-bold text-primary-600 mb-4"
        >
          404
        </motion.div>
        
        <IoSad className="w-24 h-24 text-gray-400 mx-auto mb-6" />
        
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Page Not Found</h1>
        <p className="text-xl text-gray-600 mb-8 max-w-md">
          Oops! The page you're looking for doesn't exist or has been moved.
        </p>
        
        <Link to="/dashboard">
          <Button size="lg">
            <IoHome className="w-5 h-5 mr-2" />
            Go to Dashboard
          </Button>
        </Link>
      </motion.div>
    </div>
  )
}

export default NotFound
