'use client';

import { useState } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  TextField, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  FormHelperText,
  Box
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { CheckFrequency, MessagePlatform } from '@/lib/supabase/types';

interface ScheduledCheckFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: ScheduledCheckFormData) => void;
  patientId: string;
}

export interface ScheduledCheckFormData {
  title: string;
  description: string;
  frequency: CheckFrequency;
  nextScheduled: Date;
  platform: MessagePlatform;
  patientId: string;
}

export default function ScheduledCheckForm({ open, onClose, onSubmit, patientId }: ScheduledCheckFormProps) {
  const [formData, setFormData] = useState<ScheduledCheckFormData>({
    title: '',
    description: '',
    frequency: 'daily',
    nextScheduled: new Date(Date.now() + 24 * 60 * 60 * 1000), // Tomorrow
    platform: 'telegram',
    patientId
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const handleChange = (field: keyof ScheduledCheckFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error for this field if it exists
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };
  
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }
    
    if (!formData.nextScheduled) {
      newErrors.nextScheduled = 'Next scheduled date is required';
    } else if (formData.nextScheduled < new Date()) {
      newErrors.nextScheduled = 'Next scheduled date must be in the future';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = () => {
    if (validateForm()) {
      onSubmit(formData);
    }
  };
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Scheduled Check</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            label="Title"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            fullWidth
            error={!!errors.title}
            helperText={errors.title}
            required
          />
          
          <TextField
            label="Description"
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            fullWidth
            multiline
            rows={3}
          />
          
          <FormControl fullWidth>
            <InputLabel>Frequency</InputLabel>
            <Select
              value={formData.frequency}
              onChange={(e) => handleChange('frequency', e.target.value)}
              label="Frequency"
            >
              <MenuItem value="daily">Daily</MenuItem>
              <MenuItem value="weekly">Weekly</MenuItem>
              <MenuItem value="monthly">Monthly</MenuItem>
              <MenuItem value="once">Once</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl fullWidth>
            <InputLabel>Platform</InputLabel>
            <Select
              value={formData.platform}
              onChange={(e) => handleChange('platform', e.target.value)}
              label="Platform"
            >
              <MenuItem value="telegram">Telegram</MenuItem>
              <MenuItem value="whatsapp">WhatsApp</MenuItem>
              <MenuItem value="sms">SMS</MenuItem>
              <MenuItem value="email">Email</MenuItem>
            </Select>
          </FormControl>
          
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DateTimePicker
              label="Next Scheduled Date"
              value={formData.nextScheduled}
              onChange={(date) => handleChange('nextScheduled', date)}
              slotProps={{
                textField: {
                  fullWidth: true,
                  error: !!errors.nextScheduled,
                  helperText: errors.nextScheduled
                }
              }}
            />
          </LocalizationProvider>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" color="primary">
          Add Check
        </Button>
      </DialogActions>
    </Dialog>
  );
} 