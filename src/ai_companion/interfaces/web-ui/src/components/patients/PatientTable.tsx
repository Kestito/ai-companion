"use client";

import { Patient, PatientStatus } from '@/lib/supabase/types';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Paper,
  IconButton,
  Avatar,
  Box,
  Typography,
  Checkbox,
  Chip,
  Tooltip,
  TablePagination
} from '@mui/material';
import { 
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';
import { PatientStatusIndicator } from './patientstatusindicator';
import { PatientPlatformIndicator } from './patientplatformindicator';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useLogger } from '@/hooks/useLogger';

interface PatientTableProps {
  patients: Patient[];
  loading?: boolean;
}

/**
 * A table component for displaying patient information
 * Includes sorting, pagination, and action buttons
 * 
 * @param patients - Array of patient data to display
 * @param loading - Whether the data is currently loading
 */
export function PatientTable({ patients, loading = false }: PatientTableProps) {
  const router = useRouter();
  const logger = useLogger({ component: 'PatientTable' });
  
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selected, setSelected] = useState<string[]>([]);

  // Log initial mount and patient data
  useEffect(() => {
    logger.debug('PatientTable mounted', {
      totalPatients: patients.length,
      loading,
    });
  }, []);

  // Log when patient data changes
  useEffect(() => {
    logger.debug('Patient data updated', {
      totalPatients: patients.length,
      currentPage: page,
      displayedPatients: Math.min(rowsPerPage, patients.length - page * rowsPerPage),
    });
  }, [patients, page, rowsPerPage]);

  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    logger.debug('Select all patients clicked', {
      checked: event.target.checked,
      totalPatients: patients.length,
    });

    if (event.target.checked) {
      const newSelected = patients.map((p) => p.id);
      setSelected(newSelected);
      logger.info('All patients selected', { count: newSelected.length });
      return;
    }
    setSelected([]);
    logger.info('All patients deselected');
  };

  const handleClick = (event: React.MouseEvent<unknown>, id: string) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected: string[] = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
      logger.debug('Patient selected', { patientId: id });
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
      logger.debug('First patient deselected', { patientId: id });
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
      logger.debug('Last patient deselected', { patientId: id });
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1),
      );
      logger.debug('Patient deselected', { patientId: id, index: selectedIndex });
    }

    logger.info('Selection updated', {
      previousCount: selected.length,
      newCount: newSelected.length,
    });
    setSelected(newSelected);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    logger.info('Page changed', {
      previousPage: page,
      newPage,
      rowsPerPage,
    });
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newRowsPerPage = parseInt(event.target.value, 10);
    logger.info('Rows per page changed', {
      previousRowsPerPage: rowsPerPage,
      newRowsPerPage,
    });
    setRowsPerPage(newRowsPerPage);
    setPage(0);
  };

  const handlePatientView = (patientId: string) => {
    logger.info('Viewing patient details', { patientId });
    router.push(`/patients/${patientId}`);
  };

  const handlePatientEdit = (patientId: string) => {
    logger.info('Editing patient', { patientId });
    router.push(`/patients/${patientId}/edit`);
  };

  const isSelected = (id: string) => selected.indexOf(id) !== -1;

  // Pagination
  const displayedPatients = patients.slice(
    page * rowsPerPage, 
    page * rowsPerPage + rowsPerPage
  );

  // Add a helper function to determine platform from phone number if platform is not explicitly set
  const getPlatformFromPhone = (phone?: string): string => {
    if (!phone) return 'unknown';
    
    // Check if the phone number contains any platform identifiers
    if (phone.includes('telegram')) return 'telegram';
    if (phone.includes('whatsapp')) return 'whatsapp';
    
    // If the phone number starts with a specific format, it might be a WhatsApp number
    if (phone.startsWith('+')) return 'phone';
    
    return 'unknown';
  };

  if (loading) {
    logger.debug('Rendering loading state');
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Loading patients...</Typography>
      </Box>
    );
  }

  if (patients.length === 0) {
    logger.debug('Rendering empty state');
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>No patients found</Typography>
      </Box>
    );
  }

  logger.debug('Rendering patient table', {
    totalPatients: patients.length,
    displayedPatients: displayedPatients.length,
    page,
    rowsPerPage,
    selectedCount: selected.length,
  });

  return (
    <Paper sx={{ width: '100%', mb: 2, overflow: 'hidden' }}>
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader aria-label="patient table">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selected.length > 0 && selected.length < patients.length}
                  checked={patients.length > 0 && selected.length === patients.length}
                  onChange={handleSelectAllClick}
                  inputProps={{ 'aria-label': 'select all patients' }}
                />
              </TableCell>
              <TableCell>Patient</TableCell>
              <TableCell>Platform</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Doctor</TableCell>
              <TableCell>Admission Date</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {displayedPatients.map((patient) => {
              const isItemSelected = isSelected(patient.id);

              return (
                <TableRow
                  hover
                  role="checkbox"
                  aria-checked={isItemSelected}
                  tabIndex={-1}
                  key={patient.id}
                  selected={isItemSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isItemSelected}
                      onClick={(event) => handleClick(event, patient.id)}
                      inputProps={{ 'aria-labelledby': `patient-${patient.id}` }}
                    />
                  </TableCell>
                  <TableCell 
                    component="th" 
                    scope="row" 
                    onClick={() => handlePatientView(patient.id)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                        {patient.name.charAt(0)}
                      </Avatar>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {patient.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {patient.age} yrs, {patient.gender}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <PatientPlatformIndicator platform={patient.platform || getPlatformFromPhone(patient.phone)} />
                  </TableCell>
                  <TableCell>
                    <PatientStatusIndicator status={patient.status} />
                  </TableCell>
                  <TableCell>
                    {patient.doctor}
                  </TableCell>
                  <TableCell>
                    {new Date(patient.admissionDate).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex' }}>
                      <Tooltip title="View Patient">
                        <IconButton 
                          size="small" 
                          onClick={() => handlePatientView(patient.id)}
                        >
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Patient">
                        <IconButton 
                          size="small" 
                          onClick={() => handlePatientEdit(patient.id)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="More Options">
                        <IconButton 
                          size="small"
                          onClick={() => {
                            logger.debug('More options clicked', { patientId: patient.id });
                          }}
                        >
                          <MoreVertIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={patients.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
} 