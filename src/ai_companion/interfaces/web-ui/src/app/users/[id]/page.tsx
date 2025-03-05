'use client';

import { 
  Box, 
  Container, 
  Paper, 
  Typography, 
  Button, 
  Stack, 
  Tabs,
  Tab,
  Avatar,
  Chip,
  Grid,
  IconButton
} from '@mui/material';
import { 
  ArrowBack,
  Message,
  Phone,
  CalendarMonth,
  Email,
  Home,
  Warning
} from '@mui/icons-material';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

// Mock data - In real app, this would come from an API
const mockUser = {
  id: 1,
  name: 'Jonas Petraitis',
  phone: '+370 612 34567',
  email: 'jonas.petraitis@email.com',
  location: 'Vilnius, Lithuania',
  risk: 'Medium',
  photo: '/placeholder-avatar.png',
  diagnosis: 'Breast Cancer Stage II',
  treatment: 'Chemotherapy (Cycle 3/6)',
  lastAssessment: '2023-08-15',
  conversations: [
    { date: 'Yesterday, 15:42', platform: 'WhatsApp', type: 'Medication reminder' },
    { date: '2023-08-14, 10:15', platform: 'Telegram', type: 'Symptom check' },
    { date: '2023-08-12, 09:30', platform: 'WhatsApp', type: 'Appointment confirmation' }
  ],
  appointments: [
    { date: '2023-08-20, 14:00', type: 'Oncology follow-up', doctor: 'Dr. Vaitiekūnas' },
    { date: '2023-08-25, 11:30', type: 'Chemotherapy session', doctor: 'Dr. Kazlauskienė' }
  ]
};

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`user-tabpanel-${index}`}
      aria-labelledby={`user-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function UserDetailPage() {
  const router = useRouter();
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Button
        startIcon={<ArrowBack />}
        onClick={() => router.back()}
        sx={{ mb: 4 }}
      >
        Back to Users
      </Button>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: 3, 
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider'
            }}
          >
            <Box sx={{ display: 'flex', gap: 3, mb: 4 }}>
              <Avatar
                src={mockUser.photo}
                sx={{ width: 100, height: 100 }}
              />
              <Box>
                <Typography variant="h4" gutterBottom>
                  {mockUser.name}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Email fontSize="small" color="action" />
                  <Typography variant="body2">{mockUser.email}</Typography>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Phone fontSize="small" color="action" />
                  <Typography variant="body2">{mockUser.phone}</Typography>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Home fontSize="small" color="action" />
                  <Typography variant="body2">{mockUser.location}</Typography>
                </Stack>
              </Box>
              <Box sx={{ ml: 'auto' }}>
                <Chip
                  icon={<Warning />}
                  label={`${mockUser.risk} Risk`}
                  color="warning"
                  variant="outlined"
                />
              </Box>
            </Box>

            <Stack direction="row" spacing={2}>
              <Button startIcon={<Message />} variant="contained">
                Message
              </Button>
              <Button startIcon={<Phone />} variant="outlined">
                Call
              </Button>
              <Button startIcon={<CalendarMonth />} variant="outlined">
                Schedule
              </Button>
            </Stack>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 4 }}>
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="Overview" />
                <Tab label="Medical" />
                <Tab label="Conversations" />
                <Tab label="Risk Factors" />
                <Tab label="Appointments" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <Typography variant="h6" gutterBottom>
                Health Summary
              </Typography>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Diagnosis
                  </Typography>
                  <Typography>{mockUser.diagnosis}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Treatment
                  </Typography>
                  <Typography>{mockUser.treatment}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Last Assessment
                  </Typography>
                  <Typography>{mockUser.lastAssessment}</Typography>
                </Box>
              </Stack>
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Typography variant="h6" gutterBottom>
                Recent Conversations
              </Typography>
              <Stack spacing={2}>
                {mockUser.conversations.map((conv, index) => (
                  <Paper
                    key={index}
                    variant="outlined"
                    sx={{ p: 2, borderRadius: 2 }}
                  >
                    <Typography variant="subtitle2" color="text.secondary">
                      {conv.date}
                    </Typography>
                    <Typography>
                      {conv.type} ({conv.platform})
                    </Typography>
                  </Paper>
                ))}
              </Stack>
            </TabPanel>

            <TabPanel value={tabValue} index={4}>
              <Typography variant="h6" gutterBottom>
                Upcoming Appointments
              </Typography>
              <Stack spacing={2}>
                {mockUser.appointments.map((apt, index) => (
                  <Paper
                    key={index}
                    variant="outlined"
                    sx={{ p: 2, borderRadius: 2 }}
                  >
                    <Typography variant="subtitle2" color="text.secondary">
                      {apt.date}
                    </Typography>
                    <Typography>
                      {apt.type} with {apt.doctor}
                    </Typography>
                  </Paper>
                ))}
              </Stack>
            </TabPanel>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Stack spacing={3}>
            <Paper
              elevation={0}
              sx={{
                p: 3,
                borderRadius: 4,
                border: '1px solid',
                borderColor: 'divider'
              }}
            >
              <Typography variant="h6" gutterBottom>
                Quick Stats
              </Typography>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Last Active
                  </Typography>
                  <Typography>2 hours ago</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Messages This Week
                  </Typography>
                  <Typography>12</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Next Appointment
                  </Typography>
                  <Typography>Aug 20, 2023</Typography>
                </Box>
              </Stack>
            </Paper>

            <Paper
              elevation={0}
              sx={{
                p: 3,
                borderRadius: 4,
                border: '1px solid',
                borderColor: 'divider'
              }}
            >
              <Typography variant="h6" gutterBottom>
                Notes
              </Typography>
              <Typography variant="body2" color="text.secondary">
                No notes added yet.
              </Typography>
            </Paper>
          </Stack>
        </Grid>
      </Grid>
    </Container>
  );
} 