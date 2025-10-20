import React, { useState } from 'react';
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from '@mui/material';
import apiClient from '../../services/api';

const ChangePassword: React.FC = () => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    try {
      await apiClient.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword });
      setMessage('Password updated');
      setOldPassword('');
      setNewPassword('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update password');
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
      <Card sx={{ width: 420 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Change Password</Typography>
          {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <TextField fullWidth margin="normal" type="password" label="Old Password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
            <TextField fullWidth margin="normal" type="password" label="New Password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            <Button fullWidth variant="contained" type="submit" sx={{ mt: 2 }}>Update Password</Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ChangePassword;


