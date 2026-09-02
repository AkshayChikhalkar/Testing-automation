import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Grid,
  Paper,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Download as DownloadIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Assessment as AssessmentIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatGermanDate } from '../../utils/dateFormatting';
import { apiService, default as apiClient } from '../../services/api';


const TestRunDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [expandedLogs, setExpandedLogs] = useState(false);

  // Fetch test run details - poll when pending/running for live status updates
  const { data: testRun, isLoading, error } = useQuery({
    queryKey: ['testRun', id],
    queryFn: async () => {
      const response = await apiService.testRuns.get(parseInt(id!));
      return response.data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data as { status?: string };
      return data?.status === 'pending' || data?.status === 'running' ? 2000 : false;
    },
  });

  // Start/Stop test run mutations
  const startTestRunMutation = useMutation({
    mutationFn: () => apiService.testRuns.execute(parseInt(id!)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testRun', id] });
      queryClient.invalidateQueries({ queryKey: ['testRuns'] });
    },
  });

  const stopTestRunMutation = useMutation({
    mutationFn: () => apiService.testRuns.cancel(parseInt(id!)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testRun', id] });
      queryClient.invalidateQueries({ queryKey: ['testRuns'] });
    },
  });

  const handleStart = () => {
    startTestRunMutation.mutate();
  };

  const handleStop = () => {
    stopTestRunMutation.mutate();
  };

  const handleDownloadResults = async () => {
    try {
      const response = await apiService.testRuns.downloadResults(parseInt(id!));
      const blob = new Blob([response.data], { type: 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `test-run-${id}-results.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading results:', error);
      // Fallback to JSON download if API fails
      if (testRun?.results) {
        const dataStr = JSON.stringify(testRun.results, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `test-run-${id}-results.json`;
        link.click();
        URL.revokeObjectURL(url);
      }
    }
  };

  const handleDownloadLogs = async () => {
    try {
      const response = await apiService.testRuns.downloadLogs(parseInt(id!));
      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `test-run-${id}-logs.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading logs:', error);
      // Fallback to local logs if API fails
      if (testRun?.logs) {
        const logsStr = testRun.logs.join('\n');
        const dataBlob = new Blob([logsStr], { type: 'text/plain' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `test-run-${id}-logs.txt`;
        link.click();
        URL.revokeObjectURL(url);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'completed_warning': return 'warning';
      case 'failed': return 'error';
      case 'running': return 'warning';
      case 'pending': return 'info';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />;
      case 'completed_warning': return <WarningIcon />;
      case 'failed': return <ErrorIcon />;
      case 'running': return <PlayIcon />;
      case 'pending': return <ScheduleIcon />;
      case 'cancelled': return <StopIcon />;
      default: return <InfoIcon />;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading test run details...</Typography>
      </Box>
    );
  }

  if (error || !testRun) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Alert severity="error">
          Failed to load test run details
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/test-runs')}
            variant="outlined"
          >
            Back to Test Runs
          </Button>
          <Typography variant="h4">{testRun.name}</Typography>
        </Box>
        <Box display="flex" gap={2}>
          {testRun.status === 'pending' && (
            <Button
              variant="contained"
              startIcon={<PlayIcon />}
              onClick={handleStart}
              disabled={startTestRunMutation.isPending}
            >
              Start Test
            </Button>
          )}
          {testRun.status === 'running' && (
            <Button
              variant="contained"
              color="error"
              startIcon={<StopIcon />}
              onClick={handleStop}
              disabled={stopTestRunMutation.isPending}
            >
              Stop Test
            </Button>
          )}
          {(testRun.status === 'completed' || testRun.status === 'completed_warning') && (
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadResults}
            >
              Download Results
            </Button>
          )}
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ flexGrow: 1, overflow: 'auto' }}>
        {/* Status and Progress */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Run Status
              </Typography>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Chip
                  icon={getStatusIcon(testRun.status)}
                  label={testRun.status.replace(/_/g, ' ').toUpperCase()}
                  color={getStatusColor(testRun.status) as any}
                  size="medium"
                />
                {testRun.progress !== undefined && testRun.status === 'running' && (
                  <Typography variant="body2" color="text.secondary">
                    {testRun.progress}% Complete
                  </Typography>
                )}
              </Box>
              
              {testRun.status === 'running' && testRun.progress !== undefined && (
                <LinearProgress 
                  variant="determinate" 
                  value={testRun.progress} 
                  sx={{ mb: 2 }}
                />
              )}

              {testRun.error_message && (
                <Alert severity={testRun.status === 'completed_warning' ? 'warning' : 'error'} sx={{ mt: 2 }}>
                  {testRun.error_message}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Test Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <InfoIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Simulation ID" 
                    secondary={testRun.simulation_id ?? "Not available yet"}
                    secondaryTypographyProps={{ 
                      component: 'span', 
                      sx: { fontFamily: testRun.simulation_id ? 'monospace' : 'inherit' }
                    }}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <InfoIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Test Run ID" 
                    secondary={testRun.id}
                    secondaryTypographyProps={{ component: 'span' }}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <AssessmentIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Model" 
                    secondary={testRun.model_name}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <ScheduleIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Start Time" 
                    secondary={formatGermanDate(testRun.start_time)}
                  />
                </ListItem>
                {testRun.end_time && (
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircleIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary="End Time" 
                      secondary={formatGermanDate(testRun.end_time)}
                    />
                  </ListItem>
                )}
                <ListItem>
                  <ListItemIcon>
                    <ScheduleIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Duration" 
                    secondary={formatDuration(testRun.execution_time)}
                  />
                </ListItem>
              </List>
              <Alert severity="info" sx={{ mt: 2 }} icon={<InfoIcon />}>
                <Typography variant="subtitle2" gutterBottom>
                  IDs and how data is filtered
                </Typography>
                {testRun.simulation_id && (
                  <Typography variant="body2" color="text.secondary" component="span">
                    <strong>Simulation ID ({testRun.simulation_id})</strong> — From InfluxDB. Use it in Grafana (<code>simulation_id</code> filter) and when sharing results. Mapping stored in Postgres.
                  </Typography>
                )}
                <Typography variant="body2" color="text.secondary" sx={{ display: 'block', mt: 1 }} component="span">
                  <strong>Test Run ID ({testRun.id})</strong> — Internal ID in this app and database (<code>test_runs.id</code>, <code>test_run_id</code> in relations).
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        {/* Parameters */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Parameters
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {(() => {
                    const rawConfig = testRun.configuration;
                    const params = rawConfig?.parameters ?? testRun.parameters;

                    // 1) Explicit parameters object with keys
                    if (params != null && typeof params === 'object' && Object.keys(params).length > 0) {
                      return JSON.stringify(params, null, 2);
                    }

                    // 2) Configuration object with more than just an empty parameters object
                    if (rawConfig != null && typeof rawConfig === 'object') {
                      const { parameters, ...rest } = rawConfig as any;
                      const hasNonEmptyParams =
                        parameters && typeof parameters === 'object' && Object.keys(parameters).length > 0;
                      const hasOtherConfigKeys = Object.keys(rest).length > 0;

                      if (hasNonEmptyParams) {
                        return JSON.stringify(parameters, null, 2);
                      }
                      if (hasOtherConfigKeys) {
                        return JSON.stringify(rest, null, 2);
                      }
                    }

                    // 3) Fallback to input_data to at least show which file/format was used
                    if (testRun.input_data && typeof testRun.input_data === 'object' && Object.keys(testRun.input_data).length > 0) {
                      return JSON.stringify(testRun.input_data, null, 2);
                    }

                    // 4) Nothing meaningful available
                    return 'No parameters specified';
                  })()}
                </pre>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Results */}
        {testRun.results && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    Test Results
                  </Typography>
                  <Button
                    startIcon={<DownloadIcon />}
                    onClick={handleDownloadResults}
                    variant="outlined"
                    size="small"
                  >
                    Download
                  </Button>
                </Box>
                <Paper sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 400, overflow: 'auto' }}>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                    {JSON.stringify(testRun.results, null, 2)}
                  </pre>
                </Paper>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Logs */}
        {testRun.logs && testRun.logs.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    Execution Logs
                  </Typography>
                  <Button
                    startIcon={<DownloadIcon />}
                    onClick={handleDownloadLogs}
                    variant="outlined"
                    size="small"
                  >
                    Download Logs
                  </Button>
                </Box>
                <Accordion 
                  expanded={expandedLogs} 
                  onChange={() => setExpandedLogs(!expandedLogs)}
                >
                  <AccordionSummary>
                    <Typography variant="subtitle2">
                      {expandedLogs ? 'Hide Logs' : 'Show Logs'} ({testRun.logs.length} entries)
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Paper sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 300, overflow: 'auto' }}>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {testRun.logs.join('\n')}
                      </pre>
                    </Paper>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Output Files */}
        {testRun.output_files && testRun.output_files.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Output Files
                </Typography>
                <List>
                  {testRun.output_files.map((file: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemText primary={file} />
                      <Button
                        startIcon={<DownloadIcon />}
                        onClick={async () => {
                          try {
                            const response = await apiClient.get(`/test-runs/${id}/files/${encodeURIComponent(file)}`, {
                              responseType: 'blob'
                            });
                            const blob = new Blob([response.data]);
                            const url = window.URL.createObjectURL(blob);
                            const link = document.createElement('a');
                            link.href = url;
                            link.download = file;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                            window.URL.revokeObjectURL(url);
                          } catch (error) {
                            console.error(`Error downloading ${file}:`, error);
                          }
                        }}
                        size="small"
                      >
                        Download
                      </Button>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default TestRunDetail;
