import { useState } from 'react';
import { Card, Input, Button } from '@components/ui';
import toast from 'react-hot-toast';
import { authService } from '@services/index';

const Settings = () => {
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPasswordData({ ...passwordData, [e.target.name]: e.target.value });
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.new_password_confirm) {
      toast.error('New passwords do not match.');
      return;
    }
    setIsSubmitting(true);
    try {
      await authService.changePassword(passwordData);
      toast.success('Password changed successfully.');
      setPasswordData({
        old_password: '',
        new_password: '',
        new_password_confirm: '',
      });
    } catch (error) {
      toast.error('Failed to change password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Settings</h1>
      <Card>
        <h2 className="text-2xl font-bold mb-6">Change Password</h2>
        <form onSubmit={handlePasswordSubmit} className="space-y-4 max-w-md">
          <Input
            label="Old Password"
            name="old_password"
            type="password"
            value={passwordData.old_password}
            onChange={handlePasswordChange}
            required
          />
          <Input
            label="New Password"
            name="new_password"
            type="password"
            value={passwordData.new_password}
            onChange={handlePasswordChange}
            required
          />
          <Input
            label="Confirm New Password"
            name="new_password_confirm"
            type="password"
            value={passwordData.new_password_confirm}
            onChange={handlePasswordChange}
            required
          />
          <Button type="submit" isLoading={isSubmitting}>
            Change Password
          </Button>
        </form>
      </Card>
    </div>
  );
};

export default Settings;
