import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Fab,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as RunIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { formatGermanDateOnly } from '../../utils/dateFormatting';

import { apiService } from '../../services/api';

interface Model {
  id: number;
  name: string;
  description: string;
  version: string;
  status: 'active' | 'inactive' | 'training';
  created_at: string;
  updated_at: string;
  file_size: number;
  accuracy?: number;
}

const Models: React.FC = () => {
  const { t } = useTranslation();
  const [openDialog, setOpenDialog] = useState(false);
  const [editingModel, setEditingModel] = useState<Model | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    version: '1.0.0',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [advanced, setAdvanced] = useState({
    category: '',
    tags: '', // comma-separated or JSON
    author: '',
    startup_script: '',
    parameters: '{}', // JSON
  });
  const [startupFile, setStartupFile] = useState<File | null>(null);

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Fetch models
  const { data: models = [], isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: () => apiService.models.list().then(res => res.data),
  });

  // Create/Update model mutation
  const createModelMutation = useMutation({
    mutationFn: apiService.models.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      setOpenDialog(false);
      resetForm();
    },
  });

  const updateModelMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => apiService.models.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      setOpenDialog(false);
      resetForm();
    },
  });

  const deleteModelMutation = useMutation({
    mutationFn: apiService.models.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  const resetForm = () => {
    setFormData({ name: '', description: '', version: '1.0.0' });
    setEditingModel(null);
    setSelectedFile(null);
    setAdvancedOpen(false);
    setAdvanced({ category: '', tags: '', author: '', startup_script: '', parameters: '{}' });
    setStartupFile(null);
  };

  const handleOpenDialog = (model?: Model) => {
    if (model) {
      setEditingModel(model);
      setFormData({
        name: model.name,
        description: model.description,
        version: model.version,
      });
    } else {
      resetForm();
    }
    setOpenDialog(true);
  };

  const handleSubmit = () => {
    if (editingModel) {
      updateModelMutation.mutate({ id: editingModel.id, data: formData });
      return;
    }

    // If a file is chosen, use upload endpoint
    if (selectedFile) {
      const fd = new FormData();
      fd.append('file', selectedFile);
      fd.append('name', formData.name);
      if (formData.description) fd.append('description', formData.description);
      if (formData.version) fd.append('version', formData.version);
      if (advanced.category) fd.append('category', advanced.category);
      if (advanced.author) fd.append('author', advanced.author);
      if (startupFile) {
        fd.append('startup_script_file', startupFile);
      } else if (advanced.startup_script) {
        fd.append('startup_script', advanced.startup_script);
      }
      if (advanced.tags) fd.append('tags', advanced.tags);
      if (advanced.parameters) fd.append('parameters', advanced.parameters);
      // category optional; skip for now

      apiService.models.upload(fd)
        .then(() => {
          queryClient.invalidateQueries({ queryKey: ['models'] });
          setOpenDialog(false);
          resetForm();
        })
        .catch(() => { /* silently fail, UI could add snackbar later */ });
      return;
    }

    // No file: create metadata-only model
    createModelMutation.mutate(formData);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this model?')) {
      deleteModelMutation.mutate(id);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'training': return 'warning';
      default: return 'default';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading models...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('models.title')}</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          {t('models.addNewModel')}
        </Button>
      </Box>

      <Grid container spacing={3} sx={{ flexGrow: 1, overflow: 'auto' }}>
        {models.map((model: Model) => (
          <Grid item xs={12} sm={6} md={4} key={model.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" component="div">
                    {model.name}
                  </Typography>
                  <Chip
                    label={model.status}
                    color={getStatusColor(model.status) as any}
                    size="small"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {model.description}
                </Typography>
                
                <Typography variant="body2" color="text.secondary">
                  Version: {model.version}
                </Typography>
                
                <Typography variant="body2" color="text.secondary">
                  Size: {formatFileSize(model.file_size)}
                </Typography>
                
                {model.accuracy && (
                  <Typography variant="body2" color="text.secondary">
                    Accuracy: {(model.accuracy * 100).toFixed(2)}%
                  </Typography>
                )}
                
                <Typography variant="body2" color="text.secondary">
                  Created: {formatGermanDateOnly(model.created_at)}
                </Typography>
              </CardContent>
              
              <CardActions>
                <Button
                  size="small"
                  startIcon={<RunIcon />}
                  onClick={() => navigate(`/test-runs?model=${model.id}`)}
                >
                  {t('models.runTest')}
                </Button>
                <Button
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={() => handleOpenDialog(model)}
                >
                  {t('common.edit')}
                </Button>
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => handleDelete(model.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
        
        {models.length === 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No models found
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={3}>
                  Get started by adding your first model
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => handleOpenDialog()}
                >
                  Add Model
                </Button>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Add/Edit Model Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingModel ? t('models.editModel') : t('models.addNewModel')}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('models.modelName')}
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <input
            type="file"
            accept=".slx,.m"
            onChange={(e) => setSelectedFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)}
            style={{ marginBottom: 16 }}
          />
          <TextField
            margin="dense"
            label={t('models.description')}
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('models.version')}
            fullWidth
            variant="outlined"
            value={formData.version}
            onChange={(e) => setFormData({ ...formData, version: e.target.value })}
          />

          {/* Advanced Section inside the dialog */}
          <Box sx={{ mt: 2 }}>
            <Button size="small" onClick={() => setAdvancedOpen(v => !v)}>
              {advancedOpen ? t('models.hideAdvanced') : t('models.showAdvanced')}
            </Button>
            {advancedOpen && (
              <Box sx={{ mt: 2, display: 'grid', gap: 2 }}>
                <TextField
                  label={t('models.category')}
                  fullWidth
                  value={advanced.category}
                  onChange={(e) => setAdvanced({ ...advanced, category: e.target.value })}
                />
                <TextField
                  label="Tags (comma-separated or JSON array)"
                  fullWidth
                  value={advanced.tags}
                  onChange={(e) => setAdvanced({ ...advanced, tags: e.target.value })}
                />
                <TextField
                  label={t('models.author')}
                  fullWidth
                  value={advanced.author}
                  onChange={(e) => setAdvanced({ ...advanced, author: e.target.value })}
                />
                <TextField
                  label={t('models.startupScriptPath')}
                  fullWidth
                  value={advanced.startup_script}
                  onChange={(e) => setAdvanced({ ...advanced, startup_script: e.target.value })}
                />
              <input
                type="file"
                accept=".m"
                onChange={(e) => setStartupFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)}
              />
                <TextField
                  label="Parameters (JSON)"
                  fullWidth
                  multiline
                  minRows={3}
                  value={advanced.parameters}
                  onChange={(e) => setAdvanced({ ...advanced, parameters: e.target.value })}
                />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.name || createModelMutation.isPending || updateModelMutation.isPending}
          >
            {editingModel ? t('common.update') : t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button for Upload */}
      <Tooltip title={t('models.uploadModel')}>
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => handleOpenDialog()}
        >
          <UploadIcon />
        </Fab>
      </Tooltip>
    </Box>
  );
};

export default Models;
