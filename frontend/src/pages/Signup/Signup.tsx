import React, { useState } from 'react';
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from '@mui/material';
import { useTranslation } from 'react-i18next';
import apiClient from '../../services/api';
import { useNavigate } from 'react-router-dom';

const Signup: React.FC = () => {
  const { t } = useTranslation();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await apiClient.post('/auth/signup', {
        username,
        email,
        password,
        full_name: fullName,
      });
      const { access_token, refresh_token } = res.data;
      localStorage.setItem('auth_token', access_token);
      if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('auth.signupFailed'));
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
      <Card sx={{ width: 420 }}>
        <CardContent>
          <Typography variant="h5" mb={2}>{t('auth.createAccount')}</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <TextField fullWidth margin="normal" label={t('auth.username')} value={username} onChange={(e) => setUsername(e.target.value)} />
            <TextField fullWidth margin="normal" label={t('auth.email')} value={email} onChange={(e) => setEmail(e.target.value)} />
            <TextField fullWidth margin="normal" label={t('auth.fullName')} value={fullName} onChange={(e) => setFullName(e.target.value)} />
            <TextField fullWidth margin="normal" type="password" label={t('auth.password')} value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button fullWidth variant="contained" type="submit" sx={{ mt: 2 }}>{t('auth.signup')}</Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Signup;


