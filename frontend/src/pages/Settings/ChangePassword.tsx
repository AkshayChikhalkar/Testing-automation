import React, { useState } from 'react';
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from '@mui/material';
import { useTranslation } from 'react-i18next';
import apiClient from '../../services/api';

const ChangePassword: React.FC = () => {
  const { t } = useTranslation();
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
      setMessage(t('settings.passwordChanged'));
      setOldPassword('');
      setNewPassword('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('settings.passwordUpdateFailed'));
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
      <Card sx={{ width: 420 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>{t('settings.changePassword')}</Typography>
          {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <TextField fullWidth margin="normal" type="password" label={t('settings.currentPassword')} value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
            <TextField fullWidth margin="normal" type="password" label={t('settings.newPassword')} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            <Button fullWidth variant="contained" type="submit" sx={{ mt: 2 }}>{t('settings.updatePassword')}</Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ChangePassword;


