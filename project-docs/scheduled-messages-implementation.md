# Scheduled Messages - Implementation Guide

## Overview
This document provides a detailed implementation plan for enhancing the Scheduled Messages UI. Rather than directly modifying the existing code and potentially introducing errors, this outlines the specific components and changes needed for implementation.

## Database Schema
The implementation will use the existing `scheduled_messages` table:
```sql
TABLE scheduled_messages (
  id uuid PRIMARY KEY,
  patient_id uuid REFERENCES patients(id),
  scheduled_time timestamptz NOT NULL,
  message_content text NOT NULL,
  status text NOT NULL,
  platform text NOT NULL,
  created_at timestamptz NOT NULL,
  attempts integer NOT NULL,
  last_attempt_time timestamptz,
  priority integer NOT NULL,
  metadata jsonb,
  delivery_window_seconds integer
)
```

## Components to Implement

### 1. Enhanced Filter Component
```tsx
// 1. Import necessary components
import {
  Box, Paper, OutlinedInput, InputAdornment, Button, Badge,
  FormControl, InputLabel, Select, MenuItem, Grid
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { FilterList as FilterIcon, Search as SearchIcon, Refresh as RefreshIcon } from '@mui/icons-material';

// 2. Add filter state
const [searchQuery, setSearchQuery] = useState('');
const [filterOptions, setFilterOptions] = useState<FilterOptions>({
  status: null,
  platform: null,
  patient: patientId || null,
  dateRange: {
    start: null,
    end: null
  }
});
const [showFilters, setShowFilters] = useState(false);

// 3. Implement filter component
<Paper className="mb-6 p-4">
  <Box className="flex flex-col md:flex-row gap-4">
    <OutlinedInput
      placeholder="Search messages or patients..."
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
      fullWidth
      startAdornment={
        <InputAdornment position="start">
          <SearchIcon className="text-gray-400" />
        </InputAdornment>
      }
      className="rounded-md"
    />
    <Box className="flex shrink-0 gap-2">
      <Button 
        variant="outlined"
        startIcon={<FilterIcon />}
        onClick={() => setShowFilters(!showFilters)}
        className="text-gray-700 border-gray-300"
      >
        Filters
        {(filterOptions.status || filterOptions.platform || filterOptions.patient || 
        filterOptions.dateRange.start || filterOptions.dateRange.end) && (
          <Badge color="primary" variant="dot" className="ml-2" />
        )}
      </Button>
      <Button 
        variant="outlined"
        startIcon={<RefreshIcon />}
        onClick={loadSchedules}
        disabled={isLoading}
        className="text-gray-700 border-gray-300"
      >
        Refresh
      </Button>
    </Box>
  </Box>
  
  {/* Expanded Filters */}
  {showFilters && (
    <Box className="mt-4 pt-4 border-t border-gray-200">
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Status</InputLabel>
            <Select
              value={filterOptions.status || ''}
              onChange={(e) => setFilterOptions({
                ...filterOptions,
                status: e.target.value as string || null
              })}
              label="Status"
            >
              <MenuItem value="">All Statuses</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="sent">Sent</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Platform</InputLabel>
            <Select
              value={filterOptions.platform || ''}
              onChange={(e) => setFilterOptions({
                ...filterOptions,
                platform: e.target.value as string || null
              })}
              label="Platform"
            >
              <MenuItem value="">All Platforms</MenuItem>
              {PLATFORM_OPTIONS.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="From Date"
              value={filterOptions.dateRange.start}
              onChange={(date) => setFilterOptions({
                ...filterOptions,
                dateRange: {
                  ...filterOptions.dateRange,
                  start: date
                }
              })}
              slotProps={{ textField: { fullWidth: true, size: 'small' } }}
            />
          </LocalizationProvider>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="To Date"
              value={filterOptions.dateRange.end}
              onChange={(date) => setFilterOptions({
                ...filterOptions,
                dateRange: {
                  ...filterOptions.dateRange,
                  end: date
                }
              })}
              slotProps={{ textField: { fullWidth: true, size: 'small' } }}
            />
          </LocalizationProvider>
        </Grid>
        
        <Grid item xs={12}>
          <Box className="flex justify-end gap-2">
            <Button 
              variant="outlined"
              size="small"
              onClick={() => setFilterOptions({
                status: null,
                platform: null,
                patient: null,
                dateRange: {
                  start: null,
                  end: null
                }
              })}
              className="text-gray-700 border-gray-300"
            >
              Clear All
            </Button>
            <Button 
              variant="contained"
              size="small"
              onClick={() => {
                setShowFilters(false);
                loadSchedules();
              }}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Apply Filters
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )}
</Paper>
```

### 2. Enhanced Form for Creating Messages
```tsx
// Step-based form implementation
const steps = ['Select Patient', 'Message Content', 'Schedule Options', 'Review'];

<Dialog open={openNewDialog} onClose={closeDialog} maxWidth="md" fullWidth>
  <DialogTitle>
    New Scheduled Message
    <IconButton
      edge="end"
      color="inherit"
      onClick={closeDialog}
      aria-label="close"
      sx={{ position: 'absolute', right: 8, top: 8 }}
    >
      <CloseIcon />
    </IconButton>
  </DialogTitle>
  <DialogContent>
    <Stepper activeStep={activeStep} alternativeLabel className="mb-6 mt-2">
      {steps.map((label) => (
        <Step key={label}>
          <StepLabel>{label}</StepLabel>
        </Step>
      ))}
    </Stepper>
    
    {/* Step content */}
    {activeStep === 0 && (
      <Box>
        <Typography variant="h6" className="mb-4">
          Select Patient
        </Typography>
        
        <Autocomplete
          options={patients}
          loading={loadingPatients}
          value={selectedPatient}
          onChange={(e, newValue: Patient | null) => {
            setSelectedPatient(newValue);
            // Validation and platform selection logic
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Patient"
              required
              fullWidth
              InputProps={{
                ...params.InputProps,
                endAdornment: (
                  <>
                    {loadingPatients ? <CircularProgress size={20} /> : null}
                    {params.InputProps.endAdornment}
                  </>
                ),
              }}
            />
          )}
        />
        
        {/* Platform selection */}
        <Box className="mt-4">
          <Typography variant="subtitle1" className="mb-2">
            Communication Channel
          </Typography>
          <Grid container spacing={2}>
            {PLATFORM_OPTIONS.map(option => {
              const isAvailable = selectedPatient && 
                (option.value === 'telegram' ? !!selectedPatient.telegram_id : 
                 option.value === 'email' ? !!selectedPatient.email :
                 option.value === 'sms' ? !!selectedPatient.phone : false);
              
              return (
                <Grid item xs={4} key={option.value}>
                  <Paper 
                    className={`p-3 text-center cursor-pointer transition-all
                      ${selectedPlatform === option.value 
                        ? 'border-2 border-blue-500 bg-blue-50' 
                        : 'border border-gray-200'
                      }
                      ${!isAvailable && 'opacity-50'}
                    `}
                    onClick={() => isAvailable && setSelectedPlatform(option.value)}
                  >
                    {option.value === 'telegram' && <MessageIcon className="mb-1" />}
                    {option.value === 'email' && <MailIcon className="mb-1" />}
                    {option.value === 'sms' && <SmsIcon className="mb-1" />}
                    <Typography>{option.label}</Typography>
                    {!isAvailable && (
                      <Typography variant="caption" className="text-red-500">
                        Not available
                      </Typography>
                    )}
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      </Box>
    )}
    
    {/* Continue with other steps... */}
  </DialogContent>
  <DialogActions>
    <Button
      onClick={closeDialog}
      variant="outlined"
      className="mr-2"
    >
      Cancel
    </Button>
    
    {activeStep > 0 && (
      <Button
        onClick={() => setActiveStep(prev => prev - 1)}
        variant="outlined"
      >
        Back
      </Button>
    )}
    
    <Button
      onClick={() => {
        if (activeStep === steps.length - 1) {
          handleCreateSchedule();
        } else {
          setActiveStep(prev => prev + 1);
        }
      }}
      variant="contained"
      className="bg-blue-600 hover:bg-blue-700"
      disabled={
        (activeStep === 0 && (!selectedPatient || !selectedPlatform)) ||
        (activeStep === 1 && !messageContent) ||
        (activeStep === 2 && !selectedDate)
      }
    >
      {activeStep === steps.length - 1 ? 'Schedule Message' : 'Next'}
    </Button>
  </DialogActions>
</Dialog>
```

### 3. Enhanced Messages Table Component
```tsx
<Table>
  <TableHead>
    <TableRow>
      <TableCell>Patient</TableCell>
      <TableCell>Scheduled Time</TableCell>
      <TableCell>Message</TableCell>
      <TableCell>Platform</TableCell>
      <TableCell>Recurrence</TableCell>
      <TableCell>Status</TableCell>
      <TableCell align="right">Actions</TableCell>
    </TableRow>
  </TableHead>
  <TableBody>
    {filteredSchedules.map((schedule) => (
      <TableRow 
        key={schedule.id}
        className={`
          ${schedule.status === 'pending' ? 'bg-blue-50' : ''}
          ${schedule.status === 'sent' ? 'bg-green-50' : ''}
          ${schedule.status === 'failed' ? 'bg-red-50' : ''}
          ${schedule.status === 'cancelled' ? 'bg-gray-50' : ''}
        `}
      >
        <TableCell>
          <Box className="flex items-center">
            <PersonIcon className="mr-2 text-gray-400" fontSize="small" />
            <Box>
              <Typography variant="body2">
                {patientInfo[schedule.patient_id] || 'Unknown Patient'}
              </Typography>
              {/* Add patient contact info for the selected platform */}
              {schedule.platform === 'telegram' && (
                <Typography variant="caption" className="text-gray-500">
                  {patients.find(p => p.id === schedule.patient_id)?.telegram_id || 'No Telegram ID'}
                </Typography>
              )}
            </Box>
          </Box>
        </TableCell>
        <TableCell>
          <Box className="flex items-center">
            <CalendarToday className="mr-2 text-gray-400" fontSize="small" />
            <Box>
              <Typography variant="body2">
                {safeFormatDate(schedule.scheduled_time, 'MMM d, yyyy')}
              </Typography>
              <Typography variant="caption" className="text-gray-500">
                {safeFormatDate(schedule.scheduled_time, 'h:mm a')}
              </Typography>
            </Box>
          </Box>
        </TableCell>
        <TableCell 
          className="max-w-xs overflow-hidden text-ellipsis cursor-pointer"
          onClick={() => {
            setSelectedMessage(schedule);
            setShowDetailDialog(true);
          }}
        >
          <Tooltip title="Click to view full message">
            <Typography variant="body2" noWrap>
              {schedule.message_content}
            </Typography>
          </Tooltip>
        </TableCell>
        <TableCell>
          {schedule.platform === 'telegram' && (
            <Chip size="small" label="Telegram" className="bg-blue-100 text-blue-800" />
          )}
          {schedule.platform === 'email' && (
            <Chip size="small" label="Email" className="bg-purple-100 text-purple-800" />
          )}
          {schedule.platform === 'sms' && (
            <Chip size="small" label="SMS" className="bg-green-100 text-green-800" />
          )}
        </TableCell>
        <TableCell>
          {schedule.recurrence ? (
            <Box className="flex items-center">
              <RepeatIcon className="mr-1 text-indigo-500" fontSize="small" />
              <Typography variant="body2">
                {schedule.recurrence.type === 'daily' && 'Daily'}
                {schedule.recurrence.type === 'weekly' && 'Weekly'}
                {schedule.recurrence.type === 'monthly' && 'Monthly'}
                {schedule.recurrence.days && ` (${schedule.recurrence.days.map(d => WEEKDAYS[d].name.slice(0, 3)).join(', ')})`}
              </Typography>
            </Box>
          ) : (
            <Typography variant="body2" className="text-gray-500">One-time</Typography>
          )}
        </TableCell>
        <TableCell>{getStatusChip(schedule.status)}</TableCell>
        <TableCell align="right">
          <Box className="flex gap-1 justify-end">
            {schedule.status === 'pending' && (
              <>
                <Tooltip title="Send Now">
                  <IconButton 
                    size="small" 
                    color="primary"
                    onClick={() => handleSendNowSchedule(schedule.id)}
                    disabled={!health.isRunning}
                  >
                    <SendIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Cancel">
                  <IconButton 
                    size="small" 
                    color="error"
                    onClick={() => {
                      setSelectedMessageId(schedule.id);
                      setShowDeleteConfirm(true);
                    }}
                  >
                    <CancelIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
            {schedule.status === 'failed' && (
              <>
                <Tooltip title="Retry">
                  <IconButton 
                    size="small" 
                    color="warning"
                    onClick={() => handleRetryFailedMessage(schedule.id)}
                    disabled={!health.isRunning}
                  >
                    <RefreshIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
            {/* View details button for all statuses */}
            <Tooltip title="View Details">
              <IconButton 
                size="small" 
                onClick={() => {
                  setSelectedMessage(schedule);
                  setShowDetailDialog(true);
                }}
              >
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

## Implementation Steps

1. Add new types and constants
2. Update component state variables
3. Add the new filtered schedules function
4. Implement enhanced search and filter UI
5. Implement new form with step-by-step workflow
6. Enhance the message table display
7. Add confirmation dialogs
8. Add message details dialog

## Next Steps

Once these components are implemented, the next phases will include:
- Calendar view for scheduled messages
- Message templates functionality
- Batch operations for messages
- Recurring message management improvements 