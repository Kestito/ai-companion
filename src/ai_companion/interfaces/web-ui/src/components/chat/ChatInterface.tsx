import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Avatar,
  Divider,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  Mic as MicIcon,
  Image as ImageIcon,
  SmartToy as BotIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { PatientInfo } from './PatientInfo';
import { Patient, PatientStatus } from '@/lib/supabase/types';
import { useLogger } from '@/hooks/useLogger';

type MessageSource = 'telegram' | 'whatsapp' | 'web';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  source?: MessageSource;
}

interface ChatInterfaceProps {
  patientId?: string;
  patient?: Patient;
  messageSource?: MessageSource;
  onSendMessage?: (message: string) => Promise<void>;
  initialMessages?: Message[];
}

/**
 * A chat interface component for the AI assistant
 * Supports displaying patient information when messages come from Telegram or WhatsApp
 * 
 * @param patientId - ID of the patient for retrieving data
 * @param patient - Patient data if already available
 * @param messageSource - Source of the message (telegram, whatsapp, or web)
 * @param onSendMessage - Callback for sending messages
 * @param initialMessages - Initial messages to display
 */
export const ChatInterface = React.memo(function ChatInterfaceComponent({
  patientId,
  patient,
  messageSource = 'web',
  onSendMessage,
  initialMessages = []
}: ChatInterfaceProps): React.ReactNode {
  const logger = useLogger({ component: 'ChatInterface' });
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [patientData, setPatientData] = useState<Patient | null>(patient || null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const isFirstRender = useRef(true);

  // Fetch patient data if needed
  useEffect(() => {
    const fetchPatientData = async () => {
      if (!patientId || patientData) return;
      
      try {
        setLoading(true);
        // In a real implementation, this would be a call to your API or Supabase
        // const { data, error } = await supabaseClient
        //   .from('patients')
        //   .select('*')
        //   .eq('id', patientId)
        //   .single();
        
        // Mock data for demo purposes
        const mockPatientData = {
          id: patientId,
          name: "John Doe",
          email: "john.doe@example.com",
          phone: "+1234567890",
          age: 45,
          gender: "male",
          status: "stable" as PatientStatus,
          admissionDate: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          diagnosis: "General checkup",
          doctor: "Dr. Smith",
          roomNumber: "A-101",
          contactNumber: "+1234567890",
          risk_level: "low"
        } as Patient;
        
        setPatientData(mockPatientData);
      } catch (error) {
        logger.error('Error fetching patient data:', error);
        setError('Failed to load patient information');
      } finally {
        setLoading(false);
      }
    };
    
    if (!isFirstRender.current) {
      fetchPatientData();
    } else {
      isFirstRender.current = false;
    }
  }, [patientId, patientData, logger]);

  // Auto scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Handler for sending a new message
  const handleSendMessage = useCallback(async () => {
    if (!newMessage.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      content: newMessage,
      sender: 'user',
      timestamp: new Date(),
      source: messageSource
    };
    
    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setLoading(true);
    
    try {
      if (onSendMessage) {
        await onSendMessage(newMessage);
      } else {
        // Mock response after delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: `This is a sample response to: "${newMessage}"`,
          sender: 'assistant',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (err) {
      logger.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [newMessage, messageSource, onSendMessage, logger]);

  // Format timestamp for display
  const formatTimestamp = (timestamp: Date) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
      
      if (diffInDays === 0) {
        // Today, show time only
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else if (diffInDays === 1) {
        // Yesterday
        return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      } else if (diffInDays < 7) {
        // Within a week
        return `${diffInDays} days ago at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      } else {
        // More than a week
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
    } catch (error) {
      logger.error('Error formatting timestamp:', error);
      return 'Invalid date';
    }
  };

  // Memoize the message input handler to prevent excessive renders
  const handleMessageChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value !== newMessage) {
      setNewMessage(value);
    }
  }, [newMessage]);

  // Memoize the send handler to prevent excessive renders
  const handleSendClick = useCallback(() => {
    if (newMessage.trim()) {
      handleSendMessage();
    }
  }, [newMessage, handleSendMessage]);

  // Memoize the key press handler
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && newMessage.trim()) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [newMessage, handleSendMessage]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '80vh' }}>
      {/* Show patient info for Telegram or WhatsApp messages */}
      {(messageSource === 'telegram' || messageSource === 'whatsapp') && patientData && (
        <PatientInfo 
          patient={patientData}
          messageSource={messageSource}
          lastActive={patientData?.updated_at ? formatTimestamp(new Date(patientData.updated_at)) : undefined}
        />
      )}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {/* Messages container */}
      <Paper
        elevation={3}
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          mb: 2,
          maxHeight: 'calc(100% - 80px)'
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <BotIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" color="textSecondary">
              Start a conversation
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Send a message to begin chatting with the AI assistant
            </Typography>
          </Box>
        ) : (
          messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
                alignItems: 'flex-start',
                gap: 1,
              }}
            >
              <Avatar
                sx={{
                  bgcolor: message.sender === 'assistant' ? 'primary.main' : 'secondary.main',
                }}
              >
                {message.sender === 'assistant' ? <BotIcon /> : <PersonIcon />}
              </Avatar>
              <Box
                sx={{
                  maxWidth: '70%',
                  p: 2,
                  borderRadius: 2,
                  bgcolor: message.sender === 'assistant' ? 'primary.light' : 'secondary.light',
                  color: message.sender === 'assistant' ? 'primary.contrastText' : 'secondary.contrastText',
                  position: 'relative',
                }}
              >
                <Typography variant="body1">{message.content}</Typography>
                <Typography
                  variant="caption"
                  sx={{
                    display: 'block',
                    mt: 1,
                    textAlign: message.sender === 'user' ? 'left' : 'right',
                    opacity: 0.8,
                  }}
                >
                  {formatTimestamp(message.timestamp)}
                  {message.source && message.source !== 'web' && (
                    <span style={{ marginLeft: '8px' }}>
                      via {message.source.charAt(0).toUpperCase() + message.source.slice(1)}
                    </span>
                  )}
                </Typography>
              </Box>
            </Box>
          ))
        )}
        <div ref={messagesEndRef} />
      </Paper>
      
      {/* Message input */}
      <Paper
        elevation={3}
        component="div"
        sx={{
          p: '2px 4px',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <IconButton color="primary" aria-label="attach file">
          <AttachFileIcon />
        </IconButton>
        <IconButton color="primary" aria-label="attach image">
          <ImageIcon />
        </IconButton>
        <TextField
          fullWidth
          placeholder="Type a message..."
          value={newMessage}
          onChange={handleMessageChange}
          variant="standard"
          multiline
          maxRows={4}
          InputProps={{ 
            disableUnderline: true,
            inputProps: {
              style: { paddingTop: 8, paddingBottom: 8 }
            }
          }}
          FormHelperTextProps={{
            style: { margin: 0 }
          }}
          disabled={loading}
          onKeyDown={handleKeyDown}
        />
        <IconButton color="primary" aria-label="record audio">
          <MicIcon />
        </IconButton>
        <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
        <IconButton
          color="primary"
          aria-label="send message"
          onClick={handleSendClick}
          disabled={!newMessage.trim() || loading}
        >
          {loading ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
      </Paper>
    </Box>
  );
}); 