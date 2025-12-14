import { useState, useEffect } from 'react';
import { useParams, useHistory } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, Button, Input, LoadingSpinner } from '@components/ui';
import { courseService } from '@services/index';
import type { Course } from '@/types';
import toast from 'react-hot-toast';

const EditCourse = () => {
  const { id } = useParams<{ id: string }>();
  const history = useHistory();
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    semester: 'Fall',
    year: new Date().getFullYear(),
    start_date: '',
    end_date: '',
    is_active: true,
  });
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchCourseDetails();
  }, [id]);

  const fetchCourseDetails = async () => {
    if (!id) return;
    try {
      const course = await courseService.getCourse(parseInt(id, 10));
      setFormData({
        name: course.name,
        code: course.code,
        description: course.description || '',
        semester: course.semester,
        year: course.year,
        start_date: course.start_date || '',
        end_date: course.end_date || '',
        is_active: course.is_active,
      });
    } catch (error) {
      toast.error('Failed to load course details.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setIsSubmitting(true);
    try {
      await courseService.updateCourse(parseInt(id, 10), formData);
      toast.success('Course details updated successfully.');
      history.push(`/courses/${id}`);
    } catch (error) {
      toast.error('Failed to update course details.');
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h1 className="text-3xl font-bold mb-8">Edit Course</h1>
      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="Course Name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
          <Input
            label="Course Code"
            name="code"
            value={formData.code}
            onChange={handleChange}
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              name="description"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows={3}
              value={formData.description}
              onChange={handleChange}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Semester
              </label>
              <select
                name="semester"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                value={formData.semester}
                onChange={handleChange}
              >
                <option value="Fall">Fall</option>
                <option value="Spring">Spring</option>
                <option value="Summer">Summer</option>
              </select>
            </div>
            <Input
              label="Year"
              name="year"
              type="number"
              value={formData.year}
              onChange={handleChange}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Start Date"
              name="start_date"
              type="date"
              value={formData.start_date}
              onChange={handleChange}
            />
            <Input
              label="End Date"
              name="end_date"
              type="date"
              value={formData.end_date}
              onChange={handleChange}
            />
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              name="is_active"
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              checked={formData.is_active}
              onChange={handleChange}
            />
            <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
              Active course
            </label>
          </div>
          <div className="flex justify-end">
            <Button type="submit" loading={isSubmitting}>
              Update Course
            </Button>
          </div>
        </form>
      </Card>
    </motion.div>
  );
};

export default EditCourse;
