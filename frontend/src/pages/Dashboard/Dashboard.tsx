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
  Avatar,
  Fade,
  Skeleton,
} from '@mui/material';
import {
  ModelTraining,
  PlayArrow,
  Assessment,
  CheckCircle,
  Error,
  TrendingUp,
  Schedule,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { formatGermanDate } from '../../utils/dateFormatting';

import { apiService } from '../../services/api';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Fetch dashboard data
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: apiService.getDashboardData,
  });

  const stats = [
    {
      title: t('dashboard.totalModels'),
      value: dashboardData?.totalModels || 0,
      icon: <ModelTraining />,
      color: '#1976d2',
      bgColor: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
      trend: '+12%',
    },
    {
      title: t('dashboard.testRunsToday'),
      value: dashboardData?.testRunsToday || 0,
      icon: <PlayArrow />,
      color: '#2e7d32',
      bgColor: 'linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%)',
      trend: '+8%',
    },
    {
      title: t('dashboard.successfulTests'),
      value: dashboardData?.successfulTests || 0,
      icon: <CheckCircle />,
      color: '#388e3c',
      bgColor: 'linear-gradient(135deg, #388e3c 0%, #66bb6a 100%)',
      trend: '+15%',
    },
    {
      title: t('dashboard.failedTests'),
      value: dashboardData?.failedTests || 0,
      icon: <Error />,
      color: '#d32f2f',
      bgColor: 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)',
      trend: '-5%',
    },
  ];

  const recentTestRuns = dashboardData?.recentTestRuns || [];

  if (isLoading) {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Typography variant="h4" gutterBottom>
          {t('common.dashboard')}
        </Typography>
        
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {[1, 2, 3, 4].map((index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box sx={{ flexGrow: 1 }}>
                      <Skeleton variant="text" width="60%" height={20} />
                      <Skeleton variant="text" width="40%" height={40} />
                    </Box>
                    <Skeleton variant="circular" width={48} height={48} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3, height: '400px' }}>
              <Skeleton variant="text" width="30%" height={30} />
              <Box sx={{ mt: 2 }}>
                {[1, 2, 3].map((index) => (
                  <Skeleton key={index} variant="rectangular" height={80} sx={{ mb: 2 }} />
                ))}
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, height: '400px' }}>
              <Skeleton variant="text" width="40%" height={30} />
              <Box sx={{ mt: 2 }}>
                {[1, 2, 3].map((index) => (
                  <Skeleton key={index} variant="rectangular" height={48} sx={{ mb: 2 }} />
                ))}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" gutterBottom>
        {t('common.dashboard')}
      </Typography>
      
      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Fade in timeout={300 + index * 100}>
              <Card 
                sx={{ 
                  height: '100%',
                  background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                  border: '1px solid rgba(0,0,0,0.05)',
                  borderRadius: '16px',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
                  }
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{ 
                          fontWeight: 500,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                          fontSize: '0.75rem',
                          mb: 1
                        }}
                      >
                        {stat.title}
                      </Typography>
                      <Typography 
                        variant="h3" 
                        component="div"
                        sx={{ 
                          fontWeight: 700,
                          background: stat.bgColor,
                          backgroundClip: 'text',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                          mb: 1
                        }}
                      >
                        {stat.value}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <TrendingUp sx={{ fontSize: 16, color: stat.color }} />
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: stat.color,
                            fontWeight: 600,
                            fontSize: '0.875rem'
                          }}
                        >
                          {stat.trend}
                        </Typography>
                      </Box>
                    </Box>
                    <Avatar
                      sx={{
                        width: 56,
                        height: 56,
                        background: stat.bgColor,
                        boxShadow: `0 4px 12px ${stat.color}40`,
                        '& .MuiSvgIcon-root': {
                          fontSize: '1.75rem',
                          color: 'white'
                        }
                      }}
                    >
                      {stat.icon}
                    </Avatar>
                  </Box>
                </CardContent>
              </Card>
            </Fade>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3} sx={{ flexGrow: 1 }}>
        {/* Recent Test Runs */}
        <Grid item xs={12} md={8}>
          <Paper 
            sx={{ 
              p: 3, 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              border: '1px solid rgba(0,0,0,0.05)',
              borderRadius: '16px',
            }}
          >
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 600,
                  color: 'text.primary'
                }}
              >
                {t('dashboard.recentTestRuns')}
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/test-runs')}
                sx={{ borderRadius: '20px' }}
              >
                {t('dashboard.viewAll')}
              </Button>
            </Box>
            <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
              {recentTestRuns.length > 0 ? (
                <Box>
                  {recentTestRuns.map((testRun: any, index: number) => (
                    <Fade in timeout={400 + index * 100} key={testRun.id}>
                      <Card 
                        sx={{ 
                          mb: 2,
                          background: 'white',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                          border: '1px solid rgba(0,0,0,0.04)',
                          borderRadius: '12px',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
                            transform: 'translateY(-1px)',
                          }
                        }}
                      >
                        <CardContent sx={{ p: 2.5 }}>
                          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                            <Box sx={{ flexGrow: 1 }}>
                              <Typography 
                                variant="h6" 
                                sx={{ 
                                  fontWeight: 600,
                                  mb: 0.5,
                                  color: 'text.primary'
                                }}
                              >
                                {testRun.name}
                              </Typography>
                              <Typography 
                                color="text.secondary" 
                                sx={{ fontSize: '0.875rem', mb: 0.5 }}
                              >
                                {t('dashboard.model')}: {testRun.model_name}
                              </Typography>
                              <Box display="flex" alignItems="center" gap={1}>
                                <Schedule sx={{ fontSize: 16, color: 'text.secondary' }} />
                                <Typography 
                                  color="text.secondary" 
                                  sx={{ fontSize: '0.875rem' }}
                                >
                                  {formatGermanDate(testRun.start_time)}
                                </Typography>
                              </Box>
                            </Box>
                            <Box display="flex" alignItems="center" gap={1}>
                              <Chip
                                label={t(`common.${testRun.status.toLowerCase()}`)}
                                color={
                                  testRun.status === 'completed'
                                    ? 'success'
                                    : testRun.status === 'failed'
                                    ? 'error'
                                    : 'default'
                                }
                                size="small"
                                sx={{ 
                                  fontWeight: 500,
                                  borderRadius: '12px'
                                }}
                              />
                              {testRun.execution_time && (
                                <Typography 
                                  variant="body2" 
                                  color="text.secondary"
                                  sx={{ 
                                    fontWeight: 500,
                                    fontSize: '0.75rem'
                                  }}
                                >
                                  {testRun.execution_time}s
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </CardContent>
                        <CardActions sx={{ px: 2.5, pb: 2 }}>
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => navigate(`/test-runs/${testRun.id}`)}
                            sx={{ 
                              borderRadius: '8px',
                              textTransform: 'none',
                              fontWeight: 500
                            }}
                          >
                            {t('common.viewDetails')}
                          </Button>
                        </CardActions>
                      </Card>
                    </Fade>
                  ))}
                </Box>
              ) : (
                <Box 
                  display="flex" 
                  flexDirection="column" 
                  alignItems="center" 
                  justifyContent="center" 
                  py={6}
                >
                  <Assessment sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography 
                    color="text.secondary" 
                    variant="h6"
                    sx={{ fontWeight: 500 }}
                  >
                    {t('dashboard.noRecentTestRuns')}
                  </Typography>
                  <Typography 
                    color="text.secondary" 
                    variant="body2"
                    sx={{ mt: 1 }}
                  >
                    {t('dashboard.startFirstTestRun')}
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Paper 
            sx={{ 
              p: 3, 
              height: '100%',
              background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              border: '1px solid rgba(0,0,0,0.05)',
              borderRadius: '16px',
            }}
          >
            <Typography 
              variant="h6" 
              gutterBottom
              sx={{ 
                fontWeight: 600,
                color: 'text.primary',
                mb: 3
              }}
            >
              {t('dashboard.quickActions')}
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Button
                variant="contained"
                startIcon={<ModelTraining />}
                onClick={() => navigate('/models')}
                fullWidth
                size="large"
                sx={{
                  borderRadius: '12px',
                  py: 1.5,
                  background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
                  boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                  textTransform: 'none',
                  fontWeight: 600,
                  '&:hover': {
                    background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
                    boxShadow: '0 6px 16px rgba(25, 118, 210, 0.4)',
                    transform: 'translateY(-1px)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                {t('dashboard.manageModels')}
              </Button>
              <Button
                variant="outlined"
                startIcon={<PlayArrow />}
                onClick={() => navigate('/test-runs')}
                fullWidth
                size="large"
                sx={{
                  borderRadius: '12px',
                  py: 1.5,
                  borderColor: '#2e7d32',
                  color: '#2e7d32',
                  textTransform: 'none',
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: '#1b5e20',
                    backgroundColor: 'rgba(46, 125, 50, 0.04)',
                    transform: 'translateY(-1px)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                {t('dashboard.runTests')}
              </Button>
              <Button
                variant="outlined"
                startIcon={<Assessment />}
                onClick={() => navigate('/reports')}
                fullWidth
                size="large"
                sx={{
                  borderRadius: '12px',
                  py: 1.5,
                  borderColor: '#7b1fa2',
                  color: '#7b1fa2',
                  textTransform: 'none',
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: '#4a148c',
                    backgroundColor: 'rgba(123, 31, 162, 0.04)',
                    transform: 'translateY(-1px)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                {t('dashboard.viewReports')}
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
