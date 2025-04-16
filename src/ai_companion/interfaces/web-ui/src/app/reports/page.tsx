'use client';

import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Box, 
  Typography, 
  Paper, 
  Container,
  Grid,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  IconButton
} from '@mui/material';
import Link from 'next/link';
import { 
  Home as HomeIcon, 
  Download as DownloadIcon,
  FileDownload as FileDownloadIcon,
  FilterList as FilterListIcon,
  Refresh as RefreshIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  TableChart as TableChartIcon,
  DateRange as DateRangeIcon
} from '@mui/icons-material';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { useLogger } from '@/hooks/useLogger';

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

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [filters, setFilters] = useState<ReportFilter>({
    dateRange: 'week',
    type: 'all',
    status: 'all'
  });
  const logger = useLogger({ component: 'ReportsPage' });
  const supabase = createClientComponentClient();

  useEffect(() => {
    fetchReports();
  }, [filters]);

  async function fetchReports() {
    try {
      setLoading(true);
      setError(null);
      logger.info('Fetching reports with filters', filters);

      // Check if the 'reports' table exists
      const { error: tableError } = await supabase
        .from('reports')
        .select('id')
        .limit(1);

      // If there's an error accessing the reports table, use sample data
      if (tableError) {
        logger.warn('Reports table not accessible, using sample data');
        const sampleReports = generateSampleReports();
        setReports(sampleReports);
        setLoading(false);
        return;
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
      } else {
        // If no data, use sample data
        logger.info('No reports found, using sample data');
        const sampleReports = generateSampleReports();
        setReports(sampleReports);
      }
    } catch (err: any) {
      logger.error('Error fetching reports', err);
      setError(err.message || 'Failed to load reports');
      // Fallback to sample data
      const sampleReports = generateSampleReports();
      setReports(sampleReports);
    } finally {
      setLoading(false);
    }
  }

  // Generate sample report data for demonstration
  function generateSampleReports(): ReportType[] {
    return [
      {
        id: 'rep-001',
        title: 'Patient Growth Summary',
        description: 'Monthly patient registration and activity metrics',
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'analytics',
        status: 'completed'
      },
      {
        id: 'rep-002',
        title: 'Message Engagement Report',
        description: 'User engagement with messaging platform',
        created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'engagement',
        status: 'completed'
      },
      {
        id: 'rep-003',
        title: 'Health Records Summary',
        description: 'Summary of patient health record activity',
        created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'records',
        status: 'completed'
      },
      {
        id: 'rep-004',
        title: 'System Usage Analytics',
        description: 'Platform usage statistics and metrics',
        created_at: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'analytics',
        status: 'completed'
      },
      {
        id: 'rep-005',
        title: 'Monthly Executive Summary',
        description: 'High-level overview for leadership team',
        created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'summary',
        status: 'pending'
      }
    ];
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
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
        return 'success.main';
      case 'pending':
        return 'warning.main';
      case 'failed':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

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
            startIcon={<BarChartIcon />}
            onClick={() => alert('Generate new report functionality would go here')}
          >
            Generate Report
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 2 }}>
          View and manage system reports and analytics.
        </Typography>
      </Box>

      <Paper sx={{ mb: 4, p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Report Filters</Typography>
          <Tooltip title="Refresh Reports">
            <IconButton onClick={handleRefresh} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Date Range</InputLabel>
              <Select
                value={filters.dateRange}
                label="Date Range"
                onChange={(e) => handleFilterChange('dateRange', e.target.value)}
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
            <FormControl fullWidth size="small">
              <InputLabel>Report Type</InputLabel>
              <Select
                value={filters.type}
                label="Report Type"
                onChange={(e) => handleFilterChange('type', e.target.value)}
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
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status}
                label="Status"
                onChange={(e) => handleFilterChange('status', e.target.value)}
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

      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab 
            icon={<TableChartIcon />} 
            iconPosition="start" 
            label="Reports List" 
          />
          <Tab 
            icon={<BarChartIcon />} 
            iconPosition="start" 
            label="Charts" 
          />
          <Tab 
            icon={<PieChartIcon />} 
            iconPosition="start" 
            label="Summary" 
          />
        </Tabs>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {error && (
              <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
            )}

            {activeTab === 0 && (
              <TableContainer sx={{ maxHeight: 440 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Title</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reports.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          No reports found matching your filters
                        </TableCell>
                      </TableRow>
                    ) : (
                      reports
                        .filter(report => {
                          // Apply filters
                          if (filters.type !== 'all' && report.type !== filters.type) {
                            return false;
                          }
                          if (filters.status !== 'all' && report.status !== filters.status) {
                            return false;
                          }
                          return true;
                        })
                        .map((report) => (
                          <TableRow hover key={report.id}>
                            <TableCell sx={{ fontWeight: 'medium' }}>{report.title}</TableCell>
                            <TableCell>{report.description}</TableCell>
                            <TableCell sx={{ textTransform: 'capitalize' }}>{report.type}</TableCell>
                            <TableCell>{new Date(report.created_at).toLocaleDateString()}</TableCell>
                            <TableCell>
                              <Box 
                                component="span" 
                                sx={{ 
                                  p: 0.75, 
                                  borderRadius: 1,
                                  fontSize: '0.75rem',
                                  fontWeight: 'bold',
                                  textTransform: 'uppercase',
                                  backgroundColor: `${getReportStatusColor(report.status)}20`,
                                  color: getReportStatusColor(report.status)
                                }}
                              >
                                {report.status}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Tooltip title="Download Report">
                                <IconButton 
                                  size="small" 
                                  color="primary"
                                  onClick={() => alert(`Download ${report.title}`)}
                                >
                                  <FileDownloadIcon />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            {activeTab === 1 && (
              <Box p={4} textAlign="center">
                <Typography variant="h6" mb={2}>Charts View</Typography>
                <Typography color="text.secondary">
                  Report visualization charts would be displayed here.
                </Typography>
              </Box>
            )}

            {activeTab === 2 && (
              <Box p={4} textAlign="center">
                <Typography variant="h6" mb={2}>Summary View</Typography>
                <Typography color="text.secondary">
                  Executive summary and key metrics would be displayed here.
                </Typography>
              </Box>
            )}
          </>
        )}
      </Paper>
    </Container>
  );
} 