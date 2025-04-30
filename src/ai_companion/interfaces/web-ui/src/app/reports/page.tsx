'use client';

import React, { useState, useEffect } from 'react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { useLogger } from '@/hooks/useLogger';
import { getSupabaseCredentials } from '@/lib/supabase/client';
import { FORCE_REAL_DATA, USE_MOCK_DATA } from '@/lib/config';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Container,
  Grid,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Link as MuiLink,
  Stack
} from '@mui/material';
import {
  Refresh,
  Download,
  Add,
  Home as HomeIcon,
  TableChart,
  PieChart,
  Assessment,
  MoreVert
} from '@mui/icons-material';
import Link from 'next/link';

// Types
interface ReportType {
  id: string;
  title: string;
  description: string;
  created_at: string;
  type: string;
  status: string;
}

interface ReportFilter {
  dateRange: string;
  type: string;
  status: string;
}

interface ActivityItem {
  id: string;
  time: string;
  user: string;
  action: string;
  severity: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
}

// Activity Card Component
const ActivityCard = ({ title, items }: { title: string; items: ActivityItem[] }) => (
  <Paper
    sx={{
      p: 3,
      height: '100%',
      bgcolor: 'background.paper',
      borderRadius: 1,
      mb: 3
    }}
  >
    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
      <Typography variant="h6">{title}</Typography>
      <IconButton size="small">
        <MoreVert />
      </IconButton>
    </Box>
    <Stack spacing={2}>
      {items.length > 0 ? (
        items.map((item) => (
          <Box 
            key={item.id} 
            sx={{ 
              display: 'flex', 
              alignItems: 'flex-start', 
              gap: 2,
              p: 1.5,
              borderRadius: 1,
              bgcolor: 'background.default',
              '&:hover': {
                bgcolor: 'action.hover',
              },
              borderBottom: '1px solid',
              borderColor: 'divider',
              '&:last-child': {
                borderBottom: 'none'
              }
            }}
          >
            <Box 
              sx={{ 
                width: 8, 
                height: 8, 
                borderRadius: '50%', 
                bgcolor: `${item.severity}.main`,
                flexShrink: 0,
                mt: 1
              }} 
            />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                {item.time}
              </Typography>
              <Typography variant="body1">
                <Box component="span" fontWeight="fontWeightMedium">{item.user}</Box> • {item.action}
              </Typography>
            </Box>
          </Box>
        ))
      ) : (
        <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
          <Typography variant="body2">No recent activity found</Typography>
        </Box>
      )}
    </Stack>
  </Paper>
);

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [filters, setFilters] = useState<ReportFilter>({
    dateRange: 'week',
    type: 'all',
    status: 'all'
  });
  const logger = useLogger({ component: 'ReportsPage' });
  
  // Generate sample report data for demonstration
  function generateSampleReports(): ReportType[] {
    return [
      {
        id: 'rep-001',
        title: 'Patient Activity Report',
        description: 'Comprehensive analysis of patient engagement and activities',
        created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'analytics',
        status: 'completed'
      },
      {
        id: 'rep-002',
        title: 'Patient Growth Summary',
        description: 'Monthly patient registration and activity metrics',
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'analytics',
        status: 'completed'
      },
      {
        id: 'rep-003',
        title: 'Message Engagement Report',
        description: 'User engagement with messaging platform',
        created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'engagement',
        status: 'completed'
      },
      {
        id: 'rep-004',
        title: 'Health Records Summary',
        description: 'Summary of patient health record activity',
        created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'records',
        status: 'completed'
      },
      {
        id: 'rep-005',
        title: 'System Usage Analytics',
        description: 'Platform usage statistics and metrics',
        created_at: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'analytics',
        status: 'completed'
      },
      {
        id: 'rep-006',
        title: 'Monthly Executive Summary',
        description: 'High-level overview for leadership team',
        created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'summary',
        status: 'pending'
      }
    ];
  }

  // Generate sample activity data
  function generateSampleActivity(): ActivityItem[] {
    return [
      {
        id: 'act-001',
        time: formatDate(new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()) + ' ' + new Date(Date.now() - 2 * 60 * 60 * 1000).toLocaleTimeString(),
        user: 'System',
        action: 'Generated Patient Activity Report',
        severity: 'success'
      },
      {
        id: 'act-002',
        time: formatDate(new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString()) + ' ' + new Date(Date.now() - 5 * 60 * 60 * 1000).toLocaleTimeString(),
        user: 'Admin',
        action: 'Approved Monthly Executive Summary',
        severity: 'primary'
      },
      {
        id: 'act-003',
        time: formatDate(new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString()) + ' ' + new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toLocaleTimeString(),
        user: 'System',
        action: 'Failed to generate Health Records Summary',
        severity: 'error'
      },
      {
        id: 'act-004',
        time: formatDate(new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()) + ' ' + new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toLocaleTimeString(),
        user: 'User',
        action: 'Scheduled System Usage Analytics report',
        severity: 'info'
      },
      {
        id: 'act-005',
        time: formatDate(new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()) + ' ' + new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toLocaleTimeString(),
        user: 'Admin',
        action: 'Updated reporting parameters',
        severity: 'warning'
      }
    ];
  }

  useEffect(() => {
    // Immediately set mock data to prevent UI flashing
    setReports(generateSampleReports());
    setRecentActivity(generateSampleActivity());
    fetchReports();
  }, [filters]);

  async function fetchReports() {
    try {
      setLoading(true);
      
      // If we're in development mode and mock data is allowed, use sample data
      if (USE_MOCK_DATA()) {
        logger.info('Using sample data in development mode');
        const sampleData = generateSampleReports();
        setReports(sampleData);
        setLoading(false);
        return;
      }
      
      // Initialize Supabase client - for production or when real data is required
      const { supabaseUrl, supabaseKey } = getSupabaseCredentials();
      if (!supabaseUrl || !supabaseKey) {
        throw new Error('Missing Supabase credentials. Check environment variables.');
      }
      
      const supabase = createClientComponentClient({
        supabaseUrl,
        supabaseKey
      });
      
      logger.info('Fetching reports with filters', filters);

      // Try to fetch real data but handle any errors gracefully
      try {
        // Check if the 'reports' table exists
        const { error: tableError } = await supabase
          .from('reports')
          .select('id')
          .limit(1);

        // If there's an error accessing the reports table, use sample data
        if (tableError) {
          logger.warn('Reports table not accessible, using sample data', tableError);
          return;  // We already set sample data at the beginning
        }

        // Fetch actual reports
        const { data, error } = await supabase
          .from('reports')
          .select('*')
          .order('created_at', { ascending: false });

        if (error) {
          throw error;
        }

        if (data && data.length > 0) {
          setReports(data as ReportType[]);
          logger.info('Successfully loaded real data from database');
        }
        // If no data, we keep the sample data that was already set
      } catch (err) {
        logger.error('Error in database operation', err);
        if (!FORCE_REAL_DATA) {
          // Only fall back to sample data if not forcing real data
          setReports(generateSampleReports());
          logger.info('Falling back to sample data');
        } else {
          // When forcing real data, show the error
          setError('Failed to load reports. Database error occurred.');
        }
      }
    } catch (err: any) {
      logger.error('Error in report fetching process', err);
      setError(err.message || 'An unknown error occurred');
      if (!FORCE_REAL_DATA) {
        // Only fall back to sample data if not forcing real data
        setReports(generateSampleReports());
      }
    } finally {
      setLoading(false);
    }
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleRefresh = () => {
    fetchReports();
  };

  const handleFilterChange = (name: keyof ReportFilter, value: string) => {
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const getReportStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getReportTypeColor = (type: string) => {
    switch (type) {
      case 'analytics':
        return 'primary';
      case 'engagement':
        return 'secondary';
      case 'records':
        return 'info';
      case 'summary':
        return 'success';
      default:
        return 'default';
    }
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Link 
              href="/"
              style={{
                display: 'flex',
                alignItems: 'center',
                color: 'inherit',
                textDecoration: 'none',
                marginRight: '8px'
              }}
            >
              <HomeIcon sx={{ fontSize: 18, mr: 0.5 }} />
              Home
            </Link>
            <Box sx={{ mx: 1, color: 'text.secondary' }}>/</Box>
            <Typography color="text.primary">Reports</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Reports
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Link 
              href="/"
              style={{
                display: 'flex',
                alignItems: 'center',
                color: 'inherit',
                textDecoration: 'none',
                marginRight: '8px'
              }}
            >
              <HomeIcon sx={{ fontSize: 18, mr: 0.5 }} />
              Home
            </Link>
            <Box sx={{ mx: 1, color: 'text.secondary' }}>/</Box>
            <Typography color="text.primary">Reports</Typography>
          </Box>
          
          <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }}>
            Reports
          </Typography>
        </Box>
        
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold">Error loading reports</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Container>
    );
  }

  // Filter reports based on selected filters
  const filteredReports = reports.filter(report => {
    // Apply filters
    if (filters.type !== 'all' && report.type !== filters.type) {
      return false;
    }
    if (filters.status !== 'all' && report.status !== filters.status) {
      return false;
    }
    return true;
  });

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Link 
            href="/"
            style={{
              display: 'flex',
              alignItems: 'center',
              color: 'inherit',
              textDecoration: 'none',
              marginRight: '8px'
            }}
          >
            <HomeIcon sx={{ fontSize: 18, mr: 0.5 }} />
            Home
          </Link>
          <Box sx={{ mx: 1, color: 'text.secondary' }}>/</Box>
          <Typography color="text.primary">Reports</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
          <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
            Reports
          </Typography>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<Add />}
            onClick={() => alert('Generate new report functionality would go here')}
          >
            Generate Report
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4 }}>
          View and manage system reports and analytics.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">Report Filters</Typography>
              <IconButton
                onClick={handleRefresh}
                size="small"
                aria-label="Refresh reports"
              >
                <Refresh />
              </IconButton>
            </Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth variant="outlined" size="small">
                  <InputLabel id="date-range-label">Date Range</InputLabel>
                  <Select
                    labelId="date-range-label"
                    id="date-range"
                    value={filters.dateRange}
                    onChange={(e) => handleFilterChange('dateRange', e.target.value as string)}
                    label="Date Range"
                  >
                    <MenuItem value="week">Last 7 Days</MenuItem>
                    <MenuItem value="month">Last 30 Days</MenuItem>
                    <MenuItem value="quarter">Last 90 Days</MenuItem>
                    <MenuItem value="year">Last 12 Months</MenuItem>
                    <MenuItem value="all">All Time</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth variant="outlined" size="small">
                  <InputLabel id="report-type-label">Report Type</InputLabel>
                  <Select
                    labelId="report-type-label"
                    id="report-type"
                    value={filters.type}
                    onChange={(e) => handleFilterChange('type', e.target.value as string)}
                    label="Report Type"
                  >
                    <MenuItem value="all">All Types</MenuItem>
                    <MenuItem value="analytics">Analytics</MenuItem>
                    <MenuItem value="engagement">Engagement</MenuItem>
                    <MenuItem value="records">Records</MenuItem>
                    <MenuItem value="summary">Summary</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth variant="outlined" size="small">
                  <InputLabel id="status-label">Status</InputLabel>
                  <Select
                    labelId="status-label"
                    id="status"
                    value={filters.status}
                    onChange={(e) => handleFilterChange('status', e.target.value as string)}
                    label="Status"
                  >
                    <MenuItem value="all">All Statuses</MenuItem>
                    <MenuItem value="completed">Completed</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                    <MenuItem value="failed">Failed</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <ActivityCard title="Recent System Activity" items={recentActivity} />
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ overflow: 'hidden' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={activeTab} 
                onChange={handleTabChange}
                aria-label="report view tabs"
              >
                <Tab 
                  label="Reports List" 
                  icon={<TableChart />} 
                  iconPosition="start" 
                />
                <Tab 
                  label="Charts" 
                  icon={<PieChart />} 
                  iconPosition="start" 
                />
                <Tab 
                  label="Summary" 
                  icon={<Assessment />} 
                  iconPosition="start" 
                />
              </Tabs>
            </Box>

            {activeTab === 0 && (
              <TableContainer>
                <Table sx={{ minWidth: 650 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell><Typography variant="subtitle2">Title</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2">Description</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2">Type</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2">Created</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2">Status</Typography></TableCell>
                      <TableCell align="right"><Typography variant="subtitle2">Actions</Typography></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredReports.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          <Typography variant="body1" sx={{ py: 3 }}>
                            No reports found matching your filters
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredReports.map((report) => (
                        <TableRow 
                          key={report.id}
                          hover
                          sx={{ '&:hover': { cursor: 'pointer' } }}
                        >
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {report.title}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {report.description}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={report.type}
                              color={getReportTypeColor(report.type) as any}
                              size="small"
                              sx={{ textTransform: 'capitalize' }}
                            />
                          </TableCell>
                          <TableCell>{formatDate(report.created_at)}</TableCell>
                          <TableCell>
                            <Chip 
                              label={report.status}
                              color={getReportStatusColor(report.status) as any}
                              size="small"
                              sx={{ textTransform: 'uppercase' }}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <IconButton
                              size="small"
                              onClick={() => alert(`Download ${report.title}`)}
                              aria-label={`Download ${report.title}`}
                            >
                              <Download fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            {activeTab === 1 && (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>
                  Charts View
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Report visualization charts would be displayed here.
                </Typography>
              </Box>
            )}

            {activeTab === 2 && (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>
                  Summary View
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Executive summary and key metrics would be displayed here.
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
} 