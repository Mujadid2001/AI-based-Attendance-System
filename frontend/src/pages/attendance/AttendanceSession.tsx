import { Card } from '@components/ui'
import { useParams } from 'react-router-dom'

const AttendanceSession = () => {
  const { id } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Attendance Session - ID: {id}</h1>
      <Card>
        <p className="text-gray-600">Attendance session detail - Coming soon!</p>
      </Card>
    </div>
  )
}

export default AttendanceSession
