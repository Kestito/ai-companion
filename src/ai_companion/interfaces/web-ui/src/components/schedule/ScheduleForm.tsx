import React, { useState } from 'react';
import {
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Typography,
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Grid,
  Box,
  Snackbar,
  Alert,
  Paper
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { usePatients } from '@/hooks/usePatients';

type ScheduleFormProps = {
  onSuccess?: () => void;
};

export function ScheduleForm({ onSuccess }: ScheduleFormProps) {
  const { patients, isLoading } = usePatients();
  const [isRecurring, setIsRecurring] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<{open: boolean, message: string, severity: 'success' | 'error'}>({
    open: false,
    message: '',
    severity: 'success'
  });
  
  const [formData, setFormData] = useState({
    patientId: '',
    platform: 'telegram',
    message: '',
    date: new Date(),
    time: new Date(),
    recurrenceType: 'daily',
    recurrenceDay: 'monday',
    recurrenceDate: '1',
  });

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleCloseToast = () => {
    setToast({ ...toast, open: false });
  };

  const showToast = (message: string, severity: 'success' | 'error') => {
    setToast({
      open: true,
      message,
      severity
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Find the selected patient to get their platform-specific ID
      const selectedPatient = patients?.find(p => p.id === formData.patientId);
      if (!selectedPatient) {
        showToast("Please select a valid patient", "error");
        setIsSubmitting(false);
        return;
      }

      // Extract recipient ID based on platform
      let recipientId = '';
      if (formData.platform === 'telegram') {
        // Extract Telegram ID from phone field (format: "telegram:12345678")
        const telegramMatch = selectedPatient.phone?.match(/telegram:(\d+)/);
        recipientId = telegramMatch ? telegramMatch[1] : '';
      } else if (formData.platform === 'whatsapp') {
        // Extract WhatsApp number from phone field
        recipientId = selectedPatient.phone?.replace('whatsapp:', '') || '';
      }

      if (!recipientId) {
        showToast(`No ${formData.platform} contact information found for this patient`, "error");
        setIsSubmitting(false);
        return;
      }

      // Combine date and time
      const scheduledDate = new Date(formData.date);
      const timeDate = new Date(formData.time);
      scheduledDate.setHours(timeDate.getHours(), timeDate.getMinutes(), 0, 0);

      // Prepare recurrence pattern if applicable
      let recurrence = null;
      if (isRecurring) {
        if (formData.recurrenceType === 'daily') {
          recurrence = { type: 'daily' };
        } else if (formData.recurrenceType === 'weekly') {
          recurrence = { 
            type: 'weekly', 
            day: formData.recurrenceDay 
          };
        } else if (formData.recurrenceType === 'monthly') {
          recurrence = { 
            type: 'monthly', 
            day: parseInt(formData.recurrenceDate) 
          };
        }
      }

      // Send to API
      const response = await fetch('/api/scheduled-messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patientId: formData.patientId,
          recipientId,
          platform: formData.platform,
          message: formData.message,
          scheduledTime: scheduledDate.toISOString(),
          recurrence,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to schedule message');
      }

      showToast("Message scheduled successfully", "success");

      // Reset form
      setFormData({
        patientId: '',
        platform: 'telegram',
        message: '',
        date: new Date(),
        time: new Date(),
        recurrenceType: 'daily',
        recurrenceDay: 'monday',
        recurrenceDate: '1',
      });
      setIsRecurring(false);

      // Call success callback if provided
      if (onSuccess) {
        onSuccess();
      }
    } catch (error: any) {
      showToast(error.message || "Failed to schedule message", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card sx={{ maxWidth: '800px', mx: 'auto' }}>
      <CardHeader 
        title="Schedule a Message" 
        subheader="Schedule a message to be sent to a patient via Telegram or WhatsApp"
      />
      <CardContent>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControl fullWidth disabled={isLoading}>
                <InputLabel id="patient-label">Patient</InputLabel>
                <Select
                  labelId="patient-label"
                  value={formData.patientId}
                  onChange={(e) => handleChange('patientId', e.target.value)}
                  label="Patient"
                >
                  {patients?.map((patient) => (
                    <MenuItem key={patient.id} value={patient.id}>
                      {patient.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id="platform-label">Platform</InputLabel>
                <Select
                  labelId="platform-label"
                  value={formData.platform}
                  onChange={(e) => handleChange('platform', e.target.value)}
                  label="Platform"
                >
                  <MenuItem value="telegram">Telegram</MenuItem>
                  <MenuItem value="whatsapp">WhatsApp</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                label="Message"
                multiline
                rows={4}
                value={formData.message}
                onChange={(e) => handleChange('message', e.target.value)}
                fullWidth
                required
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label="Date"
                  value={formData.date}
                  onChange={(date) => date && handleChange('date', date)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>

            <Grid item xs={12} md={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <TimePicker
                  label="Time"
                  value={formData.time}
                  onChange={(time) => time && handleChange('time', time)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch 
                    checked={isRecurring}
                    onChange={(e) => setIsRecurring(e.target.checked)}
                  />
                }
                label="Recurring Schedule"
              />
            </Grid>

            {isRecurring && (
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Recurrence Settings
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <FormControl fullWidth>
                        <InputLabel id="recurrence-type-label">Recurrence Type</InputLabel>
                        <Select
                          labelId="recurrence-type-label"
                          value={formData.recurrenceType}
                          onChange={(e) => handleChange('recurrenceType', e.target.value)}
                          label="Recurrence Type"
                        >
                          <MenuItem value="daily">Daily</MenuItem>
                          <MenuItem value="weekly">Weekly</MenuItem>
                          <MenuItem value="monthly">Monthly</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    {formData.recurrenceType === 'weekly' && (
                      <Grid item xs={12}>
                        <FormControl fullWidth>
                          <InputLabel id="day-of-week-label">Day of Week</InputLabel>
                          <Select
                            labelId="day-of-week-label"
                            value={formData.recurrenceDay}
                            onChange={(e) => handleChange('recurrenceDay', e.target.value)}
                            label="Day of Week"
                          >
                            <MenuItem value="monday">Monday</MenuItem>
                            <MenuItem value="tuesday">Tuesday</MenuItem>
                            <MenuItem value="wednesday">Wednesday</MenuItem>
                            <MenuItem value="thursday">Thursday</MenuItem>
                            <MenuItem value="friday">Friday</MenuItem>
                            <MenuItem value="saturday">Saturday</MenuItem>
                            <MenuItem value="sunday">Sunday</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                    )}

                    {formData.recurrenceType === 'monthly' && (
                      <Grid item xs={12}>
                        <FormControl fullWidth>
                          <InputLabel id="day-of-month-label">Day of Month</InputLabel>
                          <Select
                            labelId="day-of-month-label"
                            value={formData.recurrenceDate}
                            onChange={(e) => handleChange('recurrenceDate', e.target.value)}
                            label="Day of Month"
                          >
                            {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
                              <MenuItem key={day} value={day.toString()}>
                                {day}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                    )}
                  </Grid>
                </Paper>
              </Grid>
            )}
          </Grid>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button 
              type="submit" 
              variant="contained" 
              disabled={isSubmitting}
              sx={{ minWidth: '120px' }}
            >
              {isSubmitting ? 'Scheduling...' : 'Schedule'}
            </Button>
          </Box>
        </Box>
      </CardContent>

      <Snackbar open={toast.open} autoHideDuration={6000} onClose={handleCloseToast}>
        <Alert onClose={handleCloseToast} severity={toast.severity} sx={{ width: '100%' }}>
          {toast.message}
        </Alert>
      </Snackbar>
    </Card>
  );
} 