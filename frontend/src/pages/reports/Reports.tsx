import { useState, useEffect } from 'react';
import { Card, Button, Input } from '@components/ui';
import { IoBarChart, IoFilter, IoDownload } from 'react-icons/io5';
import { attendanceService, courseService } from '@services/index';
import type { Course, AttendanceReport } from '@/types';
import toast from 'react-hot-toast';

const Reports = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reportData, setReportData] = useState<AttendanceReport[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const coursesRes = await courseService.getCourses();
      setCourses(coursesRes.results);
    } catch (error) {
      toast.error('Failed to load courses.');
    } finally {
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedCourse) {
      toast.error('Please select a course.');
      return;
    }
    
    if (!startDate || !endDate) {
      toast.error('Please select start and end dates.');
      return;
    }
    
    setLoading(true);
    try {
      const reportRes = await attendanceService.generateAttendanceReport({
        course: parseInt(selectedCourse, 10),
        start_date: startDate,
        end_date: endDate,
      });
      setReportData(reportRes);
      
      if (reportRes.length === 0) {
        toast('No attendance sessions found for the selected period.');
      } else {
        toast.success(`Report generated successfully! Found ${reportRes.length} session(s).`);
      }
    } catch (error) {
      toast.error('Failed to generate report.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = async () => {
    if (!selectedCourse) {
      toast.error('Please select a course to export.');
      return;
    }
    try {
      const blob = await attendanceService.exportAttendanceReport({
        course: parseInt(selectedCourse, 10),
        start_date: startDate,
        end_date: endDate,
        format: 'csv'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_report_${selectedCourse}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      toast.error('Failed to export report.');
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Reports & Analytics</h1>
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Course
            </label>
            <select
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(e.target.value)}
            >
              <option value="">Select a course</option>
              {courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.name}
                </option>
              ))}
            </select>
          </div>
          <Input
            label="Start Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <Input
            label="End Date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
          <div className="self-end">
            <Button onClick={handleGenerateReport} isLoading={loading}>
              <IoFilter className="w-5 h-5 mr-2" />
              Generate Report
            </Button>
          </div>
        </div>
      </Card>

      {reportData.length > 0 && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Attendance Report</h2>
            <Button onClick={handleExportReport} variant="outline">
                <IoDownload className="w-5 h-5 mr-2" />
                Export as CSV
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4">Date</th>
                  <th className="text-left py-3 px-4">Time</th>
                  <th className="text-left py-3 px-4">Course</th>
                  <th className="text-center py-3 px-4">Total Students</th>
                  <th className="text-center py-3 px-4">Present</th>
                  <th className="text-center py-3 px-4">Leave</th>
                  <th className="text-center py-3 px-4">Absent</th>
                  <th className="text-center py-3 px-4">Excused</th>
                  <th className="text-center py-3 px-4">Attendance %</th>
                </tr>
              </thead>
              <tbody>
                {reportData.map((record) => (
                  <tr key={record.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">{new Date(record.date).toLocaleDateString()}</td>
                    <td className="py-3 px-4">
                      {record.start_time}
                      {record.end_time && ` - ${record.end_time}`}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium">{record.course_code}</div>
                      <div className="text-sm text-gray-600">{record.course_name}</div>
                    </td>
                    <td className="py-3 px-4 text-center font-medium">{record.total_students}</td>
                    <td className="py-3 px-4 text-center text-green-600 font-medium">{record.present_count}</td>
                    <td className="py-3 px-4 text-center text-yellow-600 font-medium">{record.leave_count}</td>
                    <td className="py-3 px-4 text-center text-red-600 font-medium">{record.absent_count}</td>
                    <td className="py-3 px-4 text-center text-blue-600 font-medium">{record.excused_count}</td>
                    <td className="py-3 px-4 text-center font-bold text-lg">
                      {record.attendance_percentage.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {reportData.length === 0 && !loading && (
        <Card className="text-center py-12">
          <IoBarChart className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600">No report data to display.</p>
          <p className="text-sm text-gray-500">Select a course and generate a report to see the data.</p>
        </Card>
      )}
    </div>
  );
};

export default Reports;
