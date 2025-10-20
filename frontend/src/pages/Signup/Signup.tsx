import React, { useState } from 'react';
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from '@mui/material';
import apiClient from '../../services/api';
import { useNavigate } from 'react-router-dom';

const Signup: React.FC = () => {
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
      setError(err?.response?.data?.detail || 'Sign up failed');
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
      <Card sx={{ width: 420 }}>
        <CardContent>
          <Typography variant="h5" mb={2}>Create Account</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <TextField fullWidth margin="normal" label="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <TextField fullWidth margin="normal" label="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <TextField fullWidth margin="normal" label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            <TextField fullWidth margin="normal" type="password" label="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button fullWidth variant="contained" type="submit" sx={{ mt: 2 }}>Sign Up</Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Signup;


