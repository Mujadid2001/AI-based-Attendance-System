import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Card, Button, Input } from '@components/ui'
import { useAuthStore } from '@store/authStore'
import { authService } from '@services/index'
import toast from 'react-hot-toast'

const EditProfile = () => {
  const navigate = useNavigate()
  const { user, setUser } = useAuthStore()
  
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name,
        last_name: user.last_name,
        phone: user.phone || '',
      })
    }
  }, [user])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const updatedUser = await authService.updateProfile(formData)
      setUser(updatedUser)
      toast.success('Profile updated successfully')
      navigate('/profile')
    } catch (error: any) {
      console.error('Profile update error:', error)
      if (error.response?.data) {
        const errors = error.response.data
        if (typeof errors === 'object') {
          Object.keys(errors).forEach(key => {
            const messages = Array.isArray(errors[key]) ? errors[key] : [errors[key]]
            messages.forEach((msg: string) => toast.error(`${key}: ${msg}`))
          })
        } else {
          toast.error('Failed to update profile')
        }
      } else {
        toast.error('Failed to update profile')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Edit Profile</h1>
          <p className="text-gray-600 mt-1">Update your personal information.</p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label="First Name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              required
            />
            <Input
              label="Last Name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              required
            />
          </div>

          <Input
            label="Email"
            type="email"
            value={user?.email || ''}
            disabled
            helperText="Email cannot be changed"
          />

          <Input
            label="Phone"
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={handleChange}
            placeholder="e.g., +92-300-1234567"
          />

          <div className="flex justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/profile')}
            >
              Cancel
            </Button>
            <Button type="submit" isLoading={loading}>
              Save Changes
            </Button>
          </div>
        </form>
      </Card>
    </motion.div>
  )
}

export default EditProfile
