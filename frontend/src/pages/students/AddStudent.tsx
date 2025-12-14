import { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, Button, Input } from '@components/ui';
import { studentService } from '@services/index';
import toast from 'react-hot-toast';

const AddStudent = () => {
  const history = useHistory();
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    roll_number: '',
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
      toast.success('Student added successfully');
      history.push('/students');
    } catch (error) {
      toast.error('Failed to add student');
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
