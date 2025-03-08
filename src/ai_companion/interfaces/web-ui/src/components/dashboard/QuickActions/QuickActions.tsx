import { Button, Stack, Typography, Paper } from '@mui/material'
import AddIcon from '@mui/icons-material/PersonAdd'
import MessageIcon from '@mui/icons-material/Message'
import ReportIcon from '@mui/icons-material/Assessment'

export const QuickActions = () => (
  <Paper sx={{ p: 2, height: '100%' }}>
    <Typography variant="h6" gutterBottom>
      Quick Actions
    </Typography>
    <Stack spacing={1}>
      <Button
        variant="contained"
        startIcon={<MessageIcon />}
        fullWidth
        sx={{ justifyContent: 'flex-start' }}
      >
        New Message
      </Button>
      <Button
        variant="contained"
        startIcon={<AddIcon />}
        fullWidth
        sx={{ justifyContent: 'flex-start' }}
      >
        Add Patient
      </Button>
      <Button
        variant="contained"
        startIcon={<ReportIcon />}
        fullWidth
        sx={{ justifyContent: 'flex-start' }}
      >
        Generate Report
      </Button>
    </Stack>
  </Paper>
)