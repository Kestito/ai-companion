import React from 'react';
import { 
  Box, 
  Card, 
  Avatar, 
  Typography, 
  Divider, 
  Chip, 
  Tooltip
} from '@mui/material';
import { 
  Person as PersonIcon,
  CalendarMonth as CalendarIcon,
  LocalHospital as MedicalIcon,
  Warning as WarningIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import { Patient, PatientStatus } from '@/lib/supabase/types';
import { PatientStatusIndicator } from '../patients/patientstatusindicator';

interface PatientInfoProps {
  patient: Patient;
  messageSource: 'telegram' | 'whatsapp' | 'web';
  lastActive?: string;
}

/**
 * Component to display patient information in chat interfaces
 * Shows relevant patient details when chatting via Telegram or WhatsApp
 * 
 * @param patient - Patient data to display
 * @param messageSource - Source of the message (telegram, whatsapp, or web)
 * @param lastActive - When the patient was last active
 */
export function PatientInfo({ patient, messageSource, lastActive }: PatientInfoProps) {
  if (!patient) return null;
  
  // Determine the source icon and color
  const getSourceIcon = () => {
    switch(messageSource) {
      case 'telegram':
        return <Chip 
          size="small" 
          label="Telegram" 
          color="primary" 
          sx={{ backgroundColor: '#0088cc', fontWeight: 'bold' }}
        />;
      case 'whatsapp':
        return <Chip 
          size="small" 
          label="WhatsApp" 
          color="primary" 
          sx={{ backgroundColor: '#25D366', fontWeight: 'bold' }}
        />;
      default:
        return <Chip 
          size="small" 
          label="Web" 
          color="default" 
        />;
    }
  };

  // Extract risk level from patient data or default to 'low'
  const riskLevel = (patient as any).risk_level || 'low';

  return (
    <Card 
      variant="outlined" 
      sx={{ 
        mb: 2, 
        borderRadius: '12px',
        borderColor: messageSource === 'telegram' ? '#0088cc' : 
                    messageSource === 'whatsapp' ? '#25D366' : 'divider',
        borderWidth: '2px',
        position: 'relative',
        overflow: 'visible'
      }}
    >
      <Box sx={{ position: 'absolute', top: -10, right: 16 }}>
        {getSourceIcon()}
      </Box>

      <Box sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
        <Avatar 
          src={(patient as any).avatar_url} 
          alt={patient.name}
          sx={{ width: 48, height: 48, mr: 2 }}
        >
          {!(patient as any).avatar_url && <PersonIcon />}
        </Avatar>
        
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" component="h3">
              {patient.name}
            </Typography>
            <PatientStatusIndicator status={patient.status} />
            
            {riskLevel === 'high' && (
              <Tooltip title="High Risk Patient">
                <WarningIcon color="error" fontSize="small" />
              </Tooltip>
            )}
          </Box>
          
          <Typography variant="body2" color="text.secondary">
            Patient ID: {patient.id.substring(0, 8)}
          </Typography>
        </Box>
      </Box>
      
      <Divider />
      
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CalendarIcon fontSize="small" color="action" />
            <Typography variant="body2">
              {lastActive ? `Last active: ${lastActive}` : `Admitted: ${new Date(patient.admissionDate).toLocaleDateString()}`}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MedicalIcon fontSize="small" color="action" />
            <Typography variant="body2">
              Risk: <span style={{ 
                fontWeight: 'bold',
                color: riskLevel === 'high' ? '#d32f2f' : 
                       riskLevel === 'medium' ? '#ed6c02' : '#2e7d32'
              }}>
                {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
              </span>
            </Typography>
          </Box>
        </Box>
        
        {patient.diagnosis && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
            <NotificationsIcon fontSize="small" color="primary" />
            <Typography variant="body2" color="primary.main">
              Diagnosis: {patient.diagnosis}
            </Typography>
          </Box>
        )}
      </Box>
    </Card>
  );
} 