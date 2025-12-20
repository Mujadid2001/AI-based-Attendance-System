import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, Button, Input } from '@components/ui';
import { studentService } from '@services/index';
import toast from 'react-hot-toast';

const AddStudent = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    roll_number: '',
    department: '',
    semester: '',
    password: '',
    password_confirm: '',
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.password_confirm) {
      toast.error('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      await studentService.createStudent(formData);
      toast.success('Student added successfully! A verification email has been sent to the student.');
      navigate('/students');
    } catch (error: any) {
      console.error('Student registration error:', error);
      if (error.response?.data) {
        // Display specific validation errors
        const errors = error.response.data;
        if (typeof errors === 'object') {
          Object.keys(errors).forEach(key => {
            const messages = Array.isArray(errors[key]) ? errors[key] : [errors[key]];
            messages.forEach((msg: string) => toast.error(`${key}: ${msg}`));
          });
        } else {
          toast.error('Failed to add student');
        }
      } else {
        toast.error('Failed to add student');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Add New Student</h1>
          <p className="text-gray-600 mt-1">Enter the details for the new student.</p>
        </div>
      </div>
      
      {/* Information Alert */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 text-blue-600 text-xl">ℹ️</div>
          <div>
            <h3 className="font-semibold text-blue-900 mb-1">Email Verification Required</h3>
            <p className="text-sm text-blue-700">
              After creating the account, a verification email will be sent to the student. 
              The student must verify their email before they can log in. They should also change 
              their password after the first login for security.
            </p>
          </div>
        </div>
      </div>
      
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
            label="Phone"
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={handleChange}
            placeholder="e.g., +92-300-1234567"
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
              placeholder="e.g., Computer Science"
            />
            <Input
              label="Semester"
              name="semester"
              type="number"
              value={formData.semester}
              onChange={handleChange}
              placeholder="e.g., 1, 2, 3..."
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label="Password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
            <Input
              label="Confirm Password"
              name="password_confirm"
              type="password"
              value={formData.password_confirm}
              onChange={handleChange}
              required
            />
          </div>
          <div className="flex justify-end">
            <Button type="submit" loading={loading}>
              Add Student
            </Button>
          </div>
        </form>
      </Card>
    </motion.div>
  );
};

export default AddStudent;
