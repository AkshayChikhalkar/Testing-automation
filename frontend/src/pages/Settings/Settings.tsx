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
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import apiClient from '../../services/api';


interface AppSettings {
  general: {
    appName: string;
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
  const { t, i18n } = useTranslation();
  
  const defaultSettings: AppSettings = {
    general: {
      appName: 'MATLAB Automation Platform',
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
  };

  const [settings, setSettings] = useState<AppSettings>(defaultSettings);

  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const [activeTab, setActiveTab] = useState('general');

  const queryClient = useQueryClient();

  // Fetch settings
  const { data: currentSettings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const res = await apiClient.get('/settings');
      const data = res.data || {};
      const loaded: AppSettings = {
        general: { ...defaultSettings.general, ...(data.general || {}) },
        matlab: { ...defaultSettings.matlab, ...(data.matlab || {}) },
        storage: { ...defaultSettings.storage, ...(data.storage || {}) },
        security: { ...defaultSettings.security, ...(data.security || {}) },
        appearance: { ...defaultSettings.appearance, ...(data.appearance || {}) },
      };
      return loaded;
    },
  });

  // Keep local form state in sync with server
  React.useEffect(() => {
    if (currentSettings) {
      setSettings(currentSettings);
    }
  }, [currentSettings]);

  // Save settings mutation
  const saveSettingsMutation = useMutation({
    mutationFn: async (newSettings: AppSettings) => {
      const res = await apiClient.put('/settings', newSettings);
      const data = res.data || {};
      const saved: AppSettings = {
        general: { ...defaultSettings.general, ...(data.general || {}) },
        matlab: { ...defaultSettings.matlab, ...(data.matlab || {}) },
        storage: { ...defaultSettings.storage, ...(data.storage || {}) },
        security: { ...defaultSettings.security, ...(data.security || {}) },
        appearance: { ...defaultSettings.appearance, ...(data.appearance || {}) },
      };
      return saved;
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Settings saved successfully!', severity: 'success' });
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: () => {
      setSnackbar({ open: true, message: t('settings.saveFailed'), severity: 'error' });
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
    { id: 'general', label: t('settings.general'), icon: <NotificationsIcon /> },
    { id: 'matlab', label: t('settings.matlab'), icon: <StorageIcon /> },
    { id: 'storage', label: t('settings.storage'), icon: <StorageIcon /> },
    { id: 'security', label: t('settings.security'), icon: <SecurityIcon /> },
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
            <CardHeader title={t('settings.categories')} />
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
                      label={t('settings.appName')}
                      value={settings.general.appName}
                      onChange={(e) => handleSettingChange('general', 'appName', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>{t('settings.language')}</InputLabel>
                      <Select
                        value={i18n.language}
                        label={t('settings.language')}
                        onChange={(e) => {
                          i18n.changeLanguage(e.target.value);
                          handleSettingChange('general', 'language', e.target.value);
                        }}
                      >
                        <MenuItem value="en">{t('languages.en')}</MenuItem>
                        <MenuItem value="es">{t('languages.es')}</MenuItem>
                        <MenuItem value="fr">{t('languages.fr')}</MenuItem>
                        <MenuItem value="de">{t('languages.de')}</MenuItem>
                        <MenuItem value="zh">{t('languages.zh')}</MenuItem>
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
                      label={t('settings.notifications')}
                    />
                  </Grid>
                </Grid>
              )}

              {activeTab === 'matlab' && (
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label={t('settings.matlabPath')}
                      value={settings.matlab.matlabPath}
                      onChange={(e) => handleSettingChange('matlab', 'matlabPath', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label={t('settings.simulinkPath')}
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
                      label={t('settings.backupEnabled')}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Backup Frequency</InputLabel>
                      <Select
                        value={settings.storage.backupFrequency}
                        label={t('settings.backupFrequency')}
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
                      label={t('settings.requireAuth')}
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
                      label={t('settings.allowGuestAccess')}
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
                      label={t('settings.auditLogging')}
                    />
                  </Grid>
                </Grid>
              )}

              {/* Appearance settings removed until fully supported in UI theme */}
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
