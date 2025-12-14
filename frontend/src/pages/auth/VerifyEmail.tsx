import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { IoCheckmarkCircle, IoCloseCircle, IoArrowForward } from 'react-icons/io5'
import { Card, Button } from '@components/ui'
import { authService } from '@services/authService'
import api from '@services/api'
import toast from 'react-hot-toast'

const VerifyEmail = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [isVerifying, setIsVerifying] = useState(true)
  const [isSuccess, setIsSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [userEmail, setUserEmail] = useState('')

  useEffect(() => {
    verifyEmail()
  }, [searchParams])

  const verifyEmail = async () => {
    try {
      const token = searchParams.get('token')
      
      if (!token) {
        setErrorMessage('Verification token not found in URL.')
        setIsVerifying(false)
        return
      }

      // Fetch CSRF token first
      await api.get('/auth/csrf-token/')

      // Call the verify email endpoint
      const response = await authService.verifyEmail({ token })
      
      setUserEmail(response.user?.email || '')
      setIsSuccess(true)
      toast.success('Email verified successfully! You can now log in.')
    } catch (error: any) {
      const message = error.response?.data?.error || error.message || 'Failed to verify email. Token may be invalid or expired.'
      setErrorMessage(message)
      toast.error(message)
    } finally {
      setIsVerifying(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <Card className="p-8">
          {isVerifying ? (
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                >
                  <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full" />
                </motion.div>
              </div>
              <h2 className="text-2xl font-bold text-gray-800">Verifying Email...</h2>
              <p className="text-gray-600">Please wait while we verify your email address.</p>
            </div>
          ) : isSuccess ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center space-y-4"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 100 }}
                className="flex justify-center"
              >
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                  <IoCheckmarkCircle className="w-12 h-12 text-green-600" />
                </div>
              </motion.div>
              
              <div>
                <h2 className="text-2xl font-bold text-gray-800">Email Verified!</h2>
                <p className="text-gray-600 mt-2">
                  {userEmail && `Your email (${userEmail}) has been successfully verified.`}
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-6">
                <p className="text-green-800">
                  ✓ Your account is now active and ready to use!
                </p>
              </div>

              <div className="pt-6 space-y-3">
                <Button
                  onClick={() => navigate('/login')}
                  className="w-full"
                  variant="primary"
                >
                  <span className="flex items-center justify-center gap-2">
                    Go to Login
                    <IoArrowForward />
                  </span>
                </Button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center space-y-4"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 100 }}
                className="flex justify-center"
              >
                <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
                  <IoCloseCircle className="w-12 h-12 text-red-600" />
                </div>
              </motion.div>

              <div>
                <h2 className="text-2xl font-bold text-gray-800">Verification Failed</h2>
                <p className="text-gray-600 mt-2">{errorMessage}</p>
              </div>

              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-6">
                <p className="text-red-800 text-sm">
                  The verification token may have expired or is invalid. Please request a new verification email.
                </p>
              </div>

              <div className="pt-6 space-y-3">
                <Link to="/resend-verification">
                  <Button className="w-full" variant="primary">
                    Resend Verification Email
                  </Button>
                </Link>
                <Link to="/login">
                  <Button className="w-full" variant="outline">
                    Back to Login
                  </Button>
                </Link>
              </div>
            </motion.div>
          )}
        </Card>

        {!isVerifying && (
          <div className="text-center mt-6">
            <p className="text-gray-600 text-sm">
              {isSuccess ? (
                <>
                  Need help? <Link to="/contact" className="text-blue-600 hover:underline">Contact support</Link>
                </>
              ) : (
                <>
                  Go back to <Link to="/login" className="text-blue-600 hover:underline">login</Link>
                </>
              )}
            </p>
          </div>
        )}
      </motion.div>
    </div>
  )
}

export default VerifyEmail
