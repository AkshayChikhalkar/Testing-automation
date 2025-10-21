import React, { useState } from 'react';
import { Box, Card, CardContent, TextField, Button, Typography, Alert, Link } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import apiClient from '../../services/api';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const { t } = useTranslation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const form = new URLSearchParams();
      form.append('username', username);
      form.append('password', password);
      const res = await apiClient.post('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      const { access_token, refresh_token } = res.data;
      localStorage.setItem('auth_token', access_token);
      if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('auth.loginFailed'));
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
      <Card sx={{ width: 380 }}>
        <CardContent>
          <Typography variant="h5" mb={2}>{t('auth.login')}</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <TextField fullWidth margin="normal" label={t('auth.username')} value={username} onChange={(e) => setUsername(e.target.value)} />
            <TextField fullWidth margin="normal" type="password" label={t('auth.password')} value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button fullWidth variant="contained" type="submit" sx={{ mt: 2 }}>{t('auth.login')}</Button>
          </form>
          <Box display="flex" justifyContent="space-between" mt={2}>
            <Link component={RouterLink} to="/signup">{t('auth.signup')}</Link>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Login;


