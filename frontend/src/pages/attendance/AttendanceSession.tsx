import { useState, useEffect } from 'react';
import { useParams, useHistory } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, LoadingSpinner, Badge, Button } from '@components/ui';
import { IoArrowBack, IoCheckmarkCircle, IoCloseCircle, IoHelpCircle } from 'react-icons/io5';
import { attendanceService, courseService } from '@services/index';
import type { AttendanceSession, AttendanceRecord, StudentProfile } from '@/types';
import toast from 'react-hot-toast';

const AttendanceSessionDetail = () => {
  const { id } = useParams<{ id: string }>();
  const history = useHistory();
  const [session, setSession] = useState<AttendanceSession | null>(null);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessionDetails();
  }, [id]);

  const fetchSessionDetails = async () => {
    if (!id) return;
    try {
      const sessionData = await attendanceService.getSession(parseInt(id, 10));
      setSession(sessionData);

      const recordsData = await attendanceService.getSessionRecords(parseInt(id, 10));
      setRecords(recordsData);

      if (sessionData.course) {
        const courseStudents = await courseService.getCourseEnrollments(sessionData.course.id);
        // This is a placeholder. I'll need to check the actual service implementation
        const studentProfiles = courseStudents.map((enrollment: any) => enrollment.student);
        setStudents(studentProfiles);
      }
    } catch (error) {
      toast.error('Failed to load session details.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAttendance = async (studentId: number, status: 'present' | 'absent' | 'late') => {
    if (!id) return;
    try {
      const newRecord = await attendanceService.markAttendance({
        session: parseInt(id, 10),
        student: studentId,
        status,
      });
      setRecords([...records, newRecord]);
      toast.success('Attendance marked successfully.');
    } catch (error) {
      toast.error('Failed to mark attendance.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!session) {
    return (
      <Card className="text-center py-12">
        <p className="text-gray-600">Attendance session not found.</p>
      </Card>
    );
  }

  const getStudentStatus = (studentId: number) => {
    const record = records.find((r) => r.student.id === studentId);
    return record ? record.status : 'unmarked';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <Button variant="secondary" onClick={() => history.push('/attendance')}>
        <IoArrowBack className="w-5 h-5 mr-2" />
        Back to Sessions
      </Button>
      <Card>
        <h1 className="text-3xl font-bold">{session.course.name}</h1>
        <p className="text-gray-600">
          {new Date(session.start_time).toLocaleString()}
        </p>
      </Card>

      <Card>
        <h2 className="text-2xl font-bold mb-6">Enrolled Students</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4">Student</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-left py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => {
                const status = getStudentStatus(student.id);
                return (
                  <tr key={student.id} className="border-b">
                    <td className="py-3 px-4">{student.user.first_name} {student.user.last_name}</td>
                    <td className="py-3 px-4">
                      {status === 'present' && <Badge variant="success">Present</Badge>}
                      {status === 'absent' && <Badge variant="danger">Absent</Badge>}
                      {status === 'late' && <Badge variant="warning">Late</Badge>}
                      {status === 'unmarked' && <Badge variant="default">Unmarked</Badge>}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex space-x-2">
                        <Button size="sm" variant="success" onClick={() => handleMarkAttendance(student.id, 'present')}>
                          <IoCheckmarkCircle className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="danger" onClick={() => handleMarkAttendance(student.id, 'absent')}>
                          <IoCloseCircle className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="warning" onClick={() => handleMarkAttendance(student.id, 'late')}>
                          <IoHelpCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
};

export default AttendanceSessionDetail;
