import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { IoLockClosed, IoEye, IoEyeOff, IoCheckmarkCircle } from 'react-icons/io5'
import { Button, Input } from '@components/ui'
import { authService } from '@services/authService'
import toast from 'react-hot-toast'

interface ResetPasswordForm {
  new_password: string
  new_password_confirm: string
}

const ResetPassword = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [resetSuccess, setResetSuccess] = useState(false)
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  
  const token = searchParams.get('token')

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordForm>()

  const password = watch('new_password')

  useEffect(() => {
    if (!token) {
      toast.error('Invalid or missing reset token')
      navigate('/login')
    }
  }, [token, navigate])

  const onSubmit = async (data: ResetPasswordForm) => {
    if (!token) return
    
    setIsLoading(true)
    try {
      await authService.resetPassword(token, data.new_password, data.new_password_confirm)
      setResetSuccess(true)
      toast.success('Password reset successful! You can now log in.')
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error || 
                          error.response?.data?.token?.[0] ||
                          'Failed to reset password'
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  if (!token) {
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-600 via-primary-700 to-secondary-600 p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              className={`w-20 h-20 ${
                resetSuccess 
                  ? 'bg-gradient-to-br from-green-500 to-green-600' 
                  : 'bg-gradient-to-br from-primary-600 to-secondary-600'
              } rounded-2xl flex items-center justify-center mx-auto mb-4`}
            >
              {resetSuccess ? (
                <IoCheckmarkCircle className="w-10 h-10 text-white" />
              ) : (
                <IoLockClosed className="w-10 h-10 text-white" />
              )}
            </motion.div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {resetSuccess ? 'Password Reset Complete!' : 'Reset Your Password'}
            </h1>
            <p className="text-gray-600">
              {resetSuccess 
                ? 'Your password has been successfully updated'
                : 'Enter your new password below'
              }
            </p>
          </div>

          {!resetSuccess ? (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="relative">
                <Input
                  label="New Password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter new password"
                  leftIcon={<IoLockClosed className="w-5 h-5 text-gray-400" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? (
                        <IoEyeOff className="w-5 h-5" />
                      ) : (
                        <IoEye className="w-5 h-5" />
                      )}
                    </button>
                  }
                  error={errors.new_password?.message}
                  {...register('new_password', {
                    required: 'Password is required',
                    minLength: {
                      value: 8,
                      message: 'Password must be at least 8 characters',
                    },
                    pattern: {
                      value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                      message: 'Password must contain at least one lowercase letter, one uppercase letter, and one number',
                    },
                  })}
                />
              </div>

              <div className="relative">
                <Input
                  label="Confirm New Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm new password"
                  leftIcon={<IoLockClosed className="w-5 h-5 text-gray-400" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      {showConfirmPassword ? (
                        <IoEyeOff className="w-5 h-5" />
                      ) : (
                        <IoEye className="w-5 h-5" />
                      )}
                    </button>
                  }
                  error={errors.new_password_confirm?.message}
                  {...register('new_password_confirm', {
                    required: 'Please confirm your password',
                    validate: (value) =>
                      value === password || 'Passwords do not match',
                  })}
                />
              </div>

              <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                <h3 className="text-sm font-medium text-blue-800 mb-2">Password Requirements:</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• At least 8 characters long</li>
                  <li>• Contains at least one lowercase letter</li>
                  <li>• Contains at least one uppercase letter</li>
                  <li>• Contains at least one number</li>
                </ul>
              </div>

              <Button type="submit" fullWidth isLoading={isLoading}>
                Reset Password
              </Button>
            </form>
          ) : (
            <div className="text-center">
              <div className="bg-green-50 text-green-800 p-6 rounded-lg mb-6">
                <IoCheckmarkCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
                <p className="font-medium text-lg mb-2">Success!</p>
                <p className="text-sm">
                  Your password has been successfully reset. You can now log in with your new password.
                </p>
              </div>
              
              <Button 
                onClick={() => navigate('/login')} 
                fullWidth
                className="bg-green-600 hover:bg-green-700"
              >
                Go to Login
              </Button>
            </div>
          )}

          {!resetSuccess && (
            <div className="mt-6 text-center">
              <Link
                to="/login"
                className="text-primary-600 hover:text-primary-700 font-medium text-sm"
              >
                Remember your password? Sign in
              </Link>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}

export default ResetPassword