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
  const [openDialog, setOpenDialog] = useState(false);
  const [editingModel, setEditingModel] = useState<Model | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    version: '1.0.0',
  });

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
    } else {
      createModelMutation.mutate(formData);
    }
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
        <Typography variant="h4">Models</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Model
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
                  Created: {new Date(model.created_at).toLocaleDateString()}
                </Typography>
              </CardContent>
              
              <CardActions>
                <Button
                  size="small"
                  startIcon={<RunIcon />}
                  onClick={() => navigate(`/test-runs?model=${model.id}`)}
                >
                  Run Test
                </Button>
                <Button
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={() => handleOpenDialog(model)}
                >
                  Edit
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
          {editingModel ? 'Edit Model' : 'Add New Model'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Model Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
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
            label="Version"
            fullWidth
            variant="outlined"
            value={formData.version}
            onChange={(e) => setFormData({ ...formData, version: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.name || createModelMutation.isPending || updateModelMutation.isPending}
          >
            {editingModel ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button for Upload */}
      <Tooltip title="Upload Model">
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => {/* Handle file upload */}}
        >
          <UploadIcon />
        </Fab>
      </Tooltip>
    </Box>
  );
};

export default Models;
