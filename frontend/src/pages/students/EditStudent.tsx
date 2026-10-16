import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, Button, Input, LoadingSpinner } from '@components/ui';
import { studentService } from '@services/index';
import toast from 'react-hot-toast';

const EditStudent = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    roll_number: '',
    department: '',
    semester: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudentDetails();
  }, [id]);

  const fetchStudentDetails = async () => {
    if (!id) return;
    try {
      const student = await studentService.getStudent(parseInt(id, 10));
      setFormData({
        first_name: student.user.first_name,
        last_name: student.user.last_name,
        email: student.user.email,
        roll_number: student.roll_number,
        department: student.department || '',
        semester: student.semester ? String(student.semester) : '',
      });
    } catch (error) {
      toast.error('Failed to load student details.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setLoading(true);
    try {
      await studentService.updateStudent(parseInt(id, 10), {
        user: {
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
        },
        roll_number: formData.roll_number,
        department: formData.department,
        semester: formData.semester ? parseInt(formData.semester, 10) : undefined,
      });
      toast.success('Student details updated successfully.');
      navigate(`/students/${id}`);
    } catch (error) {
      toast.error('Failed to update student details.');
    } finally {
      setLoading(false);
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h1 className="text-3xl font-bold mb-8">Edit Student</h1>
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
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
          <Input
            label="Roll Number"
            name="roll_number"
            value={formData.roll_number}
            onChange={handleChange}
            required
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label="Department"
              name="department"
              value={formData.department}
              onChange={handleChange}
            />
            <Input
              label="Semester"
              name="semester"
              type="number"
              value={formData.semester}
              onChange={handleChange}
            />
          </div>
          <div className="flex justify-end">
            <Button type="submit" isLoading={loading}>
              Update Student
            </Button>
          </div>
        </form>
      </Card>
    </motion.div>
  );
};

export default EditStudent;
