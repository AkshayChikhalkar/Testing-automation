import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';

const Reports: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['grafanaEmbed'],
    queryFn: async () => {
      const response = await apiService.reports.getGrafanaEmbed();
      return response.data as { url?: string; simulation_id?: string };
    },
    refetchInterval: 60_000,
  });

  const grafanaUrl = data?.url;

  if (isLoading) {
    return (
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !grafanaUrl) {
    return (
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
        <Typography color="text.secondary">
          Analytics dashboard is unavailable. Complete a test run with InfluxDB export, then refresh.
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        flex: 1,
        height: '100%',
        width: '100%',
        display: 'flex',
        p: 0,
      }}
    >
      <iframe
        src={grafanaUrl}
        title="Simulation Data Dashboard"
        style={{ border: 'none', width: '100%', height: '100%' }}
      />
    </Box>
  );
};

export default Reports;
