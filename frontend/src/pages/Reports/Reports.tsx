import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

import { apiService } from '../../services/api';


const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Reports: React.FC = () => {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    end: new Date(),
  });
  const [selectedModel, setSelectedModel] = useState('all');

  // Fetch reports data
  const { data: reportData, isLoading } = useQuery({
    queryKey: ['reports', dateRange, selectedModel],
    queryFn: async () => {
      try {
        const params = {
          start_date: dateRange.start.toISOString().split('T')[0],
          end_date: dateRange.end.toISOString().split('T')[0],
          model_id: selectedModel !== 'all' ? selectedModel : undefined,
        };

        const [analyticsResponse, trendsResponse, performanceResponse] = await Promise.all([
          apiService.reports.getAnalytics(params),
          apiService.reports.getTestTrends(params),
          apiService.reports.getModelPerformance(params),
        ]);

        return {
          ...analyticsResponse.data,
          testTrends: trendsResponse.data,
          modelPerformance: performanceResponse.data,
        };
      } catch (error) {
        console.error('Error fetching reports data:', error);
        // Fallback to mock data if API fails
        return {
          totalTests: 0,
          successfulTests: 0,
          failedTests: 0,
          averageExecutionTime: 0,
          testTrends: [],
          modelPerformance: [],
          statusDistribution: [],
        };
      }
    },
  });

  // Fetch models for filter
  const { data: models = [] } = useQuery({
    queryKey: ['models'],
    queryFn: () => apiService.models.list().then(res => res.data),
  });

  const handleExportReport = async (format: 'pdf' | 'excel') => {
    try {
      const params = {
        start_date: dateRange.start.toISOString().split('T')[0],
        end_date: dateRange.end.toISOString().split('T')[0],
        model_id: selectedModel !== 'all' ? selectedModel : undefined,
      };

      const response = format === 'pdf' 
        ? await apiService.reports.exportPDF(params)
        : await apiService.reports.exportExcel(params);

      const blob = new Blob([response.data], { 
        type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `reports-${dateRange.start.toISOString().split('T')[0]}-to-${dateRange.end.toISOString().split('T')[0]}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(`Error exporting ${format} report:`, error);
      // You could add a snackbar notification here
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading reports...</Typography>
      </Box>
    );
  }

  const data = reportData || {
    totalTests: 0,
    successfulTests: 0,
    failedTests: 0,
    averageExecutionTime: 0,
    testTrends: [],
    modelPerformance: [],
    statusDistribution: [],
  };

  const successRate = data.totalTests > 0 ? (data.successfulTests / data.totalTests) * 100 : 0;

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">{t('reports.title')}</Typography>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExportReport('pdf')}
            >
              {t('reports.exportPdf')}
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExportReport('excel')}
            >
              {t('reports.exportExcel')}
            </Button>
          </Box>
        </Box>

        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label={t('reports.startDate')}
                value={dateRange.start}
                onChange={(newValue) => setDateRange({ ...dateRange, start: newValue || new Date() })}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label={t('reports.endDate')}
                value={dateRange.end}
                onChange={(newValue) => setDateRange({ ...dateRange, end: newValue || new Date() })}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Model</InputLabel>
                <Select
                  value={selectedModel}
                  label={t('reports.model')}
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  <MenuItem value="all">All Models</MenuItem>
                  {models.map((model: any) => (
                    <MenuItem key={model.id} value={model.id}>
                      {model.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={() => window.location.reload()}
                fullWidth
              >
                Refresh
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {t('reports.totalTests')}
                    </Typography>
                    <Typography variant="h4">
                      {data.totalTests}
                    </Typography>
                  </Box>
                  <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {t('reports.successRate')}
                    </Typography>
                    <Typography variant="h4">
                      {successRate.toFixed(1)}%
                    </Typography>
                  </Box>
                  <TrendingUpIcon sx={{ fontSize: 40, color: 'success.main' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {t('reports.failedTests')}
                    </Typography>
                    <Typography variant="h4" color="error">
                      {data.failedTests}
                    </Typography>
                  </Box>
                  <AssessmentIcon sx={{ fontSize: 40, color: 'error.main' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {t('reports.avgExecutionTime')}
                    </Typography>
                    <Typography variant="h4">
                      {data.averageExecutionTime.toFixed(1)}s
                    </Typography>
                  </Box>
                  <ScheduleIcon sx={{ fontSize: 40, color: 'warning.main' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Charts */}
        <Grid container spacing={3} sx={{ flexGrow: 1, overflow: 'auto' }}>
          {/* Test Trends */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Test Trends Over Time
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={data.testTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="total" stroke="#8884d8" name={t('reports.totalTests')} />
                    <Line type="monotone" dataKey="successful" stroke="#82ca9d" name={t('reports.successful')} />
                    <Line type="monotone" dataKey="failed" stroke="#ffc658" name={t('reports.failed')} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Status Distribution */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Status Distribution
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={data.statusDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name} (${percentage}%)`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {data.statusDistribution.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Model Performance */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Performance
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={data.modelPerformance}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="modelName" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="successRate" fill="#8884d8" name="Success Rate (%)" />
                    <Bar dataKey="averageTime" fill="#82ca9d" name="Avg. Time (s)" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Detailed Table */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Performance Details
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Model Name</TableCell>
                        <TableCell align="right">Total Tests</TableCell>
                        <TableCell align="right">Success Rate</TableCell>
                        <TableCell align="right">Average Time (s)</TableCell>
                        <TableCell align="right">Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.modelPerformance.map((model: any, index: number) => (
                        <TableRow key={index}>
                          <TableCell>{model.modelName}</TableCell>
                          <TableCell align="right">{model.totalTests}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${model.successRate.toFixed(1)}%`}
                              color={model.successRate >= 90 ? 'success' : model.successRate >= 70 ? 'warning' : 'error'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">{model.averageTime.toFixed(2)}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={model.successRate >= 90 ? t('reports.excellent') : model.successRate >= 70 ? t('reports.good') : t('reports.needsImprovement')}
                              color={model.successRate >= 90 ? 'success' : model.successRate >= 70 ? 'warning' : 'error'}
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </LocalizationProvider>
  );
};

export default Reports;
