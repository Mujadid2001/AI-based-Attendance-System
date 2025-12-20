import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Webcam from 'react-webcam';
import { Card, LoadingSpinner, Badge, Button, Modal } from '@components/ui';
import { IoArrowBack, IoCheckmarkCircle, IoCloseCircle, IoHelpCircle, IoCamera, IoClose, IoLockClosed } from 'react-icons/io5';
import { attendanceService, courseService, aiService } from '@services/index';
import type { AttendanceSession, AttendanceRecord, StudentProfile } from '@/types';
import { useAuthStore } from '@store/authStore';
import toast from 'react-hot-toast';

const AttendanceSessionDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [session, setSession] = useState<AttendanceSession | null>(null);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFaceRecognition, setShowFaceRecognition] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedImages, setCapturedImages] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const webcamRef = useRef<Webcam>(null);
  
  // Check if session is editable (active OR user is admin)
  const isEditable = session?.is_active || user?.role === 'admin';

  useEffect(() => {
    fetchSessionDetails();
  }, [id]);

  const fetchSessionDetails = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const sessionData = await attendanceService.getSession(parseInt(id, 10));
      console.log('Session data:', sessionData);
      setSession(sessionData);

      const recordsData = await attendanceService.getSessionRecords(parseInt(id, 10));
      console.log('Loaded records:', recordsData.length);
      setRecords(recordsData);

      // Extract course ID - it can be either a number or an object with id
      const courseId = typeof sessionData.course === 'number' 
        ? sessionData.course 
        : sessionData.course?.id;

      if (courseId) {
        const courseStudents = await courseService.getCourseEnrollments(courseId);
        const studentProfiles = courseStudents.map((enrollment: any) => enrollment.student);
        console.log('Loaded students count:', studentProfiles.length);
        setStudents(studentProfiles);
      } else {
        console.error('No valid course ID found in session data');
        toast.error('Course information is missing');
      }
    } catch (error) {
      console.error('Failed to load session details:', error);
      toast.error('Failed to load session details.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAttendance = async (studentId: number, status: 'present' | 'absent' | 'leave') => {
    if (!id) return;
    
    console.log('Marking attendance:', JSON.stringify({ sessionId: id, studentId, status }, null, 2));
    
    try {
      // Check if attendance already exists for this student
      const existingRecord = records.find((r) => {
        const recordStudentId = r.student.id || r.student.user?.id;
        return recordStudentId === studentId;
      });
      
      if (existingRecord) {
        // Update existing record
        console.log('Updating existing record ID:', existingRecord.id);
        console.log('Full existing record:', JSON.stringify(existingRecord, null, 2));
        
        const updatedRecord = await attendanceService.updateAttendance(existingRecord.id, {
          status,
        });
        setRecords(records.map((r) => (r.id === existingRecord.id ? updatedRecord : r)));
        toast.success('Attendance updated successfully.');
      } else {
        // Create new record
        console.log('Creating new record');
        const payload = {
          session: parseInt(id, 10),
          student: studentId,
          status,
        };
        console.log('Payload:', JSON.stringify(payload, null, 2));
        const newRecord = await attendanceService.markAttendance(payload);
        setRecords([...records, newRecord]);
        toast.success('Attendance marked successfully.');
      }
    } catch (error: any) {
      console.error('Failed to mark attendance:', error);
      console.error('Error response:', JSON.stringify(error?.response?.data, null, 2));
      const errorData = error?.response?.data;
      let errorMessage = 'Failed to mark attendance.';
      
      if (errorData) {
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else {
          // Try to format field errors
          const fieldErrors = Object.entries(errorData)
            .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
            .join('; ');
          if (fieldErrors) errorMessage = fieldErrors;
        }
      }
      
      toast.error(errorMessage);
    }
  };

  const captureImage = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        setCapturedImages([...capturedImages, imageSrc]);
        toast.success(`Captured ${capturedImages.length + 1} image(s)`);
      }
    }
  };

  const dataURLtoFile = (dataurl: string, filename: string): File => {
    const arr = dataurl.split(',');
    const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  };

  const handleBulkFaceRecognition = async () => {
    if (!id || capturedImages.length === 0) {
      toast.error('Please capture at least one image');
      return;
    }

    setIsProcessing(true);
    try {
      // Convert captured images to File objects
      const imageFiles = capturedImages.map((img, index) =>
        dataURLtoFile(img, `capture_${index}.jpg`)
      );

      // Call bulk recognition API
      const result = await aiService.bulkRecognizeAttendance(parseInt(id, 10), imageFiles);

      toast.success(
        `Attendance marked: ${result.summary.marked_present} present, ${result.summary.marked_absent} absent`
      );

      // Refresh records
      await fetchSessionDetails();

      // Close modal and reset
      setShowFaceRecognition(false);
      setCapturedImages([]);
    } catch (error: any) {
      console.error('Face recognition failed:', error);
      toast.error(error?.response?.data?.error || 'Face recognition failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCloseSession = async () => {
    if (!id) return;
    
    if (!confirm('Are you sure you want to close this session? This action cannot be undone.')) {
      return;
    }

    try {
      const updatedSession = await attendanceService.closeSession(parseInt(id, 10));
      setSession(updatedSession);
      toast.success('Session closed successfully!');
    } catch (error: any) {
      console.error('Failed to close session:', error);
      toast.error(error?.response?.data?.error || 'Failed to close session');
    }
  };

  const removeCapturedImage = (index: number) => {
    setCapturedImages(capturedImages.filter((_, i) => i !== index));
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
    const record = records.find((r) => {
      const recordStudentId = r.student.id || r.student.user?.id;
      return recordStudentId === studentId;
    });
    return record ? record.status : 'unmarked';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <Button variant="secondary" onClick={() => navigate('/attendance')}>
        <IoArrowBack className="w-5 h-5 mr-2" />
        Back to Sessions
      </Button>
      
      {/* Course and Session Information */}
      <Card>
        <div className="space-y-4">
          {/* Course Name */}
          <div>
            <h1 className="text-3xl font-bold mb-2">
              {session.course_name || `Course ${typeof session.course === 'number' ? session.course : session.course?.id || 'N/A'}`}
            </h1>
            {session.course_code && (
              <p className="text-gray-500 text-sm">Course Code: {session.course_code}</p>
            )}
          </div>

          {/* Session Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t">
            <div>
              <p className="text-sm text-gray-500 font-medium">Session Date</p>
              <p className="text-lg font-semibold">
                {new Date(session.date + 'T00:00:00').toLocaleDateString('en-US', {
                  weekday: 'short',
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric'
                })}
              </p>
            </div>
            
            <div>
              <p className="text-sm text-gray-500 font-medium">Start Time</p>
              <p className="text-lg font-semibold">
                {session.start_time}
              </p>
            </div>
            
            {session.end_time && (
              <div>
                <p className="text-sm text-gray-500 font-medium">End Time</p>
                <p className="text-lg font-semibold">
                  {session.end_time}
                </p>
              </div>
            )}
            
            {session.duration_minutes && session.duration_minutes > 0 && (
              <div>
                <p className="text-sm text-gray-500 font-medium">Duration</p>
                <p className="text-lg font-semibold">{session.duration_minutes} minutes</p>
              </div>
            )}
            
            <div>
              <p className="text-sm text-gray-500 font-medium">Status</p>
              <p className="text-lg">
                <Badge variant={session.is_active ? 'success' : 'default'}>
                  {session.is_active ? 'Active' : 'Closed'}
                </Badge>
              </p>
            </div>
            
            {session.created_by_name && (
              <div>
                <p className="text-sm text-gray-500 font-medium">Created By</p>
                <p className="text-lg font-semibold">{session.created_by_name}</p>
              </div>
            )}
            
            <div>
              <p className="text-sm text-gray-500 font-medium">Attendance Marked</p>
              <p className="text-lg font-semibold">
                {records.length} / {students.length}
              </p>
            </div>
            
            <div>
              <p className="text-sm text-gray-500 font-medium">Session Created</p>
              <p className="text-lg font-semibold">
                {new Date(session.created_at).toLocaleString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        {!session.is_active && user?.role !== 'admin' && (
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-3">
            <IoLockClosed className="w-5 h-5 text-yellow-600" />
            <div>
              <p className="font-medium text-yellow-900">Session Closed</p>
              <p className="text-sm text-yellow-700">This attendance session has been completed and can no longer be modified.</p>
            </div>
          </div>
        )}
        
        {!session.is_active && user?.role === 'admin' && (
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-3">
            <IoLockClosed className="w-5 h-5 text-blue-600" />
            <div>
              <p className="font-medium text-blue-900">Session Closed (Admin Override)</p>
              <p className="text-sm text-blue-700">As an admin, you can still modify this closed session.</p>
            </div>
          </div>
        )}
        
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Enrolled Students</h2>
          <div className="flex gap-3">
            {session.is_active && (
              <Button onClick={handleCloseSession} variant="secondary">
                Complete Session
              </Button>
            )}
            {isEditable && (
              <Button onClick={() => setShowFaceRecognition(true)} variant="primary">
                <IoCamera className="w-5 h-5 mr-2" />
                Start Face Recognition
              </Button>
            )}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4">Student</th>
                <th className="text-left py-3 px-4">Roll Number</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-left py-3 px-4">Recorded At</th>
                <th className="text-left py-3 px-4">Method</th>
                <th className="text-left py-3 px-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => {
                // Get student ID from either id field or user.id (primary key)
                const studentId = student.id || student.user?.id;
                const status = getStudentStatus(studentId);
                const firstName = student.user?.first_name || '';
                const lastName = student.user?.last_name || '';
                const fullName = `${firstName} ${lastName}`.trim() || 'Unknown Student';
                
                // Find the attendance record for this student
                const record = records.find((r) => {
                  const recordStudentId = r.student.id || r.student.user?.id;
                  return recordStudentId === studentId;
                });
                
                return (
                  <tr key={studentId} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div>
                        <p className="font-medium">{fullName}</p>
                        {record?.recorded_by_name && (
                          <p className="text-xs text-gray-500">By: {record.recorded_by_name}</p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {student.roll_number || 'N/A'}
                    </td>
                    <td className="py-3 px-4">
                      {status === 'present' && <Badge variant="success">Present</Badge>}
                      {status === 'absent' && <Badge variant="danger">Absent</Badge>}
                      {status === 'leave' && <Badge variant="warning">On Leave</Badge>}
                      {status === 'unmarked' && <Badge variant="default">Unmarked</Badge>}
                    </td>
                    <td className="py-3 px-4">
                      {record ? (
                        <div className="text-sm">
                          {record.check_in_time ? (
                            <>
                              <p className="font-medium">{record.check_in_time}</p>
                              {record.session_date && (
                                <p className="text-xs text-gray-500">
                                  {new Date(record.session_date + 'T00:00:00').toLocaleDateString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    year: 'numeric'
                                  })}
                                </p>
                              )}
                            </>
                          ) : record.created_at ? (
                            <>
                              <p className="font-medium">
                                {new Date(record.created_at).toLocaleTimeString('en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit',
                                  hour12: true
                                })}
                              </p>
                              <p className="text-xs text-gray-500">
                                {new Date(record.created_at).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric'
                                })}
                              </p>
                            </>
                          ) : (
                            <span className="text-gray-400">Not recorded</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">Not recorded</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {record?.check_in_method ? (
                        <span className="text-sm">
                          {record.check_in_method_display || record.check_in_method}
                          {record.confidence_score && (
                            <span className="text-xs text-gray-500 block">
                              {Math.round(record.confidence_score * 100)}% confidence
                            </span>
                          )}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {isEditable ? (
                        <div className="flex space-x-2">
                          <Button 
                            size="sm" 
                            variant="success" 
                            onClick={() => handleMarkAttendance(studentId, 'present')}
                            title="Mark as Present"
                          >
                            <IoCheckmarkCircle className="w-4 h-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="danger" 
                            onClick={() => handleMarkAttendance(studentId, 'absent')}
                            title="Mark as Absent"
                          >
                            <IoCloseCircle className="w-4 h-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="warning" 
                            onClick={() => handleMarkAttendance(studentId, 'leave')}
                            title="Mark as On Leave"
                          >
                            <IoHelpCircle className="w-4 h-4" />
                          </Button>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400 italic">Locked</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Face Recognition Modal */}
      {showFaceRecognition && (
        <Modal
          isOpen={showFaceRecognition}
          onClose={() => {
            setShowFaceRecognition(false);
            setCapturedImages([]);
          }}
          title="Face Recognition Attendance"
          size="xl"
        >
          <div className="space-y-4">
            <p className="text-gray-600">
              Capture images of students to automatically mark attendance. Recognized students will be marked
              as present, others as absent.
            </p>

            {/* Webcam */}
            <div className="relative bg-black rounded-lg overflow-hidden">
              <Webcam
                ref={webcamRef}
                audio={false}
                screenshotFormat="image/jpeg"
                className="w-full"
                videoConstraints={{
                  width: 1280,
                  height: 720,
                  facingMode: 'user',
                }}
              />
            </div>

            {/* Capture Button */}
            <div className="flex justify-center">
              <Button onClick={captureImage} disabled={isProcessing}>
                <IoCamera className="w-5 h-5 mr-2" />
                Capture Image
              </Button>
            </div>

            {/* Captured Images */}
            {capturedImages.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-semibold">Captured Images ({capturedImages.length})</h3>
                <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
                  {capturedImages.map((img, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={img}
                        alt={`Capture ${index + 1}`}
                        className="w-full h-24 object-cover rounded"
                      />
                      <button
                        onClick={() => removeCapturedImage(index)}
                        className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <IoClose className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowFaceRecognition(false);
                  setCapturedImages([]);
                }}
                disabled={isProcessing}
              >
                Cancel
              </Button>
              <Button
                onClick={handleBulkFaceRecognition}
                disabled={capturedImages.length === 0 || isProcessing}
              >
                {isProcessing ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    <IoCheckmarkCircle className="w-5 h-5 mr-2" />
                    Process Attendance
                  </>
                )}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </motion.div>
  );
};

export default AttendanceSessionDetail;
