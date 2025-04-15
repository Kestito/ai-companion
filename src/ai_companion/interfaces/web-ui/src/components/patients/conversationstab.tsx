'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
import { fetchPatientConversations, fetchConversationMessages } from '@/lib/supabase/patientService';
import { createMinimalConversation, getPatientConversations, getConversationMessages } from '@/lib/supabase/conversationDirectService';

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
        // Try the direct service first
        try {
          const directMessages = await getConversationMessages(conversationId);
          if (directMessages && directMessages.length > 0) {
            setMessages(directMessages);
            return;
          }
        } catch (directErr) {
          console.warn('Direct message loading failed, falling back to legacy method:', directErr);
        }
        
        // Fall back to the legacy method if direct approach fails
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
  const router = useRouter();
  const [conversations, setConversations] = useState<any[]>([]);
  const [expandedConversation, setExpandedConversation] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDebug, setShowDebug] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manualMode, setManualMode] = useState(false);
  const [uiOnlyMode, setUiOnlyMode] = useState(false);
  
  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try the direct service first (Telegram style)
      try {
        const directConversations = await getPatientConversations(patientId);
        if (directConversations && directConversations.length > 0) {
          setConversations(directConversations);
          return;
        }
      } catch (directErr) {
        console.warn('Direct conversation loading failed, falling back to legacy method:', directErr);
      }
      
      // Fall back to the legacy method if direct approach fails
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
      
      // Try the direct minimal approach first (Telegram style)
      try {
        const newConversation = await createMinimalConversation(patientId);
        if (newConversation && newConversation.id) {
          console.log('Successfully created conversation using telegram-style approach:', newConversation);
          await loadConversations();
          return;
        }
      } catch (directErr) {
        console.warn('Direct conversation creation failed, trying fallbacks:', directErr);
      }
      
      // If direct method fails, try the legacy method
      await import('@/lib/supabase/patientService').then(m => m.createTestConversation(patientId));
      await loadConversations();
    } catch (err: any) {
      console.error('Error creating test conversation:', err);
      setError(`Failed to create test conversation automatically: ${err?.message}. Try the manual method instead.`);
      setManualMode(true);
      setLoading(false);
    }
  };
  
  const handleCreateUIOnlyConversation = () => {
    try {
      // Create a mock conversation in UI only without database
      const mockConversation = {
        id: `local-${Date.now()}`,
        user_id: patientId,
        patient_id: patientId,
        status: 'active',
        platform: 'web-ui',
        start_time: new Date().toISOString(),
        created_at: new Date().toISOString(),
        is_ui_only: true // Flag to indicate this is UI-only
      };
      
      // Inject directly into state
      setConversations([mockConversation]);
      setError('This is a UI-only conversation and won\'t persist in the database. Click it to see simulated messages.');
      setUiOnlyMode(true);
      setManualMode(false);
      setLoading(false);
    } catch (err: any) {
      console.error('Error creating UI-only conversation:', err);
      setError(`Failed to create UI-only conversation: ${err?.message}`);
    }
  };
  
  const handleCreateManualTestConversation = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const supabase = await import('@/lib/supabase/client').then(m => m.getSupabaseClient());
      
      // Match the exact schema from the database: 
      // id, patient_id, platform, start_time, end_time, conversation_type, status
      const conversationData = {
        id: `test-${Date.now()}`,
        patient_id: patientId,
        platform: 'web-ui',
        start_time: new Date().toISOString(),
        end_time: null,
        conversation_type: 'test',
        status: 'active'
        // No title or created_at fields
      };
      
      console.log('Trying with exact schema match:', conversationData);
      
      const { data, error } = await supabase
        .from('conversations')
        .insert([conversationData])
        .select();
      
      if (error) {
        console.error('Schema-matched conversation creation failed:', error);
        setError(`Database operation failed: ${error.message}. Using UI-only mode instead.`);
        setUiOnlyMode(true);
      } else {
        console.log('Successfully created schema-matched conversation:', data);
        setManualMode(false);
        // Reload conversations after creating a test one
        await loadConversations();
      }
    } catch (err: any) {
      console.error('Error in manual test conversation creation:', err);
      setError(`Manual test conversation failed: ${err?.message}`);
      setUiOnlyMode(true);
    } finally {
      setLoading(false);
    }
  };
  
  const handleStartNewConversation = () => {
    // Store patient ID in local storage for the chat interface
    try {
      // First get the patient information
      const getPatientInfo = async () => {
        const { fetchPatientById } = await import('@/lib/supabase/patientService');
        const patient = await fetchPatientById(patientId);
        
        if (patient) {
          // Mark as test mode and store patient data for chat interface
          document.cookie = "patient_test_mode=true;path=/;max-age=3600";
          localStorage.setItem('test_patient', JSON.stringify(patient));
          
          // Redirect to patient chat
          router.push('/patient-chat');
        } else {
          setError('Failed to load patient information for chat');
        }
      };
      
      getPatientInfo();
    } catch (err: any) {
      console.error('Error starting new conversation:', err);
      setError(`Failed to start new conversation: ${err?.message}`);
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
          
          {uiOnlyMode ? (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.light', borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                UI-Only Mode (Final Option)
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                All database methods failed. This will create a simulated conversation that exists only in the UI memory.
              </Typography>
              <Button 
                variant="contained" 
                color="warning"
                onClick={handleCreateUIOnlyConversation}
                disabled={loading}
              >
                Create UI-Only Conversation
              </Button>
            </Box>
          ) : manualMode ? (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Manual Creation Mode
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Automatic conversation creation failed. This button will try several minimal approaches to work around database schema issues.
              </Typography>
              <Button 
                variant="contained" 
                color="warning"
                onClick={handleCreateManualTestConversation}
                disabled={loading}
              >
                {loading ? "Trying..." : "Try Ultra Minimal Creation"}
              </Button>
            </Box>
          ) : (
            <Box sx={{ mt: 2 }}>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />}
                sx={{ mr: 1 }}
                onClick={handleStartNewConversation}
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
          )}
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
                    {conversation.is_ui_only && " (UI Only)"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Started: {new Date(conversation.created_at || conversation.start_time).toLocaleString()}
                  </Typography>
                </Box>
              </Box>
              <Box>
                <Chip 
                  label={conversation.is_ui_only ? "simulation" : (conversation.status || 'unknown')}
                  color={conversation.is_ui_only ? "warning" : conversation.status === 'active' ? 'success' : 'default'}
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
                {conversation.is_ui_only ? 
                  <ConversationMessagesUIOnly conversationId={conversation.id} /> :
                  <ConversationMessages conversationId={conversation.id} />
                }
              </Box>
            )}
          </Paper>
        ))
      )}
    </Box>
  );
}

// Add fake messages for UI-only conversation mode
function ConversationMessagesUIOnly({ conversationId }: { conversationId: string }) {
  // Create mock messages
  const mockMessages = [
    {
      id: `msg-${Date.now()}-1`,
      conversation_id: conversationId,
      message_content: 'Hello, how are you feeling today?',
      sender: 'assistant',
      sent_at: new Date(Date.now() - 60000).toISOString(),
    },
    {
      id: `msg-${Date.now()}-2`,
      conversation_id: conversationId,
      message_content: 'I\'m feeling better, thank you for asking.',
      sender: 'user',
      sent_at: new Date().toISOString(),
    }
  ];
  
  return (
    <Paper sx={{ p: 2, mb: 2, maxHeight: 300, overflow: 'auto' }}>
      <Alert severity="warning" sx={{ mb: 2 }}>This is a simulated conversation (UI only).</Alert>
      {mockMessages.map((message) => (
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