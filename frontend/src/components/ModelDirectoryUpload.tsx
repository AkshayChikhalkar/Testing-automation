import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Autocomplete,
  Divider,
} from '@mui/material';
import { FolderOpen as FolderIcon, Upload as UploadIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

interface ModelDirectoryUploadProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: DirectoryUploadData) => void;
  loading?: boolean;
  editingModel?: any; // Add this for editing existing models
}

interface DirectoryUploadData {
  name: string;
  description: string;
  directory_path: string;
  version: string;
  category: string;
  author: string;
  tags: string[];
  parameters: string;
}

const ModelDirectoryUpload: React.FC<ModelDirectoryUploadProps> = ({
  open,
  onClose,
  onSubmit,
  loading = false,
  editingModel = null,
}) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<DirectoryUploadData>({
    name: editingModel?.name || '',
    description: editingModel?.description || '',
    directory_path: editingModel?.model_directory || '',
    version: editingModel?.version || '1.0.0',
    category: editingModel?.category || '',
    author: editingModel?.author || '',
    tags: editingModel?.tags || [],
    parameters: editingModel?.parameters ? JSON.stringify(editingModel.parameters) : '{}',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const categories = [
    'Simulink Model',
    'MATLAB Script',
    'Control System',
    'Simulation',
    'Test Model',
    'Research Model',
  ];

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Model name is required';
    }

    if (!formData.directory_path.trim()) {
      newErrors.directory_path = 'Directory path is required';
    } else if (!formData.directory_path.includes('simulationsmodelle')) {
      newErrors.directory_path = 'Please select a valid simulationsmodelle directory';
    }

    if (formData.parameters && formData.parameters !== '{}') {
      try {
        JSON.parse(formData.parameters);
      } catch {
        newErrors.parameters = 'Parameters must be valid JSON';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleClose = () => {
    setFormData({
      name: editingModel?.name || '',
      description: editingModel?.description || '',
      directory_path: editingModel?.model_directory || '',
      version: editingModel?.version || '1.0.0',
      category: editingModel?.category || '',
      author: editingModel?.author || '',
      tags: editingModel?.tags || [],
      parameters: editingModel?.parameters ? JSON.stringify(editingModel.parameters) : '{}',
    });
    setErrors({});
    onClose();
  };

  const handleDirectorySelect = () => {
    // In a real implementation, this would open a directory picker
    // For now, we'll use a text input with a placeholder
    const path = prompt('Enter the path to the simulationsmodelle-main directory:');
    if (path) {
      setFormData({ ...formData, directory_path: path });
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <FolderIcon color="primary" />
          <Typography variant="h6">
            {editingModel ? 'Edit MATLAB Model Directory' : 'Upload MATLAB Model Directory'}
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Alert severity="info" sx={{ mb: 3 }}>
          {editingModel 
            ? 'Edit the metadata for your MATLAB model directory. The directory path and startup script are automatically detected.'
            : 'Upload a complete MATLAB model directory (like simulationsmodelle-main) with all dependencies. The system will automatically detect startup scripts and initialize the model properly.'
          }
        </Alert>

        <Box sx={{ display: 'grid', gap: 3, mt: 2 }}>
          <TextField
            label="Model Name"
            fullWidth
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={!!errors.name}
            helperText={errors.name}
            placeholder="e.g., MonoCab Stabilization Model"
          />

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Model Directory Path
            </Typography>
            <Box display="flex" gap={1}>
              <TextField
                fullWidth
                value={formData.directory_path}
                onChange={(e) => setFormData({ ...formData, directory_path: e.target.value })}
                error={!!errors.directory_path}
                helperText={errors.directory_path || 'Path to the simulationsmodelle-main directory'}
                placeholder="C:\path\to\simulationsmodelle-main"
                disabled={!!editingModel} // Disable editing directory path for existing models
              />
              {!editingModel && (
                <Button
                  variant="outlined"
                  startIcon={<FolderIcon />}
                  onClick={handleDirectorySelect}
                  sx={{ minWidth: 'auto', px: 2 }}
                >
                  Browse
                </Button>
              )}
            </Box>
          </Box>

          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Describe what this model does and its purpose..."
          />

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label="Version"
              value={formData.version}
              onChange={(e) => setFormData({ ...formData, version: e.target.value })}
              placeholder="1.0.0"
            />

            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                label="Category"
              >
                {categories.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {cat}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <TextField
            label="Author"
            fullWidth
            value={formData.author}
            onChange={(e) => setFormData({ ...formData, author: e.target.value })}
            placeholder="Your name or organization"
          />

          <Autocomplete
            multiple
            freeSolo
            options={['control', 'simulation', 'stabilization', 'monocab', 'matlab', 'simulink']}
            value={formData.tags}
            onChange={(_, newValue) => setFormData({ ...formData, tags: newValue })}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip variant="outlined" label={option} {...getTagProps({ index })} />
              ))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Tags"
                placeholder="Add tags to categorize your model"
              />
            )}
          />

          <Divider />

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Advanced Parameters (JSON)
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={formData.parameters}
              onChange={(e) => setFormData({ ...formData, parameters: e.target.value })}
              error={!!errors.parameters}
              helperText={errors.parameters || 'Optional JSON object with model parameters'}
              placeholder='{"param1": "value1", "param2": 123}'
            />
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          startIcon={<UploadIcon />}
          disabled={loading}
        >
          {loading ? (editingModel ? 'Updating...' : 'Uploading...') : (editingModel ? 'Update Directory' : 'Upload Directory')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ModelDirectoryUpload;
