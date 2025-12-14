import { Card } from '@components/ui'
import { useParams } from 'react-router-dom'

const StudentDetail = () => {
  const { id } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Student Detail - ID: {id}</h1>
      <Card>
        <p className="text-gray-600">Student detail page - Coming soon!</p>
      </Card>
    </div>
  )
}

export default StudentDetail
