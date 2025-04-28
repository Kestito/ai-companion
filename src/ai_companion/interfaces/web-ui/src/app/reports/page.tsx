'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { useLogger } from '@/hooks/useLogger';
import { getSupabaseCredentials } from '@/lib/supabase/client';
import { cn } from '@/utils/cn';
import { FORCE_REAL_DATA, USE_MOCK_DATA } from '@/lib/config';

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

  useEffect(() => {
    // Immediately set mock data to prevent UI flashing
    setReports(generateSampleReports());
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

  const handleTabChange = (index: number) => {
    setActiveTab(index);
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
        return 'bg-green-100 text-green-800 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getReportTypeColor = (type: string) => {
    switch (type) {
      case 'analytics':
        return 'bg-blue-50 text-blue-700';
      case 'engagement':
        return 'bg-purple-50 text-purple-700';
      case 'records':
        return 'bg-teal-50 text-teal-700';
      case 'summary':
        return 'bg-indigo-50 text-indigo-700';
      default:
        return 'bg-gray-50 text-gray-700';
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-10">
        <div className="flex items-center mb-2">
          <Link 
            href="/"
            className="flex items-center text-gray-600 hover:text-gray-900 mr-2"
          >
            <svg className="w-4 h-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Home
          </Link>
          <span className="mx-1 text-gray-400">/</span>
          <span className="text-gray-800">Reports</span>
        </div>
        
        <div className="flex justify-between items-center mt-6">
          <h1 className="text-2xl font-bold text-gray-900">
            Reports
          </h1>

          <button 
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-main hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-light"
            onClick={() => alert('Generate new report functionality would go here')}
            aria-label="Generate report"
          >
            <svg className="w-5 h-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Generate Report
          </button>
        </div>
        <p className="text-gray-500 mt-2">
          View and manage system reports and analytics.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Report Filters</h2>
          <button 
            onClick={handleRefresh} 
            className="p-2 text-primary-main hover:text-primary-dark rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-light"
            aria-label="Refresh reports"
          >
            <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <label htmlFor="dateRange" className="block text-sm font-medium text-gray-700 mb-1">
              Date Range
            </label>
            <select
              id="dateRange"
              value={filters.dateRange}
              onChange={(e) => handleFilterChange('dateRange', e.target.value)}
              className="block w-full bg-white border border-gray-300 rounded-md py-2 px-3 shadow-sm focus:outline-none focus:ring-primary-light focus:border-primary-light text-sm"
            >
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
              <option value="quarter">Last 90 Days</option>
              <option value="year">Last 12 Months</option>
              <option value="all">All Time</option>
            </select>
          </div>
          <div className="relative">
            <label htmlFor="reportType" className="block text-sm font-medium text-gray-700 mb-1">
              Report Type
            </label>
            <select
              id="reportType"
              value={filters.type}
              onChange={(e) => handleFilterChange('type', e.target.value)}
              className="block w-full bg-white border border-gray-300 rounded-md py-2 px-3 shadow-sm focus:outline-none focus:ring-primary-light focus:border-primary-light text-sm"
            >
              <option value="all">All Types</option>
              <option value="analytics">Analytics</option>
              <option value="engagement">Engagement</option>
              <option value="records">Records</option>
              <option value="summary">Summary</option>
            </select>
          </div>
          <div className="relative">
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              id="status"
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="block w-full bg-white border border-gray-300 rounded-md py-2 px-3 shadow-sm focus:outline-none focus:ring-primary-light focus:border-primary-light text-sm"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => handleTabChange(0)}
              className={cn(
                "py-4 px-6 text-sm font-medium flex items-center border-b-2",
                activeTab === 0
                  ? "border-primary-main text-primary-main"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
              aria-current={activeTab === 0 ? "page" : undefined}
            >
              <svg className="w-5 h-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Reports List
            </button>
            <button
              onClick={() => handleTabChange(1)}
              className={cn(
                "py-4 px-6 text-sm font-medium flex items-center border-b-2",
                activeTab === 1
                  ? "border-primary-main text-primary-main"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
              aria-current={activeTab === 1 ? "page" : undefined}
            >
              <svg className="w-5 h-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Charts
            </button>
            <button
              onClick={() => handleTabChange(2)}
              className={cn(
                "py-4 px-6 text-sm font-medium flex items-center border-b-2",
                activeTab === 2
                  ? "border-primary-main text-primary-main"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
              aria-current={activeTab === 2 ? "page" : undefined}
            >
              <svg className="w-5 h-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
              </svg>
              Summary
            </button>
          </nav>
        </div>

        {loading ? (
          <div className="flex justify-center p-8">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary-main"></div>
          </div>
        ) : (
          <>
            {error && (
              <div className="p-4 m-4 bg-red-50 border border-red-200 rounded-md text-red-800">
                {error}
              </div>
            )}

            {activeTab === 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Title
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Description
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reports.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                          No reports found matching your filters
                        </td>
                      </tr>
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
                          <tr key={report.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{report.title}</div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm text-gray-500">{report.description}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={cn("px-2 py-1 text-xs font-medium rounded-full capitalize", getReportTypeColor(report.type))}>
                                {report.type}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-500">{new Date(report.created_at).toLocaleDateString()}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span 
                                className={cn(
                                  "px-2 py-1 text-xs font-medium rounded-full uppercase", 
                                  getReportStatusColor(report.status)
                                )}
                              >
                                {report.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <button
                                className="text-primary-main hover:text-primary-dark"
                                onClick={() => alert(`Download ${report.title}`)}
                                aria-label={`Download ${report.title}`}
                              >
                                <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                              </button>
                            </td>
                          </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 1 && (
              <div className="p-8 text-center">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Charts View</h2>
                <p className="text-gray-500">
                  Report visualization charts would be displayed here.
                </p>
              </div>
            )}

            {activeTab === 2 && (
              <div className="p-8 text-center">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary View</h2>
                <p className="text-gray-500">
                  Executive summary and key metrics would be displayed here.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
} 