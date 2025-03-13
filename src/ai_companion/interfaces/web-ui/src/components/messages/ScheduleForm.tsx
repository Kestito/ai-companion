'use client';

import { useState } from 'react';
import { Button, TextField, Select, MenuItem, FormControl, InputLabel, Grid, Dialog, DialogTitle, DialogContent, DialogActions, FormHelperText } from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers';
import { addHours } from 'date-fns';

interface ScheduleFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: ScheduleRequest) => void;
}

export interface ScheduleRequest {
  recipientId: string;
  platform: 'whatsapp' | 'telegram';
  message: string;
  scheduledTime: Date;
  recurrence?: 'daily' | 'weekly' | 'monthly';
}

export const ScheduleForm = ({ open, onClose, onSubmit }: ScheduleFormProps) => {
  const [formData, setFormData] = useState<ScheduleRequest>({
    recipientId: '',
    platform: 'whatsapp',
    message: '',
    scheduledTime: addHours(new Date(), 1),
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.recipientId) newErrors.recipientId = 'Recipient is required';
    if (!formData.message) newErrors.message = 'Message is required';
    if (!formData.scheduledTime) newErrors.scheduledTime = 'Schedule time is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) {
      onSubmit(formData);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Schedule New Message</DialogTitle>
      <DialogContent>
        <Grid container spacing={3} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth error={!!errors.platform}>
              <InputLabel>Platform</InputLabel>
              <Select
                value={formData.platform}
                label="Platform"
                onChange={(e) => setFormData({ ...formData, platform: e.target.value as any })}
              >
                <MenuItem value="whatsapp">WhatsApp</MenuItem>
                <MenuItem value="telegram">Telegram</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Recipient ID"
              value={formData.recipientId}
              onChange={(e) => setFormData({ ...formData, recipientId: e.target.value })}
              error={!!errors.recipientId}
              helperText={errors.recipientId}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Message"
              multiline
              rows={4}
              value={formData.message}
              onChange={(e) => setFormData({ ...formData, message: e.target.value })}
              error={!!errors.message}
              helperText={errors.message}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <DateTimePicker
              label="Schedule Time"
              value={formData.scheduledTime}
              onChange={(newValue) => setFormData({ ...formData, scheduledTime: newValue || new Date() })}
              minDateTime={addHours(new Date(), 1)}
            />
            {errors.scheduledTime && <FormHelperText error>{errors.scheduledTime}</FormHelperText>}
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Recurrence</InputLabel>
              <Select
                value={formData.recurrence || ''}
                label="Recurrence"
                onChange={(e) => setFormData({ ...formData, recurrence: e.target.value as any })}
              >
                <MenuItem value="">None</MenuItem>
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
                <MenuItem value="monthly">Monthly</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit}>
          Schedule Message
        </Button>
      </DialogActions>
    </Dialog>
  );
}; 