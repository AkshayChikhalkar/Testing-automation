import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
} from '@mui/material';
import {
  ModelTraining,
  PlayArrow,
  Assessment,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { apiService } from '../../services/api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  // Fetch dashboard data
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: apiService.getDashboardData,
  });

  const stats = [
    {
      title: 'Total Models',
      value: dashboardData?.totalModels || 0,
      icon: <ModelTraining />,
      color: '#1976d2',
    },
    {
      title: 'Test Runs Today',
      value: dashboardData?.testRunsToday || 0,
      icon: <PlayArrow />,
      color: '#2e7d32',
    },
    {
      title: 'Successful Tests',
      value: dashboardData?.successfulTests || 0,
      icon: <CheckCircle />,
      color: '#388e3c',
    },
    {
      title: 'Failed Tests',
      value: dashboardData?.failedTests || 0,
      icon: <Error />,
      color: '#d32f2f',
    },
  ];

  const recentTestRuns = dashboardData?.recentTestRuns || [];

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading dashboard...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {stat.value}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      backgroundColor: stat.color,
                      borderRadius: '50%',
                      p: 1,
                      color: 'white',
                    }}
                  >
                    {stat.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3} sx={{ flexGrow: 1 }}>
        {/* Recent Test Runs */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Recent Test Runs
            </Typography>
            <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
              {recentTestRuns.length > 0 ? (
                <Box>
                  {recentTestRuns.map((testRun: any) => (
                    <Card key={testRun.id} sx={{ mb: 2 }}>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Box>
                            <Typography variant="h6">{testRun.name}</Typography>
                            <Typography color="textSecondary">
                              Model: {testRun.model_name}
                            </Typography>
                            <Typography color="textSecondary">
                              Started: {new Date(testRun.start_time).toLocaleString()}
                            </Typography>
                          </Box>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip
                              label={testRun.status}
                              color={
                                testRun.status === 'completed'
                                  ? 'success'
                                  : testRun.status === 'failed'
                                  ? 'error'
                                  : 'default'
                              }
                              size="small"
                            />
                            {testRun.execution_time && (
                              <Typography variant="body2" color="textSecondary">
                                {testRun.execution_time}s
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      </CardContent>
                      <CardActions>
                        <Button
                          size="small"
                          onClick={() => navigate(`/test-runs/${testRun.id}`)}
                        >
                          View Details
                        </Button>
                      </CardActions>
                    </Card>
                  ))}
                </Box>
              ) : (
                <Typography color="textSecondary">
                  No recent test runs found.
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Button
                variant="contained"
                startIcon={<ModelTraining />}
                onClick={() => navigate('/models')}
                fullWidth
                size="large"
              >
                Manage Models
              </Button>
              <Button
                variant="outlined"
                startIcon={<PlayArrow />}
                onClick={() => navigate('/test-runs')}
                fullWidth
                size="large"
              >
                Run Tests
              </Button>
              <Button
                variant="outlined"
                startIcon={<Assessment />}
                onClick={() => navigate('/reports')}
                fullWidth
                size="large"
              >
                View Reports
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
