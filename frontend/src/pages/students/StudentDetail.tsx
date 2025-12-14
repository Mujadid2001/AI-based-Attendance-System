import { useState, useEffect } from 'react';
import { useParams, useHistory, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, LoadingSpinner, Badge, Button } from '@components/ui';
import { IoPerson, IoMail, IoSchool, IoIdCard, IoCalendar, IoCheckmarkCircle, IoCloseCircle } from 'react-icons/io5';
import { studentService } from '@services/index';
import type { StudentProfile } from '@/types';
import toast from 'react-hot-toast';

const StudentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const history = useHistory();
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudentDetails();
  }, [id]);

  const fetchStudentDetails = async () => {
    if (!id) return;
    try {
      const response = await studentService.getStudent(parseInt(id, 10));
      setStudent(response);
    } catch (error) {
      toast.error('Failed to load student details.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!student) return;
    if (window.confirm('Are you sure you want to delete this student?')) {
      try {
        await studentService.deleteStudent(student.id);
        toast.success('Student deleted successfully.');
        history.push('/students');
      } catch (error) {
        toast.error('Failed to delete student.');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!student) {
    return (
      <Card className="text-center py-12">
        <p className="text-gray-600">Student not found.</p>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      {/* Header */}
      <Card>
        <div className="flex items-center space-x-6">
          {student.user.profile_picture ? (
            <img
              src={student.user.profile_picture}
              alt={`${student.user.first_name} ${student.user.last_name}`}
              className="w-24 h-24 rounded-full object-cover"
            />
          ) : (
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
              <IoPerson className="w-12 h-12 text-white" />
            </div>
          )}
          <div className="flex-grow">
            <h1 className="text-3xl font-bold text-gray-900">
              {student.user.first_name} {student.user.last_name}
            </h1>
            <p className="text-gray-600">{student.student_id}</p>
          </div>
          <div className="flex space-x-2">
            <Link to={`/students/${id}/edit`}>
              <Button variant="outline">Edit</Button>
            </Link>
            <Button variant="danger" onClick={handleDelete}>Delete</Button>
          </div>
        </div>
      </Card>

      {/* Personal Details */}
      <Card>
        <h2 className="text-2xl font-bold mb-6">Personal Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <DetailItem icon={IoMail} label="Email" value={student.user.email} />
          <DetailItem icon={IoIdCard} label="Roll Number" value={student.student_id} />
          <DetailItem icon={IoSchool} label="Department" value={student.department || 'N/A'} />
          <DetailItem icon={IoCalendar} label="Semester" value={student.semester || 'N/A'} />
        </div>
      </Card>

      {/* Face Registration Status */}
      <Card>
        <h2 className="text-2xl font-bold mb-6">Face Registration</h2>
        <div className="flex items-center space-x-4">
          {student.face_registered ? (
            <>
              <IoCheckmarkCircle className="w-12 h-12 text-green-600" />
              <div>
                <Badge variant="success">Face Registered</Badge>
                <p className="text-sm text-gray-600 mt-1">
                  Face data is available for AI attendance.
                </p>
              </div>
            </>
          ) : (
            <>
              <IoCloseCircle className="w-12 h-12 text-red-600" />
              <div>
                <Badge variant="warning">No Face Data</Badge>
                <p className="text-sm text-gray-600 mt-1">
                  Student needs to register their face for AI attendance.
                </p>
              </div>
            </>
          )}
        </div>
      </Card>

      {/* Enrolled Courses */}
      <Card>
        <h2 className="text-2xl font-bold mb-6">Enrolled Courses</h2>
        <p className="text-gray-600">Enrolled courses section - Coming soon!</p>
      </Card>

      {/* Attendance History */}
      <Card>
        <h2 className="text-2xl font-bold mb-6">Attendance History</h2>
        <p className="text-gray-600">Attendance history section - Coming soon!</p>
      </Card>
    </motion.div>
  );
};

const DetailItem = ({ icon: Icon, label, value }: { icon: React.ElementType, label: string, value: string | number }) => (
  <div className="flex items-start space-x-4">
    <div className="bg-gray-100 p-3 rounded-lg">
      <Icon className="w-6 h-6 text-gray-600" />
    </div>
    <div>
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
    </div>
  </div>
);

export default StudentDetail;
