import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, LoadingSpinner, Badge, Button } from '@components/ui';
import { IoPerson, IoMail, IoSchool, IoIdCard, IoCalendar, IoCheckmarkCircle, IoCloseCircle, IoArrowBack, IoCamera, IoBook } from 'react-icons/io5';
import { studentService, courseService } from '@services/index';
import type { StudentProfile, Enrollment, Course } from '@/types';
import toast from 'react-hot-toast';

const StudentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingCourses, setLoadingCourses] = useState(false);

  useEffect(() => {
    fetchStudentDetails();
  }, [id]);

  const fetchStudentDetails = async () => {
    if (!id) return;
    try {
      const response = await studentService.getStudent(parseInt(id, 10));
      setStudent(response);
      
      // Fetch student enrollments
      setLoadingCourses(true);
      try {
        const enrollmentsData = await courseService.getStudentEnrollments(parseInt(id, 10));
        // Handle paginated response
        const enrollmentsList = Array.isArray(enrollmentsData) ? enrollmentsData : enrollmentsData.results || [];
        setEnrollments(enrollmentsList);
        
        // Fetch course details for each enrollment
        if (enrollmentsList.length > 0) {
          const courseIds = enrollmentsList.map(e => e.course);
          const coursePromises = courseIds.map(courseId => 
            courseService.getCourse(courseId).catch(() => null)
          );
          const coursesData = await Promise.all(coursePromises);
          setCourses(coursesData.filter(c => c !== null) as Course[]);
        }
      } catch (error) {
        console.error('Failed to load enrollments:', error);
      } finally {
        setLoadingCourses(false);
      }
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
        await studentService.deleteStudent(student.user.id);
        toast.success('Student deleted successfully.');
        navigate('/students');
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
      {/* Back Button */}
      <Button variant="secondary" onClick={() => navigate('/students')}>
        <IoArrowBack className="w-5 h-5 mr-2" />
        Back to Students
      </Button>

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
            <p className="text-gray-600">{student.roll_number}</p>
          </div>
          <div className="flex space-x-2">
            {!student.is_face_registered && (
              <Link to={`/face-registration`} state={{ 
                prefilledRollNumber: student.roll_number,
                studentEmail: student.user.email,
                studentName: `${student.user.first_name} ${student.user.last_name}`
              }}>
                <Button variant="secondary">
                  <IoCamera className="w-5 h-5 mr-2" />
                  Register Face
                </Button>
              </Link>
            )}
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
          <DetailItem icon={IoIdCard} label="Roll Number" value={student.roll_number} />
          <DetailItem icon={IoSchool} label="Department" value={student.department || 'N/A'} />
          <DetailItem icon={IoCalendar} label="Semester" value={student.semester || 'N/A'} />
        </div>
        
        {/* Email Verification Status */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-4">
            {student.user.is_verified ? (
              <>
                <IoCheckmarkCircle className="w-8 h-8 text-green-600" />
                <div>
                  <Badge variant="success" size="sm">Email Verified</Badge>
                  <p className="text-sm text-gray-600 mt-1">
                    Student email has been verified.
                  </p>
                </div>
              </>
            ) : (
              <>
                <IoCloseCircle className="w-8 h-8 text-red-600" />
                <div>
                  <Badge variant="danger" size="sm">Email Unverified</Badge>
                  <p className="text-sm text-gray-600 mt-1">
                    Student needs to verify their email address before they can login.
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Face Registration Status */}
      <Card>
        <h2 className="text-2xl font-bold mb-6">Face Registration</h2>
        <div className="flex items-center space-x-4">
          {student.is_face_registered ? (
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
        {loadingCourses ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : enrollments.length === 0 ? (
          <div className="text-center py-8">
            <IoBook className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600">No courses enrolled yet.</p>
          </div>
        ) : courses.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600 mb-4">Enrolled in {enrollments.length} course(s), but unable to load course details.</p>
            <div className="space-y-2">
              {enrollments.map((enrollment) => (
                <div key={enrollment.id} className="p-4 border border-gray-200 rounded-lg">
                  <p className="font-medium">Course ID: {enrollment.course}</p>
                  <p className="text-sm text-gray-600">Course Code: {enrollment.course_code}</p>
                  <p className="text-sm text-gray-600">Course Name: {enrollment.course_name}</p>
                  <Badge variant={enrollment.is_active ? 'success' : 'warning'}>
                    {enrollment.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {courses.map((course) => {
              const enrollment = enrollments.find(e => e.course === course.id);
              return (
                <Link
                  key={course.id}
                  to={`/courses/${course.id}`}
                  className="block p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">
                        {course.code}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2">{course.name}</p>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <span>{course.semester} {course.year}</span>
                        <span>•</span>
                        <span>{course.instructor_name}</span>
                      </div>
                    </div>
                    <Badge variant={enrollment?.is_active ? 'success' : 'warning'}>
                      {enrollment?.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
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
