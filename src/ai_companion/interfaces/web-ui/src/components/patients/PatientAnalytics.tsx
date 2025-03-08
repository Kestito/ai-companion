import { Patient, PatientStatus } from '@/lib/supabase/types';
import { 
  Box, 
  Paper, 
  Grid, 
  Typography, 
  Divider, 
  Avatar
} from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  HealthAndSafety, 
  LocalHospital,
  Warning, 
  PeopleAlt 
} from '@mui/icons-material';
import { PatientStatusIndicator } from './PatientStatusIndicator';

interface PatientAnalyticsProps {
  patients: Patient[];
}

/**
 * Component to display analytics and statistics about patients
 * 
 * @param patients - Array of patient data to analyze
 */
export function PatientAnalytics({ patients }: PatientAnalyticsProps) {
  // Calculate statistics
  const totalPatients = patients.length;
  const activePatients = patients.filter(p => 
    p.status !== 'discharged' && p.status !== 'scheduled').length;
  const criticalPatients = patients.filter(p => p.status === 'critical').length;
  const stablePatients = patients.filter(p => p.status === 'stable').length;
  const dischargedPatients = patients.filter(p => p.status === 'discharged').length;
  const scheduledPatients = patients.filter(p => p.status === 'scheduled').length;

  // Get critical patients to highlight
  const criticalPatientsList = patients
    .filter(p => p.status === 'critical')
    .slice(0, 3); // Show up to 3

  // Find most common diagnosis
  const diagnosisCounts = patients.reduce((acc, patient) => {
    const diagnosis = patient.diagnosis;
    acc[diagnosis] = (acc[diagnosis] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const mostCommonDiagnosis = Object.entries(diagnosisCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  // Analytics card component
  const StatCard = ({ 
    title, 
    value, 
    icon, 
    color 
  }: { 
    title: string; 
    value: string | number; 
    icon: React.ReactNode; 
    color: string;
  }) => (
    <Paper elevation={0} sx={{ p: 2, height: '100%', border: '1px solid', borderColor: 'divider' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Avatar sx={{ bgcolor: `${color}.light`, color: `${color}.dark`, mr: 1 }}>
          {icon}
        </Avatar>
        <Typography variant="h6" component="div">
          {value}
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary">
        {title}
      </Typography>
    </Paper>
  );

  return (
    <Box sx={{ mb: 4 }}>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard 
            title="Total Patients" 
            value={totalPatients} 
            icon={<PeopleAlt />} 
            color="primary" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard 
            title="Active Patients" 
            value={activePatients} 
            icon={<LocalHospital />} 
            color="info" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard 
            title="Critical Patients" 
            value={criticalPatients} 
            icon={<Warning />} 
            color="error" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard 
            title="Stable Patients" 
            value={stablePatients} 
            icon={<HealthAndSafety />} 
            color="primary" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard 
            title="Discharged" 
            value={dischargedPatients} 
            icon={<TrendingDown />} 
            color="secondary" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard 
            title="Scheduled" 
            value={scheduledPatients} 
            icon={<TrendingUp />} 
            color="warning" 
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Critical patients section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Critical Patients
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {criticalPatientsList.length > 0 ? (
              criticalPatientsList.map((patient) => (
                <Box key={patient.id} sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                  <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                    {patient.name.charAt(0)}
                  </Avatar>
                  <Box>
                    <Typography variant="body1" fontWeight="medium">
                      {patient.name}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                      <PatientStatusIndicator status="critical" showLabel={false} />
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                        {patient.diagnosis} • Room {patient.roomNumber || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No critical patients at this time.
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Common diagnoses section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Common Diagnoses
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {mostCommonDiagnosis.map(([diagnosis, count]) => (
              <Box key={diagnosis} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body1">{diagnosis}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {count} patient{count !== 1 ? 's' : ''}
                  </Typography>
                </Box>
                <Box 
                  sx={{ 
                    width: '100%', 
                    height: 6, 
                    bgcolor: 'grey.100', 
                    borderRadius: 1, 
                    overflow: 'hidden' 
                  }}
                >
                  <Box 
                    sx={{ 
                      width: `${(count / totalPatients) * 100}%`, 
                      height: '100%', 
                      bgcolor: 'primary.main' 
                    }} 
                  />
                </Box>
              </Box>
            ))}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
} 