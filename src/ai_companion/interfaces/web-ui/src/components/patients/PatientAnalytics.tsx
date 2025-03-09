import { Patient, PatientStatus } from '@/lib/supabase/types';
import { 
  Box, 
  Paper, 
  Grid, 
  Typography, 
  Divider
} from '@mui/material';

interface PatientAnalyticsProps {
  patients: Patient[];
}

/**
 * Component to display analytics and statistics about patients
 * 
 * @param patients - Array of patient data to analyze
 */
export function PatientAnalytics({ patients }: PatientAnalyticsProps) {
  const totalPatients = patients.length;

  // Find most common diagnosis
  const diagnosisCounts = patients.reduce((acc, patient) => {
    const diagnosis = patient.diagnosis;
    acc[diagnosis] = (acc[diagnosis] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const mostCommonDiagnosis = Object.entries(diagnosisCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  return (
    <Box sx={{ mb: 4 }}>
      {/* Common diagnoses section only */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
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