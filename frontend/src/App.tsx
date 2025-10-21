import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Import i18n configuration
import './i18n';

import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Models from './pages/Models/Models';
import TestRuns from './pages/TestRuns/TestRuns';
import TestRunDetail from './pages/TestRuns/TestRunDetail';
import Reports from './pages/Reports/Reports';
import Settings from './pages/Settings/Settings';
import Login from './pages/Login/Login';
import ChangePassword from './pages/Settings/ChangePassword';
import Signup from './pages/Signup/Signup';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Layout>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/models" element={<Models />} />
              <Route path="/test-runs" element={<TestRuns />} />
              <Route path="/test-runs/:id" element={<TestRunDetail />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/change-password" element={<ChangePassword />} />
            </Routes>
          </Layout>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
