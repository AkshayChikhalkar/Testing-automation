import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material';
import {
  PlayArrow as RunIcon,
  FolderOpen as FolderIcon,
  Upload as UploadIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../../services/api';

const SimulationRunner: React.FC = () => {
  const [projectDirectory, setProjectDirectory] = useState('');
  const [paramsFile, setParamsFile] = useState<File | null>(null);
  const [paramsJson, setParamsJson] = useState('{}');
  const [paramOverrides, setParamOverrides] = useState('');
  const [batchMode, setBatchMode] = useState(false);
  const [dbMode, setDbMode] = useState(false);
  const [dbType, setDbType] = useState('influxdb');
  const [dbHost, setDbHost] = useState('193.16.126.186');
  const [dbPort, setDbPort] = useState(8086);
  const [dbToken, setDbToken] = useState('');
  const [dbOrg, setDbOrg] = useState('my-org');
  const [dbBucket, setDbBucket] = useState('simulations');
  const [startupScript, setStartupScript] = useState('');
  const [result, setResult] = useState<{ success: boolean; output?: string; error?: string } | null>(null);
  const [running, setRunning] = useState(false);

  // Fetch runner status and available models
  const { data: runnerStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['simulationRunnerStatus'],
    queryFn: () => apiService.simulations.getRunnerStatus().then((r) => r.data),
  });

  const { data: runnerModels = [] } = useQuery({
    queryKey: ['simulationRunnerModels'],
    queryFn: () => apiService.simulations.getRunnerModels().then((r) => r.data),
  });

  const handleSelectModel = (model: { model_directory: string; startup_script?: string }) => {
    setProjectDirectory(model.model_directory);
    if (model.startup_script) {
      setStartupScript(model.startup_script);
    }
  };

  const handleRun = async () => {
    if (!projectDirectory.trim()) {
      setResult({ success: false, error: 'Project directory is required.' });
      return;
    }
    setRunning(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('project_directory', projectDirectory.trim());
      formData.append('batch_mode', String(batchMode));
      formData.append('db_mode', String(dbMode));
      formData.append('db_type', dbType);
      if (paramsFile) {
        formData.append('params_file', paramsFile);
      }
      if (paramsJson && paramsJson !== '{}') {
        formData.append('params_json', paramsJson);
      }
      if (paramOverrides.trim()) {
        formData.append('param_overrides', paramOverrides.trim());
      }
      if (dbMode) {
        if (dbHost) formData.append('db_host', dbHost);
        if (dbPort) formData.append('db_port', String(dbPort));
        if (dbToken) formData.append('db_token', dbToken);
        if (dbOrg) formData.append('db_org', dbOrg);
        if (dbBucket) formData.append('db_bucket', dbBucket);
      }
      if (startupScript.trim()) {
        formData.append('startup_script', startupScript.trim());
      }

      const response = await apiService.simulations.run(formData);
      const data = response.data;
      setResult({
        success: data.success,
        output: data.output,
        error: data.error,
      });
    } catch (err: any) {
      setResult({
        success: false,
        error: err.response?.data?.detail || err.message || 'Run failed.',
      });
    } finally {
      setRunning(false);
    }
  };

  if (statusLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
      </Box>
    );
  }

  if (!runnerStatus?.available) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          MATLAB Simulation Runner
        </Typography>
        <Alert severity="error" sx={{ mt: 2 }}>
          Simulation runner is not available. Ensure:
          <ul>
            <li>The <strong>simulationsmodelle</strong> project is a sibling of Testing automation, or</li>
            <li>Set <code>SIMULATIONS_PROJECT_PATH</code> environment variable to the simulationsmodelle root directory.</li>
          </ul>
          Path expected: {runnerStatus?.simulations_path || 'Not configured'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        MATLAB Simulation Runner
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Run MATLAB Simulink models with custom parameters via simulationsmodelle CLI. Supports single run, batch mode (CSV), and database export.
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Project & Parameters
          </Typography>

          {runnerModels.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Registered Models (directory-based)
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {runnerModels.map((m: any) => (
                  <Chip
                    key={m.id}
                    label={m.name}
                    onClick={() => handleSelectModel(m)}
                    color={projectDirectory === m.model_directory ? 'primary' : 'default'}
                    variant={projectDirectory === m.model_directory ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            </Box>
          )}

          <TextField
            fullWidth
            label="Project Directory"
            value={projectDirectory}
            onChange={(e) => setProjectDirectory(e.target.value)}
            placeholder="C:\path\to\your-model-project"
            sx={{ mb: 2 }}
            helperText="Project root with run_simulation.py and a startup_*.m script (folder name can be anything)"
          />

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Parameters Input (choose one)
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Box display="flex" alignItems="center" gap={2}>
                <input
                  type="file"
                  accept=".csv,.json"
                  onChange={(e) => setParamsFile(e.target.files?.[0] || null)}
                  id="params-file"
                  style={{ display: 'none' }}
                />
                <label htmlFor="params-file">
                  <Button variant="outlined" component="span" startIcon={<UploadIcon />}>
                    Upload CSV/JSON params file
                  </Button>
                </label>
                {paramsFile && (
                  <Chip label={paramsFile.name} onDelete={() => setParamsFile(null)} size="small" />
                )}
              </Box>
              <TextField
                label="Or inline JSON params"
                fullWidth
                multiline
                rows={4}
                value={paramsJson}
                onChange={(e) => setParamsJson(e.target.value)}
                placeholder='{"STAB1.SecondaryStabCtrl.PositionCtrl.Kp": 0.5}'
                helperText="Format: param.path = value"
              />
              <TextField
                label="Or param overrides (comma-separated)"
                fullWidth
                value={paramOverrides}
                onChange={(e) => setParamOverrides(e.target.value)}
                placeholder="param.path=value,param2.path=0.3"
              />
            </Box>
          </Box>

          <FormControlLabel
            control={<Switch checked={batchMode} onChange={(e) => setBatchMode(e.target.checked)} />}
            label="Batch mode (CSV with multiple rows = multiple simulations)"
          />
        </CardContent>
      </Card>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Database Export Options</Typography>
          {dbMode && <Chip label="Enabled" color="primary" size="small" sx={{ ml: 2 }} />}
        </AccordionSummary>
        <AccordionDetails>
          <FormControlLabel
            control={<Switch checked={dbMode} onChange={(e) => setDbMode(e.target.checked)} />}
            label="Export results to database (InfluxDB/TimescaleDB)"
          />
          {dbMode && (
            <Box sx={{ display: 'grid', gap: 2, mt: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Database Type</InputLabel>
                <Select value={dbType} onChange={(e) => setDbType(e.target.value)} label="Database Type">
                  <MenuItem value="influxdb">InfluxDB</MenuItem>
                  <MenuItem value="timescaledb">TimescaleDB</MenuItem>
                </Select>
              </FormControl>
              <TextField label="Host" value={dbHost} onChange={(e) => setDbHost(e.target.value)} />
              <TextField label="Port" type="number" value={dbPort} onChange={(e) => setDbPort(Number(e.target.value))} />
              <TextField label="Token (InfluxDB)" type="password" value={dbToken} onChange={(e) => setDbToken(e.target.value)} helperText="Or set INFLUXDB_TOKEN env var" />
              <TextField label="Org" value={dbOrg} onChange={(e) => setDbOrg(e.target.value)} />
              <TextField label="Bucket" value={dbBucket} onChange={(e) => setDbBucket(e.target.value)} />
            </Box>
          )}
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Advanced</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <TextField
            fullWidth
            label="Custom Startup Script"
            value={startupScript}
            onChange={(e) => setStartupScript(e.target.value)}
            placeholder="Optional: path to startup_MDL.m"
          />
        </AccordionDetails>
      </Accordion>

      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          startIcon={running ? <CircularProgress size={20} /> : <RunIcon />}
          onClick={handleRun}
          disabled={running}
        >
          {running ? 'Running...' : 'Run Simulation'}
        </Button>
      </Box>

      {result && (
        <Paper sx={{ mt: 3, p: 2 }}>
          <Box display="flex" alignItems="center" gap={1} mb={2}>
            {result.success ? (
              <SuccessIcon color="success" />
            ) : (
              <ErrorIcon color="error" />
            )}
            <Typography variant="h6">
              {result.success ? 'Simulation completed' : 'Simulation failed'}
            </Typography>
          </Box>
          {(result.output || result.error) && (
            <TextField
              fullWidth
              multiline
              rows={12}
              value={result.output || result.error || ''}
              InputProps={{ readOnly: true }}
              sx={{
                fontFamily: 'monospace',
                '& .MuiInputBase-input': { fontSize: '0.85rem' },
              }}
            />
          )}
        </Paper>
      )}
    </Box>
  );
};

export default SimulationRunner;
