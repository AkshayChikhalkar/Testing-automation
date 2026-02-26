import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Fab,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { formatGermanDate } from '../../utils/dateFormatting';

import { apiService, default as apiClient } from '../../services/api';

interface TestRun {
  id: number;
  name: string;
  model_id: number;
  model_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  start_time: string;
  end_time?: string;
  execution_time?: number;
  progress?: number;
  results?: any;
  parameters: any;
  error_message?: string | null;
}

const TestRuns: React.FC = () => {
  const { t } = useTranslation();
  const [openDialog, setOpenDialog] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    model_id: '',
    parameters: {},
  });
  const [inputFile, setInputFile] = useState<File | null>(null);

  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();

  // Fetch test runs - poll every 2s when any run is pending/running for live status updates
  const { data: testRuns = [], isLoading } = useQuery({
    queryKey: ['testRuns'],
    queryFn: () => apiService.testRuns.list().then(res => res.data),
    refetchInterval: (query) => {
      const data = query.state.data as TestRun[];
      const hasActive = data?.some((r: TestRun) => r.status === 'pending' || r.status === 'running');
      return hasActive ? 2000 : false;
    },
  });

  // Fetch models for dropdown
  const { data: models = [] } = useQuery({
    queryKey: ['models'],
    queryFn: () => apiService.models.list().then(res => res.data),
  });

  // Create test run mutation
  const createTestRunMutation = useMutation({
    mutationFn: async (data: any) => {
      if (inputFile) {
        const fd = new FormData();
        fd.append('name', data.name);
        fd.append('model_id', String(data.model_id));
        // user_id is set from the JWT on the backend
        fd.append('input_file', inputFile);
        if (data.parameters) {
          fd.append('configuration', JSON.stringify({ parameters: data.parameters }));
        }
        return apiClient.post('/test-runs/create-with-input', fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }
      return apiService.testRuns.create({
        name: data.name,
        model_id: data.model_id,
        configuration: data.parameters != null ? { parameters: data.parameters } : undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testRuns'] });
      setOpenDialog(false);
      resetForm();
      setInputFile(null);
    },
  });

  // Start/Stop test run mutations
  const startTestRunMutation = useMutation({
    mutationFn: apiService.testRuns.execute,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testRuns'] });
    },
  });

  const stopTestRunMutation = useMutation({
    mutationFn: apiService.testRuns.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testRuns'] });
    },
  });

  const deleteTestRunMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/test-runs/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testRuns'] });
    },
  });

  const resetForm = () => {
    setFormData({ name: '', model_id: '', parameters: {} });
  };

  const handleOpenDialog = () => {
    const modelId = searchParams.get('model');
    if (modelId) {
      setFormData({ name: '', model_id: modelId, parameters: {} });
    } else {
      resetForm();
    }
    setOpenDialog(true);
  };

  const handleSubmit = () => {
    createTestRunMutation.mutate(formData);
  };

  const handleStart = (id: number) => {
    startTestRunMutation.mutate(id);
  };

  const handleStop = (id: number) => {
    stopTestRunMutation.mutate(id);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this test run?')) {
      deleteTestRunMutation.mutate(id);
    }
  };

  const handleDownloadResults = async (id: number) => {
    try {
      const response = await apiService.testRuns.downloadResults(id);
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
      // You could add a snackbar notification here
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'warning';
      case 'pending': return 'info';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  const getShortErrorMessage = (msg: string) => {
    const firstLine = msg.split(/\r?\n/)[0]?.trim() || msg;
    return firstLine.length > 80 ? `${firstLine.slice(0, 77)}…` : firstLine;
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
        <Typography>Loading test runs...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('testRuns.title')}</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenDialog}
        >
          {t('testRuns.createTestRun')}
        </Button>
      </Box>

      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('testRuns.name')}</TableCell>
                <TableCell>{t('testRuns.model')}</TableCell>
                <TableCell>{t('testRuns.status')}</TableCell>
                <TableCell>{t('testRuns.progress')}</TableCell>
                <TableCell>{t('testRuns.startTime')}</TableCell>
                <TableCell>{t('testRuns.duration')}</TableCell>
                <TableCell>{t('testRuns.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {testRuns.map((testRun: TestRun) => (
                <React.Fragment key={testRun.id}>
                  <TableRow>
                    <TableCell>
                      <Typography variant="subtitle2">{testRun.name}</Typography>
                    </TableCell>
                    <TableCell>{testRun.model_name}</TableCell>
                    <TableCell>
                      <Box>
                        <Chip
                          label={testRun.status}
                          color={getStatusColor(testRun.status) as any}
                          size="small"
                        />
                        {testRun.error_message && (
                          <Tooltip title={testRun.error_message}>
                            <Typography
                              variant="caption"
                              display="block"
                              color="error.main"
                              sx={{ mt: 0.5, lineHeight: 1.2 }}
                            >
                              {getShortErrorMessage(testRun.error_message)}
                            </Typography>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {testRun.status === 'running' && testRun.progress !== undefined ? (
                        <Box sx={{ width: 100 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={testRun.progress} 
                            sx={{ mb: 1 }}
                          />
                          <Typography variant="caption">
                            {testRun.progress}%
                          </Typography>
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          {testRun.status === 'completed' ? '100%' : 'N/A'}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {formatGermanDate(testRun.start_time)}
                    </TableCell>
                    <TableCell>
                      {formatDuration(testRun.execution_time)}
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={1}>
                        {testRun.status === 'pending' && (
                          <Tooltip title={t('testRuns.startTest')}>
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleStart(testRun.id)}
                            >
                              <PlayIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        {testRun.status === 'running' && (
                          <Tooltip title={t('testRuns.stopTest')}>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleStop(testRun.id)}
                            >
                              <StopIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title={t('testRuns.viewDetails')}>
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/test-runs/${testRun.id}`)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        {testRun.status === 'completed' && (
                          <Tooltip title={t('testRuns.downloadResults')}>
                            <IconButton
                              size="small"
                              onClick={() => handleDownloadResults(testRun.id)}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title={t('common.delete')}>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete(testRun.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {testRuns.length === 0 && (
          <Card sx={{ mt: 3 }}>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No test runs found
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={3}>
                Create your first test run to get started
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenDialog}
              >
                New Test Run
              </Button>
            </CardContent>
          </Card>
        )}
      </Box>

      {/* New Test Run Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('testRuns.createTestRun')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('testRuns.testRunName')}
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" display="block" gutterBottom>Input data file</Typography>
            <input
              type="file"
              accept=".json,.csv,.mat,.xlsx"
              onChange={(e) => setInputFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)}
            />
          </Box>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Model</InputLabel>
            <Select
              value={formData.model_id}
              label={t('testRuns.model')}
              onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
            >
              {models.map((model: any) => (
                <MenuItem key={model.id} value={model.id}>
                  {model.name} (v{model.version})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            label="Parameters (JSON)"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            placeholder='{"param1": "value1", "param2": "value2"}'
            value={JSON.stringify(formData.parameters, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                setFormData({ ...formData, parameters: parsed });
              } catch (error) {
                // Invalid JSON, keep the text for user to fix
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.name || !formData.model_id || createTestRunMutation.isPending}
          >
            Create Test Run
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button */}
      <Tooltip title={t('common.refresh')}>
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => queryClient.invalidateQueries({ queryKey: ['testRuns'] })}
        >
          <RefreshIcon />
        </Fab>
      </Tooltip>
    </Box>
  );
};

export default TestRuns;
