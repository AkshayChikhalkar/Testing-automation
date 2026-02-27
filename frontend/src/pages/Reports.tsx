import React from 'react';
import { Box } from '@mui/material';

const Reports: React.FC = () => {
  // Embed Grafana dashboard only, in light mode, with full Grafana controls (simulation_id, signals, etc.)
  const grafanaUrl =
    'http://193.16.126.186:3005/d/simulation-dashboard/simulation-data-dashboard' +
    '?orgId=1&var-bucket=simulations&var-measurement=simulation_data&from=now-3h&to=now' +
    '&theme=light';

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

