import { Link } from 'react-router-dom';
import { Card, Avatar, Button } from '@components/ui'
import { useAuthStore } from '@store/authStore'
import { IoPerson, IoMail, IoCall, IoPencil } from 'react-icons/io5'

const Profile = () => {
  const { user } = useAuthStore()

  if (!user) {
    return null
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">My Profile</h1>
      <Card>
        <div className="flex items-center space-x-6">
          <Avatar
            src={user.profile_picture}
            alt={`${user.first_name} ${user.last_name}`}
            size="xl"
          />
          <div>
            <h2 className="text-2xl font-bold">{user.first_name} {user.last_name}</h2>
            <p className="text-gray-600">{user.email}</p>
          </div>
          <div className="flex-grow text-right">
            <Link to="/profile/edit">
              <Button variant="outline">
                <IoPencil className="w-4 h-4 mr-2" />
                Edit Profile
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="text-xl font-bold mb-6">Personal Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-center space-x-4">
            <IoPerson className="w-8 h-8 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500">Full Name</p>
              <p className="font-semibold">{user.first_name} {user.last_name}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <IoMail className="w-8 h-8 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500">Email</p>
              <p className="font-semibold">{user.email}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <IoCall className="w-8 h-8 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500">Phone</p>
              <p className="font-semibold">{user.phone || 'N/A'}</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default Profile
