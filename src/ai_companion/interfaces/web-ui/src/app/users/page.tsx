'use client';

import { 
  Box, 
  Container, 
  Paper, 
  Typography, 
  Button, 
  TextField, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  IconButton,
  Chip,
  Menu,
  MenuItem,
  Stack,
  Select,
  FormControl,
  InputLabel,
  SelectChangeEvent
} from '@mui/material';
import { 
  Add, 
  MoreVert, 
  Search,
  FilterList,
  ViewColumn
} from '@mui/icons-material';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

// Mock data - In real app, this would come from an API
const mockUsers = [
  { 
    id: 1,
    status: 'active',
    name: 'Jonas Petraitis',
    type: 'Patient',
    lastActive: 'Just now',
    risk: 'Medium'
  },
  { 
    id: 2,
    status: 'active',
    name: 'Marija Kazlauskienė',
    type: 'Patient',
    lastActive: '5 min ago',
    risk: 'Low'
  },
  { 
    id: 3,
    status: 'inactive',
    name: 'Tomas Butkus',
    type: 'Patient',
    lastActive: 'Yesterday',
    risk: 'High'
  },
  { 
    id: 4,
    status: 'active',
    name: 'Dr. A. Vaitiekūnas',
    type: 'Doctor',
    lastActive: '1 hour ago',
    risk: '-'
  }
];

const StatusIndicator = ({ status }: { status: string }) => (
  <Box
    sx={{
      width: 8,
      height: 8,
      borderRadius: '50%',
      bgcolor: status === 'active' ? 'success.main' : 'text.disabled',
      display: 'inline-block',
      mr: 1
    }}
  />
);

const RiskChip = ({ risk }: { risk: string }) => {
  const getColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  return risk === '-' ? (
    <Typography variant="body2">-</Typography>
  ) : (
    <Chip 
      label={risk} 
      color={getColor(risk)} 
      size="small" 
      variant="outlined"
    />
  );
};

export default function UsersPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterAnchor, setFilterAnchor] = useState<null | HTMLElement>(null);
  const [columnAnchor, setColumnAnchor] = useState<null | HTMLElement>(null);
  const [selectedType, setSelectedType] = useState('all');

  const handleTypeChange = (event: SelectChangeEvent) => {
    setSelectedType(event.target.value);
  };

  const handleUserClick = (userId: number) => {
    router.push(`/users/${userId}`);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Users</Typography>
        <Button startIcon={<Add />} variant="contained">
          New User
        </Button>
      </Box>

      <Paper elevation={0} sx={{ p: 2, mb: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            placeholder="Search users..."
            variant="outlined"
            size="small"
            fullWidth
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <Search sx={{ color: 'text.secondary', mr: 1 }} />,
            }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={selectedType}
              label="Type"
              onChange={handleTypeChange}
            >
              <MenuItem value="all">All Types</MenuItem>
              <MenuItem value="patient">Patient</MenuItem>
              <MenuItem value="doctor">Doctor</MenuItem>
            </Select>
          </FormControl>
          <IconButton onClick={(e) => setFilterAnchor(e.currentTarget)}>
            <FilterList />
          </IconButton>
          <IconButton onClick={(e) => setColumnAnchor(e.currentTarget)}>
            <ViewColumn />
          </IconButton>
        </Stack>
      </Paper>

      <TableContainer component={Paper} elevation={0} sx={{ borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Last Active</TableCell>
              <TableCell>Risk</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mockUsers.map((user) => (
              <TableRow 
                key={user.id}
                hover
                onClick={() => handleUserClick(user.id)}
                sx={{ cursor: 'pointer' }}
              >
                <TableCell>
                  <StatusIndicator status={user.status} />
                </TableCell>
                <TableCell>{user.name}</TableCell>
                <TableCell>{user.type}</TableCell>
                <TableCell>{user.lastActive}</TableCell>
                <TableCell>
                  <RiskChip risk={user.risk} />
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={(e) => e.stopPropagation()}>
                    <MoreVert />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Typography variant="body2" color="text.secondary">
          Showing {mockUsers.length} of 148 users
        </Typography>
      </Box>

      <Menu
        anchorEl={filterAnchor}
        open={Boolean(filterAnchor)}
        onClose={() => setFilterAnchor(null)}
      >
        <MenuItem>Active Users</MenuItem>
        <MenuItem>Inactive Users</MenuItem>
        <MenuItem>High Risk</MenuItem>
        <MenuItem>Recent Activity</MenuItem>
      </Menu>

      <Menu
        anchorEl={columnAnchor}
        open={Boolean(columnAnchor)}
        onClose={() => setColumnAnchor(null)}
      >
        <MenuItem>Status</MenuItem>
        <MenuItem>Name</MenuItem>
        <MenuItem>Type</MenuItem>
        <MenuItem>Last Active</MenuItem>
        <MenuItem>Risk</MenuItem>
      </Menu>
    </Container>
  );
} 