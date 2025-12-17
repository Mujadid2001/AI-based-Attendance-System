import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { IoAdd, IoCalendar, IoTime, IoPeople } from 'react-icons/io5';
import { Card, Button, LoadingSpinner, Badge, Input } from '@components/ui';
import { attendanceService, courseService } from '@services/index';
import type { AttendanceSession, Course } from '@/types';
import toast from 'react-hot-toast';

const Attendance = () => {
  const location = useLocation();
  const preselectedCourseId = location.state?.preselectedCourseId;
  
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    course: preselectedCourseId || '',
    date: new Date().toISOString().split('T')[0],
    start_time: new Date().toTimeString().split(' ')[0].substring(0, 5),
    is_active: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
    // Auto-open modal if preselected course
    if (preselectedCourseId) {
      setShowModal(true);
    }
  }, []);

  const fetchData = async () => {
    try {
      const [sessionsRes, coursesRes] = await Promise.all([
        attendanceService.getSessions(),
        courseService.getCourses({ is_active: true }),
      ]);
      setSessions(sessionsRes.results);
      setCourses(coursesRes.results);
    } catch (error) {
      toast.error('Failed to load data.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.course) {
      toast.error('Please select a course.');
      return;
    }
    setIsSubmitting(true);
    try {
      const newSession = await attendanceService.createSession(formData);
      setSessions([newSession, ...sessions]);
      toast.success('Session created successfully!');
      setShowModal(false);
      setFormData({
        course: '',
        date: new Date().toISOString().split('T')[0],
        start_time: new Date().toTimeString().split(' ')[0].substring(0, 5),
        is_active: true,
      });
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to create session.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Attendance Sessions</h1>
          <p className="text-gray-600 mt-1">Manage attendance-taking sessions</p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <IoAdd className="w-5 h-5 mr-2" />
          Create Session
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sessions.map((session, index) => (
          <motion.div
            key={session.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Link to={`/attendance/session/${session.id}`}>
              <Card hoverable>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">
                    {session.course_name || (typeof session.course === 'object' ? session.course.name : 'Unknown Course')}
                  </h3>
                  {session.is_active ? (
                    <Badge variant="success" size="sm">Active</Badge>
                  ) : (
                    <Badge variant="default" size="sm">Inactive</Badge>
                  )}
                </div>
                <div className="text-sm text-gray-600 space-y-2">
                  <div className="flex items-center">
                    <IoCalendar className="w-4 h-4 mr-2" />
                    {new Date(session.date).toLocaleDateString()}
                  </div>
                  <div className="flex items-center">
                    <IoTime className="w-4 h-4 mr-2" />
                    {session.start_time} {session.end_time ? `- ${session.end_time}` : '- Ongoing'}
                  </div>
                  <div className="flex items-center">
                    <IoPeople className="w-4 h-4 mr-2" />
                    {session.attendance_count || 0} Students
                  </div>
                </div>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

      {sessions.length === 0 && (
        <Card className="text-center py-12">
          <p className="text-gray-600">No attendance sessions found</p>
        </Card>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl shadow-xl max-w-md w-full"
          >
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Session</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Course
                  </label>
                  <select
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    value={formData.course}
                    onChange={(e) => setFormData({ ...formData, course: e.target.value })}
                  >
                    <option value="">Select a course</option>
                    {courses.map((course) => (
                      <option key={course.id} value={course.id}>
                        {course.name} ({course.code})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date
                  </label>
                  <input
                    type="date"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Time
                  </label>
                  <input
                    type="time"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    required
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                    Active
                  </label>
                </div>
                <div className="flex gap-3 mt-6">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setShowModal(false)}
                    fullWidth
                  >
                    Cancel
                  </Button>
                  <Button type="submit" fullWidth isLoading={isSubmitting}>
                    Create Session
                  </Button>
                </div>
              </form>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default Attendance;
