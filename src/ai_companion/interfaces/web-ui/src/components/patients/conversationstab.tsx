'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Skeleton, 
  Chip, 
  IconButton, 
  Icon,
  Button,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider
} from '@mui/material';
import { 
  ArrowDropUp as ArrowDropUpIcon, 
  ArrowDropDown as ArrowDropDownIcon,
  BugReport as BugReportIcon,
  Add as AddIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { fetchPatientConversations, fetchConversationMessages, createTestConversation } from '@/lib/supabase/patientService';

interface ConversationsTabProps {
  patientId: string;
}

/**
 * Component to display conversation messages
 */
function ConversationMessages({ conversationId }: { conversationId: string }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadMessages = async () => {
      try {
        setLoading(true);
        const data = await fetchConversationMessages(conversationId);
        setMessages(data);
      } catch (err) {
        console.error('Error loading messages:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadMessages();
  }, [conversationId]);
  
  if (loading) return <Skeleton variant="rectangular" height={200} />;
  
  if (messages.length === 0) {
    return <Typography>No messages found for this conversation.</Typography>;
  }
  
  return (
    <Paper sx={{ p: 2, mb: 2, maxHeight: 300, overflow: 'auto' }}>
      {messages.map((message) => (
        <Box 
          key={message.id} 
          sx={{
            py: 1,
            px: 2,
            mb: 1,
            borderRadius: 2,
            backgroundColor: message.sender === 'user' ? 'primary.light' : 'secondary.light',
            color: message.sender === 'user' ? 'primary.contrastText' : 'secondary.contrastText',
            alignSelf: message.sender === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%',
            position: 'relative',
            ml: message.sender === 'user' ? 'auto' : 0
          }}
        >
          <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
            {message.sender === 'user' ? 'Patient' : 'AI Assistant'}
          </Typography>
          <Typography variant="body1">{message.message_content}</Typography>
          <Typography variant="caption" sx={{ display: 'block', textAlign: 'right', mt: 1 }}>
            {new Date(message.sent_at).toLocaleString()}
          </Typography>
        </Box>
      ))}
    </Paper>
  );
}

/**
 * Component to display all conversations for a patient with debugging information
 */
export function ConversationsTab({ patientId }: ConversationsTabProps) {
  const [conversations, setConversations] = useState<any[]>([]);
  const [expandedConversation, setExpandedConversation] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDebug, setShowDebug] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchPatientConversations(patientId);
      setConversations(data);
    } catch (err: any) {
      console.error('Error loading conversations:', err);
      setError(err?.message || 'Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };
  
  const handleCreateTestConversation = async () => {
    try {
      setLoading(true);
      setError(null);
      await createTestConversation(patientId);
      // Reload conversations after creating a test one
      await loadConversations();
    } catch (err: any) {
      console.error('Error creating test conversation:', err);
      setError(err?.message || 'Failed to create test conversation');
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadConversations();
  }, [patientId]);
  
  const handleExpandConversation = (conversationId: string) => {
    if (expandedConversation === conversationId) {
      setExpandedConversation(null);
    } else {
      setExpandedConversation(conversationId);
    }
  };
  
  const getPlatformIcon = (platform: string = '') => {
    switch (platform.toLowerCase()) {
      case 'whatsapp':
        return <Icon className="fa-brands fa-whatsapp" sx={{ color: '#25D366' }} />;
      case 'telegram':
        return <Icon className="fa-brands fa-telegram" sx={{ color: '#0088cc' }} />;
      case 'chainlit':
        return <Icon className="fa-solid fa-comments" />;
      default:
        return <Icon className="fa-solid fa-comment" />;
    }
  };
  
  if (loading) {
    return (
      <Box sx={{ pt: 2 }}>
        <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={100} />
      </Box>
    );
  }
  
  return (
    <Box sx={{ pt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Patient Conversations</Typography>
        <Box>
          <Button 
            startIcon={<RefreshIcon />} 
            onClick={loadConversations}
            size="small"
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button 
            startIcon={<BugReportIcon />} 
            onClick={() => setShowDebug(!showDebug)}
            size="small"
            color={showDebug ? "warning" : "primary"}
            variant={showDebug ? "contained" : "outlined"}
          >
            {showDebug ? "Hide Debug" : "Debug"}
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {showDebug && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.100' }}>
          <Typography variant="subtitle2" gutterBottom>Debug Information</Typography>
          <Typography variant="body2">Patient ID: {patientId}</Typography>
          <Typography variant="body2">Conversations found: {conversations.length}</Typography>
          <Divider sx={{ my: 1 }} />
          <Typography variant="body2" gutterBottom>Raw Data:</Typography>
          <Box 
            component="pre" 
            sx={{ 
              p: 1, 
              bgcolor: 'background.paper', 
              borderRadius: 1, 
              overflow: 'auto',
              maxHeight: 200,
              fontSize: '0.75rem'
            }}
          >
            {JSON.stringify(conversations, null, 2)}
          </Box>
        </Paper>
      )}
      
      {conversations.length === 0 ? (
        <Box sx={{ pt: 2, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">No conversations found</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This patient doesn't have any recorded conversations yet.
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />}
              sx={{ mr: 1 }}
            >
              Start New Conversation
            </Button>
            <Button 
              variant="outlined" 
              onClick={handleCreateTestConversation}
              disabled={loading}
            >
              Create Test Conversation
            </Button>
          </Box>
        </Box>
      ) : (
        conversations.map((conversation) => (
          <Paper key={conversation.id} sx={{ mb: 2, overflow: 'hidden' }}>
            <Box 
              sx={{
                p: 2,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                cursor: 'pointer',
                '&:hover': { bgcolor: 'action.hover' }
              }}
              onClick={() => handleExpandConversation(conversation.id)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {getPlatformIcon(conversation.platform)}
                <Box sx={{ ml: 2 }}>
                  <Typography variant="subtitle1">
                    {conversation.title || `${conversation.platform || 'Unknown'} Conversation`}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Started: {new Date(conversation.created_at || conversation.start_time).toLocaleString()}
                  </Typography>
                </Box>
              </Box>
              <Box>
                <Chip 
                  label={conversation.status || 'unknown'} 
                  color={conversation.status === 'active' ? 'success' : 'default'}
                  size="small"
                />
                <IconButton size="small" sx={{ ml: 1 }}>
                  {expandedConversation === conversation.id ? 
                    <ArrowDropUpIcon /> : <ArrowDropDownIcon />
                  }
                </IconButton>
              </Box>
            </Box>
            
            {expandedConversation === conversation.id && (
              <Box sx={{ p: 2, bgcolor: 'background.default' }}>
                <ConversationMessages conversationId={conversation.id} />
              </Box>
            )}
          </Paper>
        ))
      )}
    </Box>
  );
} 