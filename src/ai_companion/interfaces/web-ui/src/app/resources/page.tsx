'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Typography, 
  Container, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  CardActions,
  Button, 
  TextField, 
  InputAdornment,
  CircularProgress,
  Chip,
  IconButton,
  Divider,
  Tabs,
  Tab,
  Pagination,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Tooltip,
  Alert,
  Link as MuiLink
} from '@mui/material';
import { 
  Search as SearchIcon, 
  Home as HomeIcon,
  ContentCopy as ContentCopyIcon,
  Share as ShareIcon,
  FilterList as FilterListIcon,
  BookmarkBorder as BookmarkIcon,
  Bookmark as BookmarkFilledIcon,
  OpenInNew as OpenInNewIcon,
  SortByAlpha as SortIcon,
  Description as DocumentIcon,
  SourceOutlined as SourceIcon
} from '@mui/icons-material';
import Link from 'next/link';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { useLogger } from '@/hooks/useLogger';

// Define document type
interface DocumentResource {
  id: string;
  title: string;
  url: string;
  summary: string;
  source_type: string;
  language: string;
  created_at: string;
  metadata: any;
  resourceType: 'document';
}

// Define resource type from site_pages
interface SitePageResource {
  id: string;
  title: string;
  url: string;
  summary: string;
  metadata: any;
  source_type: string;
  language: string;
  created_at: string;
  resourceType: 'sitePage';
}

// Combined resource type
type CombinedResource = DocumentResource | SitePageResource;

// Filter options
interface DocumentFilters {
  source: string;
  language: string;
  searchQuery: string;
  sortBy: 'title' | 'created_at' | 'last_modified';
  sortOrder: 'asc' | 'desc';
}

export default function ResourcesPage() {
  const [documents, setDocuments] = useState<CombinedResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bookmarkedDocs, setBookmarkedDocs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState<DocumentFilters>({
    source: 'all',
    language: 'all',
    searchQuery: '',
    sortBy: 'created_at',
    sortOrder: 'desc'
  });
  
  const documentsPerPage = 9;
  const logger = useLogger({ component: 'ResourcesPage' });
  const supabase = createClientComponentClient();

  // Fetch documents on initial load and when filters change
  useEffect(() => {
    loadDocuments();
    // Load bookmarks from localStorage
    const savedBookmarks = localStorage.getItem('bookmarkedDocuments');
    if (savedBookmarks) {
      setBookmarkedDocs(JSON.parse(savedBookmarks));
    }
  }, [filters.source, filters.language, filters.sortBy, filters.sortOrder, currentPage]);

  // Handle search with debounce
  useEffect(() => {
    const handler = setTimeout(() => {
      if (currentPage !== 1) {
        setCurrentPage(1);
      } else {
        loadDocuments();
      }
    }, 500);

    return () => {
      clearTimeout(handler);
    };
  }, [filters.searchQuery]);

  async function loadDocuments() {
    try {
      setLoading(true);
      setError(null);
      
      // Load documents
      let documentsQuery = supabase
        .from('documents')
        .select('id, title, url, summary, source_type, language, created_at, metadata');
      
      // Apply source filter
      if (filters.source !== 'all') {
        documentsQuery = documentsQuery.eq('source_type', filters.source);
      }
      
      // Apply language filter
      if (filters.language !== 'all') {
        documentsQuery = documentsQuery.eq('language', filters.language);
      }
      
      // Apply search query
      if (filters.searchQuery) {
        documentsQuery = documentsQuery.or(`title.ilike.%${filters.searchQuery}%,summary.ilike.%${filters.searchQuery}%`);
      }
      
      // Get documents count for pagination
      const docsCountResponse = await supabase
        .from('documents')
        .select('id', { count: 'exact', head: true })
        .eq(filters.source !== 'all' ? 'source_type' : 'id', filters.source !== 'all' ? filters.source : 'id')
        .eq(filters.language !== 'all' ? 'language' : 'id', filters.language !== 'all' ? filters.language : 'id')
        .or(filters.searchQuery ? `title.ilike.%${filters.searchQuery}%,summary.ilike.%${filters.searchQuery}%` : 'id.neq.id');
      
      // Load site_pages resources
      let sitePagesQuery = supabase
        .from('site_pages')
        .select('id, url, title, summary, metadata');
      
      // Apply search query to site_pages
      if (filters.searchQuery) {
        sitePagesQuery = sitePagesQuery.or(`title.ilike.%${filters.searchQuery}%,summary.ilike.%${filters.searchQuery}%`);
      }
      
      // Get site_pages count
      const pagesCountResponse = await supabase
        .from('site_pages')
        .select('id', { count: 'exact', head: true })
        .or(filters.searchQuery ? `title.ilike.%${filters.searchQuery}%,summary.ilike.%${filters.searchQuery}%` : 'id.neq.id');
      
      // Calculate total count and pages
      const totalCount = (docsCountResponse.count || 0) + (pagesCountResponse.count || 0);
      const pages = Math.ceil(totalCount / documentsPerPage);
      setTotalPages(pages || 1);
      
      // Apply sorting and pagination to documents query
      const { data: docsData, error: docsError } = await documentsQuery
        .order(filters.sortBy, { ascending: filters.sortOrder === 'asc' });
      
      if (docsError) {
        throw docsError;
      }
      
      // Apply sorting to site_pages query
      const { data: pagesData, error: pagesError } = await sitePagesQuery
        .order('title', { ascending: filters.sortOrder === 'asc' });
      
      if (pagesError) {
        throw pagesError;
      }
      
      // Convert documents to typed objects
      const typedDocsData: DocumentResource[] = docsData ? docsData.map(doc => ({
        id: doc.id,
        title: doc.title,
        url: doc.url,
        summary: doc.summary,
        source_type: doc.source_type,
        language: doc.language,
        created_at: doc.created_at,
        metadata: doc.metadata,
        resourceType: 'document'
      })) : [];
      
      // Convert site_pages to typed objects
      const typedPagesData: SitePageResource[] = pagesData ? pagesData.map(page => ({
        id: page.id,
        title: page.title,
        url: page.url,
        summary: page.summary,
        metadata: page.metadata,
        source_type: page.metadata?.source || 'web_page',
        language: page.metadata?.language || 'en',
        created_at: page.metadata?.created_at || new Date().toISOString(),
        resourceType: 'sitePage'
      })) : [];
      
      // Combine all data
      const combinedData: CombinedResource[] = [...typedDocsData, ...typedPagesData];
      
      // Sort combined data
      const sortedData = combinedData.sort((a, b) => {
        if (filters.sortBy === 'title') {
          return filters.sortOrder === 'asc' 
            ? a.title.localeCompare(b.title)
            : b.title.localeCompare(a.title);
        } else {
          const dateA = new Date(a.created_at).getTime();
          const dateB = new Date(b.created_at).getTime();
          return filters.sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
        }
      });
      
      // Apply pagination to the combined data
      const paginatedData = sortedData.slice(
        (currentPage - 1) * documentsPerPage,
        currentPage * documentsPerPage
      );
      
      setDocuments(paginatedData);
    } catch (err: any) {
      logger.error('Error loading resources', err);
      setError(err.message || 'Failed to load resources');
    } finally {
      setLoading(false);
    }
  }
  
  // Handle filter changes
  const handleFilterChange = (name: keyof DocumentFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Reset to first page when filter changes
    if (currentPage !== 1) {
      setCurrentPage(1);
    }
  };
  
  // Handle tab changes (All/Bookmarked)
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  // Handle pagination
  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setCurrentPage(value);
  };
  
  // Toggle bookmark status
  const toggleBookmark = (docId: string) => {
    let updatedBookmarks: string[];
    
    if (bookmarkedDocs.includes(docId)) {
      updatedBookmarks = bookmarkedDocs.filter(id => id !== docId);
    } else {
      updatedBookmarks = [...bookmarkedDocs, docId];
    }
    
    setBookmarkedDocs(updatedBookmarks);
    // Save to localStorage
    localStorage.setItem('bookmarkedDocuments', JSON.stringify(updatedBookmarks));
  };
  
  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };
  
  // Filter documents for the active tab (All/Bookmarked)
  const filteredDocuments = useMemo(() => {
    if (activeTab === 0) {
      return documents;
    } else {
      return documents.filter(doc => bookmarkedDocs.includes(doc.id));
    }
  }, [documents, bookmarkedDocs, activeTab]);
  
  // Format source type for display
  const formatSourceType = (sourceType: string) => {
    if (!sourceType) return 'Unknown';
    
    return sourceType
      .replace(/_/g, ' ')
      .replace(/docs/i, '')
      .replace(/(\w+)/g, (match) => match.charAt(0).toUpperCase() + match.slice(1))
      .trim();
  };

  // Determine color for source chip
  const getSourceColor = (sourceType: string) => {
    if (sourceType.includes('pola')) return 'primary';
    if (sourceType === 'web_page') return 'info';
    return 'secondary';
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
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
          <Typography color="text.primary">Resources</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
          <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
            Resources & Reference Materials
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph>
          Browse through our collection of resources, documents, and reference materials.
        </Typography>
      </Box>
      
      {/* Search and Filters */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search resources..."
              variant="outlined"
              value={filters.searchQuery}
              onChange={(e) => handleFilterChange('searchQuery', e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Source</InputLabel>
              <Select
                value={filters.source}
                label="Source"
                onChange={(e) => handleFilterChange('source', e.target.value)}
              >
                <MenuItem value="all">All Sources</MenuItem>
                <MenuItem value="pola_docs">POLA</MenuItem>
                <MenuItem value="priesvezi_docs">Prieš Vėžį</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Sort By</InputLabel>
              <Select
                value={filters.sortBy}
                label="Sort By"
                onChange={(e) => handleFilterChange('sortBy', e.target.value as 'title' | 'created_at' | 'last_modified')}
              >
                <MenuItem value="title">Title</MenuItem>
                <MenuItem value="created_at">Date Added</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Order</InputLabel>
              <Select
                value={filters.sortOrder}
                label="Order"
                onChange={(e) => handleFilterChange('sortOrder', e.target.value as 'asc' | 'desc')}
              >
                <MenuItem value="asc">Ascending</MenuItem>
                <MenuItem value="desc">Descending</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Tabs for All and Bookmarked */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          centered
        >
          <Tab label="All Documents" />
          <Tab label="Bookmarked" />
        </Tabs>
      </Paper>

      {/* Error message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {/* Loading state */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 5 }}>
          <CircularProgress />
        </Box>
      )}
      
      {/* Documents and Resources grid */}
      {!loading && filteredDocuments.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No resources found matching your criteria
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Try adjusting your search or filters
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {filteredDocuments.map((resource) => (
            <Grid item xs={12} md={6} lg={4} key={resource.id}>
              <Card sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': { 
                  boxShadow: 6,
                  transform: 'translateY(-4px)'
                } 
              }}>
                <CardContent sx={{ flex: '1 0 auto' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Chip 
                      label={formatSourceType(resource.source_type)} 
                      size="small"
                      icon={<SourceIcon />}
                      color={getSourceColor(resource.source_type)}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(resource.created_at)}
                    </Typography>
                  </Box>
                  
                  <Typography variant="h6" component="h2" gutterBottom sx={{ fontWeight: 'medium' }}>
                    {resource.title}
                  </Typography>
                  
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ 
                      mb: 2,
                      overflow: 'hidden',
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      height: '4.5em'
                    }}
                  >
                    {resource.summary}
                  </Typography>
                </CardContent>
                
                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Box>
                    <Tooltip title="Visit Source">
                      <IconButton 
                        component="a" 
                        href={resource.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        size="small"
                      >
                        <OpenInNewIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={bookmarkedDocs.includes(resource.id) ? "Remove Bookmark" : "Add Bookmark"}>
                      <IconButton 
                        onClick={() => toggleBookmark(resource.id)} 
                        size="small"
                        color={bookmarkedDocs.includes(resource.id) ? "primary" : "default"}
                      >
                        {bookmarkedDocs.includes(resource.id) ? (
                          <BookmarkFilledIcon fontSize="small" />
                        ) : (
                          <BookmarkIcon fontSize="small" />
                        )}
                      </IconButton>
                    </Tooltip>
                  </Box>
                  
                  <Button 
                    variant="text" 
                    size="small"
                    onClick={() => alert(`View details functionality for resource: ${resource.id}`)}
                  >
                    View Details
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
      
      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Pagination 
            count={totalPages} 
            page={currentPage} 
            onChange={handlePageChange} 
            color="primary" 
          />
        </Box>
      )}
    </Container>
  );
} 