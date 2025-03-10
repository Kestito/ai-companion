"use client";

import { useState, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Button, 
  Grid, 
  IconButton, 
  Chip,
  SelectChangeEvent
} from '@mui/material';
import { PatientStatus } from '@/lib/supabase/types';
import { Search as SearchIcon, Clear as ClearIcon } from '@mui/icons-material';
import { useLogger } from '@/hooks/useLogger';

interface FilterOptions {
  search: string;
  status: PatientStatus | '';
  doctor: string;
  dateAdmitted: string;
}

interface PatientFilterProps {
  onFilterChange: (filters: FilterOptions) => void;
  doctors: string[];
}

/**
 * Filter component for patients list
 * Allows filtering by name, status, doctor, and admission date
 */
export function PatientFilter({ onFilterChange, doctors }: PatientFilterProps) {
  const logger = useLogger({ component: 'PatientFilter' });

  const [filters, setFilters] = useState<FilterOptions>({
    search: '',
    status: '',
    doctor: '',
    dateAdmitted: '',
  });

  const [activeFilters, setActiveFilters] = useState<string[]>([]);

  // Log initial mount
  useEffect(() => {
    logger.debug('PatientFilter mounted', {
      availableDoctors: doctors.length,
    });
  }, []);

  // Log when filters change
  useEffect(() => {
    if (Object.values(filters).some(value => value !== '')) {
      logger.debug('Filters updated', {
        filters,
        activeFilterCount: activeFilters.length,
      });
    }
  }, [filters, activeFilters]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const searchValue = e.target.value;
    logger.debug('Search input changed', { searchValue });
    
    const newFilters = { ...filters, search: searchValue };
    setFilters(newFilters);
  };

  const handleStatusChange = (e: SelectChangeEvent<string>) => {
    const status = e.target.value as PatientStatus | '';
    logger.debug('Status filter changed', { status });
    
    const newFilters = { ...filters, status };
    setFilters(newFilters);

    // Track active filters for the filter chips
    if (status) {
      if (!activeFilters.includes('status')) {
        logger.debug('Adding status to active filters');
        setActiveFilters([...activeFilters, 'status']);
      }
    } else {
      logger.debug('Removing status from active filters');
      setActiveFilters(activeFilters.filter(f => f !== 'status'));
    }
  };

  const handleDoctorChange = (e: SelectChangeEvent<string>) => {
    const doctor = e.target.value;
    logger.debug('Doctor filter changed', { doctor });
    
    const newFilters = { ...filters, doctor };
    setFilters(newFilters);

    // Track active filters for the filter chips
    if (doctor) {
      if (!activeFilters.includes('doctor')) {
        logger.debug('Adding doctor to active filters');
        setActiveFilters([...activeFilters, 'doctor']);
      }
    } else {
      logger.debug('Removing doctor from active filters');
      setActiveFilters(activeFilters.filter(f => f !== 'doctor'));
    }
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value;
    logger.debug('Date filter changed', { date });
    
    const newFilters = { ...filters, dateAdmitted: date };
    setFilters(newFilters);

    // Track active filters for the filter chips
    if (date) {
      if (!activeFilters.includes('dateAdmitted')) {
        logger.debug('Adding admission date to active filters');
        setActiveFilters([...activeFilters, 'dateAdmitted']);
      }
    } else {
      logger.debug('Removing admission date from active filters');
      setActiveFilters(activeFilters.filter(f => f !== 'dateAdmitted'));
    }
  };

  const applyFilters = () => {
    logger.info('Applying filters', {
      filters,
      activeFilterCount: activeFilters.length,
    });
    onFilterChange(filters);
  };

  const clearFilters = () => {
    logger.info('Clearing all filters');
    
    const resetFilters: FilterOptions = {
      search: '',
      status: '',
      doctor: '',
      dateAdmitted: '',
    };
    setFilters(resetFilters);
    setActiveFilters([]);
    onFilterChange(resetFilters);
  };

  const removeFilter = (filterName: string) => {
    logger.debug('Removing specific filter', { filterName });
    
    const newFilters = { ...filters, [filterName]: '' };
    setFilters(newFilters);
    setActiveFilters(activeFilters.filter(f => f !== filterName));
    onFilterChange(newFilters);
  };

  // Helper function to get readable name for filter
  const getFilterDisplayName = (filterName: string) => {
    switch (filterName) {
      case 'status':
        return `Status: ${filters.status}`;
      case 'doctor':
        return `Doctor: ${filters.doctor}`;
      case 'dateAdmitted':
        return `Admitted: ${filters.dateAdmitted}`;
      default:
        return filterName;
    }
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={3}>
          <TextField
            fullWidth
            label="Search Patients"
            variant="outlined"
            size="small"
            value={filters.search}
            onChange={handleSearchChange}
            placeholder="Search by name, ID..."
            InputProps={{
              endAdornment: (
                <IconButton
                  size="small"
                  onClick={() => {
                    logger.debug('Clearing search input');
                    setFilters({ ...filters, search: '' });
                  }}
                  sx={{ visibility: filters.search ? 'visible' : 'hidden' }}
                >
                  <ClearIcon fontSize="small" />
                </IconButton>
              ),
            }}
          />
        </Grid>
        <Grid item xs={12} sm={3}>
          <FormControl fullWidth size="small">
            <InputLabel id="status-select-label">Status</InputLabel>
            <Select
              labelId="status-select-label"
              id="status-select"
              value={filters.status}
              label="Status"
              onChange={handleStatusChange}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="stable">Stable</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="moderate">Moderate</MenuItem>
              <MenuItem value="recovering">Recovering</MenuItem>
              <MenuItem value="discharged">Discharged</MenuItem>
              <MenuItem value="scheduled">Scheduled</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={3}>
          <FormControl fullWidth size="small">
            <InputLabel id="doctor-select-label">Doctor</InputLabel>
            <Select
              labelId="doctor-select-label"
              id="doctor-select"
              value={filters.doctor}
              label="Doctor"
              onChange={handleDoctorChange}
            >
              <MenuItem value="">All Doctors</MenuItem>
              {doctors.map((doctor) => (
                <MenuItem key={doctor} value={doctor}>
                  {doctor}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={3}>
          <TextField
            fullWidth
            label="Admission Date"
            type="date"
            size="small"
            value={filters.dateAdmitted}
            onChange={handleDateChange}
            InputLabelProps={{
              shrink: true,
            }}
          />
        </Grid>
      </Grid>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {activeFilters.map((filter) => (
            <Chip
              key={filter}
              label={getFilterDisplayName(filter)}
              onDelete={() => removeFilter(filter)}
              size="small"
              color="primary"
              variant="outlined"
            />
          ))}
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button 
            variant="outlined" 
            size="small" 
            onClick={clearFilters}
            disabled={activeFilters.length === 0 && !filters.search}
          >
            Clear
          </Button>
          <Button 
            variant="contained" 
            size="small" 
            startIcon={<SearchIcon />} 
            onClick={applyFilters}
          >
            Apply Filters
          </Button>
        </Box>
      </Box>
    </Box>
  );
} 