import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  Storage as StorageIcon,
  Notifications as NotificationsIcon,
  Palette as PaletteIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';


interface AppSettings {
  general: {
    appName: string;
    timezone: string;
    language: string;
    autoSave: boolean;
    notifications: boolean;
  };
  matlab: {
    matlabPath: string;
    simulinkPath: string;
    maxWorkers: number;
    timeout: number;
    autoCleanup: boolean;
  };
  storage: {
    maxFileSize: number;
    retentionDays: number;
    backupEnabled: boolean;
    backupFrequency: string;
  };
  security: {
    sessionTimeout: number;
    requireAuth: boolean;
    allowGuestAccess: boolean;
    auditLogging: boolean;
  };
  appearance: {
    theme: 'light' | 'dark' | 'auto';
    primaryColor: string;
    fontSize: number;
    compactMode: boolean;
  };
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>({
    general: {
      appName: 'MATLAB Automation Platform',
      timezone: 'UTC',
      language: 'en',
      autoSave: true,
      notifications: true,
    },
    matlab: {
      matlabPath: '/usr/local/MATLAB/R2023b',
      simulinkPath: '/usr/local/MATLAB/R2023b/simulink',
      maxWorkers: 4,
      timeout: 300,
      autoCleanup: true,
    },
    storage: {
      maxFileSize: 100,
      retentionDays: 30,
      backupEnabled: true,
      backupFrequency: 'daily',
    },
    security: {
      sessionTimeout: 60,
      requireAuth: true,
      allowGuestAccess: false,
      auditLogging: true,
    },
    appearance: {
      theme: 'light',
      primaryColor: '#1976d2',
      fontSize: 14,
      compactMode: false,
    },
  });

  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const [activeTab, setActiveTab] = useState('general');

  const queryClient = useQueryClient();

  // Fetch settings
  const { data: currentSettings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => {
      // Mock data for now - replace with actual API call
      return Promise.resolve(settings);
    },
  });

  // Save settings mutation
  const saveSettingsMutation = useMutation({
    mutationFn: (newSettings: AppSettings) => {
      // Mock save - replace with actual API call
      return Promise.resolve(newSettings);
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Settings saved successfully!', severity: 'success' });
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to save settings', severity: 'error' });
    },
  });

  const handleSave = () => {
    saveSettingsMutation.mutate(settings);
  };

  const handleReset = () => {
    if (currentSettings) {
      setSettings(currentSettings);
    }
  };

  const handleSettingChange = (section: keyof AppSettings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  const tabs = [
    { id: 'general', label: 'General', icon: <NotificationsIcon /> },
    { id: 'matlab', label: 'MATLAB', icon: <StorageIcon /> },
    { id: 'storage', label: 'Storage', icon: <StorageIcon /> },
    { id: 'security', label: 'Security', icon: <SecurityIcon /> },
    { id: 'appearance', label: 'Appearance', icon: <PaletteIcon /> },
  ];

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading settings...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Settings</Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleReset}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={saveSettingsMutation.isPending}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ flexGrow: 1, overflow: 'auto' }}>
        {/* Settings Navigation */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader title="Categories" />
            <List>
              {tabs.map((tab) => (
                <ListItem
                  key={tab.id}
                  button
                  selected={activeTab === tab.id}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <ListItemText primary={tab.label} />
                </ListItem>
              ))}
            </List>
          </Card>
        </Grid>

        {/* Settings Content */}
        <Grid item xs={12} md={9}>
          <Card>
            <CardHeader title={tabs.find(t => t.id === activeTab)?.label} />
            <CardContent>
              {activeTab === 'general' && (
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Application Name"
                      value={settings.general.appName}
                      onChange={(e) => handleSettingChange('general', 'appName', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Timezone</InputLabel>
                      <Select
                        value={settings.general.timezone}
                        label="Timezone"
                        onChange={(e) => handleSettingChange('general', 'timezone', e.target.value)}
                      >
                        <MenuItem value="UTC">UTC</MenuItem>
                        <MenuItem value="America/New_York">Eastern Time</MenuItem>
                        <MenuItem value="America/Chicago">Central Time</MenuItem>
                        <MenuItem value="America/Denver">Mountain Time</MenuItem>
                        <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                        <MenuItem value="Europe/London">London</MenuItem>
                        <MenuItem value="Europe/Paris">Paris</MenuItem>
                        <MenuItem value="Asia/Tokyo">Tokyo</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Language</InputLabel>
                      <Select
                        value={settings.general.language}
                        label="Language"
                        onChange={(e) => handleSettingChange('general', 'language', e.target.value)}
                      >
                        <MenuItem value="en">English</MenuItem>
                        <MenuItem value="es">Spanish</MenuItem>
                        <MenuItem value="fr">French</MenuItem>
                        <MenuItem value="de">German</MenuItem>
                        <MenuItem value="zh">Chinese</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.general.autoSave}
                          onChange={(e) => handleSettingChange('general', 'autoSave', e.target.checked)}
                        />
                      }
                      label="Auto-save changes"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.general.notifications}
                          onChange={(e) => handleSettingChange('general', 'notifications', e.target.checked)}
                        />
                      }
                      label="Enable notifications"
                    />
                  </Grid>
                </Grid>
              )}

              {activeTab === 'matlab' && (
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="MATLAB Installation Path"
                      value={settings.matlab.matlabPath}
                      onChange={(e) => handleSettingChange('matlab', 'matlabPath', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Simulink Path"
                      value={settings.matlab.simulinkPath}
                      onChange={(e) => handleSettingChange('matlab', 'simulinkPath', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography gutterBottom>Maximum Workers</Typography>
                    <Slider
                      value={settings.matlab.maxWorkers}
                      onChange={(_, value) => handleSettingChange('matlab', 'maxWorkers', value)}
                      min={1}
                      max={16}
                      step={1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography gutterBottom>Timeout (seconds)</Typography>
                    <Slider
                      value={settings.matlab.timeout}
                      onChange={(_, value) => handleSettingChange('matlab', 'timeout', value)}
                      min={60}
                      max={3600}
                      step={60}
                      marks={[
                        { value: 60, label: '1m' },
                        { value: 300, label: '5m' },
                        { value: 600, label: '10m' },
                        { value: 1800, label: '30m' },
                        { value: 3600, label: '1h' },
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.matlab.autoCleanup}
                          onChange={(e) => handleSettingChange('matlab', 'autoCleanup', e.target.checked)}
                        />
                      }
                      label="Auto-cleanup temporary files"
                    />
                  </Grid>
                </Grid>
              )}

              {activeTab === 'storage' && (
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <Typography gutterBottom>Maximum File Size (MB)</Typography>
                    <Slider
                      value={settings.storage.maxFileSize}
                      onChange={(_, value) => handleSettingChange('storage', 'maxFileSize', value)}
                      min={10}
                      max={1000}
                      step={10}
                      marks={[
                        { value: 10, label: '10MB' },
                        { value: 100, label: '100MB' },
                        { value: 500, label: '500MB' },
                        { value: 1000, label: '1GB' },
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography gutterBottom>Data Retention (days)</Typography>
                    <Slider
                      value={settings.storage.retentionDays}
                      onChange={(_, value) => handleSettingChange('storage', 'retentionDays', value)}
                      min={7}
                      max={365}
                      step={7}
                      marks={[
                        { value: 7, label: '1 week' },
                        { value: 30, label: '1 month' },
                        { value: 90, label: '3 months' },
                        { value: 365, label: '1 year' },
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.storage.backupEnabled}
                          onChange={(e) => handleSettingChange('storage', 'backupEnabled', e.target.checked)}
                        />
                      }
                      label="Enable automatic backups"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Backup Frequency</InputLabel>
                      <Select
                        value={settings.storage.backupFrequency}
                        label="Backup Frequency"
                        onChange={(e) => handleSettingChange('storage', 'backupFrequency', e.target.value)}
                      >
                        <MenuItem value="hourly">Hourly</MenuItem>
                        <MenuItem value="daily">Daily</MenuItem>
                        <MenuItem value="weekly">Weekly</MenuItem>
                        <MenuItem value="monthly">Monthly</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              )}

              {activeTab === 'security' && (
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <Typography gutterBottom>Session Timeout (minutes)</Typography>
                    <Slider
                      value={settings.security.sessionTimeout}
                      onChange={(_, value) => handleSettingChange('security', 'sessionTimeout', value)}
                      min={15}
                      max={480}
                      step={15}
                      marks={[
                        { value: 15, label: '15m' },
                        { value: 60, label: '1h' },
                        { value: 240, label: '4h' },
                        { value: 480, label: '8h' },
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.security.requireAuth}
                          onChange={(e) => handleSettingChange('security', 'requireAuth', e.target.checked)}
                        />
                      }
                      label="Require authentication"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.security.allowGuestAccess}
                          onChange={(e) => handleSettingChange('security', 'allowGuestAccess', e.target.checked)}
                        />
                      }
                      label="Allow guest access"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.security.auditLogging}
                          onChange={(e) => handleSettingChange('security', 'auditLogging', e.target.checked)}
                        />
                      }
                      label="Enable audit logging"
                    />
                  </Grid>
                </Grid>
              )}

              {activeTab === 'appearance' && (
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Theme</InputLabel>
                      <Select
                        value={settings.appearance.theme}
                        label="Theme"
                        onChange={(e) => handleSettingChange('appearance', 'theme', e.target.value)}
                      >
                        <MenuItem value="light">Light</MenuItem>
                        <MenuItem value="dark">Dark</MenuItem>
                        <MenuItem value="auto">Auto (System)</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Primary Color"
                      type="color"
                      value={settings.appearance.primaryColor}
                      onChange={(e) => handleSettingChange('appearance', 'primaryColor', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography gutterBottom>Font Size</Typography>
                    <Slider
                      value={settings.appearance.fontSize}
                      onChange={(_, value) => handleSettingChange('appearance', 'fontSize', value)}
                      min={12}
                      max={18}
                      step={1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.appearance.compactMode}
                          onChange={(e) => handleSettingChange('appearance', 'compactMode', e.target.checked)}
                        />
                      }
                      label="Compact mode"
                    />
                  </Grid>
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;
