'use client';

import { useState, useEffect, useRef, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Box, 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Paper, 
  Avatar, 
  CircularProgress,
  Alert,
  IconButton,
  Chip,
  Switch,
  FormControlLabel
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import SentimentSatisfiedAltIcon from '@mui/icons-material/SentimentSatisfiedAlt';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import InfoIcon from '@mui/icons-material/Info';
import Cookies from 'js-cookie';

// Message types
type MessageRole = 'system' | 'user' | 'assistant' | 'info';

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

// API interfaces
interface ChatRequest {
  message: string;
  session_id?: string;
  user_id?: string;
  user_info?: any;
}

interface ChatResponse {
  session_id: string;
  response: string;
  error?: string;
}

export default function PatientChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patientInfo, setPatientInfo] = useState<any>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [useWebSocket, setUseWebSocket] = useState<boolean>(false);
  const webSocketRef = useRef<WebSocket | null>(null);
  const [isWebSocketConnected, setIsWebSocketConnected] = useState<boolean>(false);
  
  // Check if user accessed this page correctly
  useEffect(() => {
    const patientTestMode = Cookies.get('patient_test_mode');
    const storedPatient = localStorage.getItem('test_patient');
    
    if (!patientTestMode || !storedPatient) {
      router.push('/login');
      return;
    }
    
    setPatientInfo(JSON.parse(storedPatient));
    
    // Add welcome messages
    setMessages([
      {
        id: '1',
        role: 'system',
        content: 'Welcome to the patient simulation experience. This is a test environment where you can interact with our AI healthcare assistant.',
        timestamp: new Date()
      },
      {
        id: '2',
        role: 'info',
        content: 'Your conversations will be stored in our database to help improve the system. This data may be reviewed by our healthcare team for quality improvement.',
        timestamp: new Date()
      },
      {
        id: '3',
        role: 'assistant',
        content: 'Hello! I\'m your AI healthcare assistant. How can I help you today? You can ask me health-related questions or discuss symptoms you might be experiencing.',
        timestamp: new Date()
      }
    ]);
  }, [router]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize session from localStorage or create new
  useEffect(() => {
    const storedSessionId = localStorage.getItem('chat_session_id');
    if (storedSessionId) {
      setSessionId(storedSessionId);
    }
    
    // Check if WebSocket was previously enabled
    const wsEnabled = localStorage.getItem('use_websocket') === 'true';
    setUseWebSocket(wsEnabled);
    
    // If WebSocket was enabled and we have a session ID, connect
    if (wsEnabled && storedSessionId) {
      connectWebSocket(storedSessionId);
    }
    
    // Cleanup WebSocket connection when component unmounts
    return () => {
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
    };
  }, []);

  // Connect WebSocket when preference changes
  useEffect(() => {
    localStorage.setItem('use_websocket', useWebSocket.toString());
    
    if (useWebSocket && sessionId) {
      connectWebSocket(sessionId);
    } else if (!useWebSocket && webSocketRef.current) {
      webSocketRef.current.close();
      setIsWebSocketConnected(false);
    }
  }, [useWebSocket, sessionId]);

  // Function to establish WebSocket connection
  const connectWebSocket = (sid: string) => {
    // Close existing connection if any
    if (webSocketRef.current) {
      webSocketRef.current.close();
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/web-chat/ws/${sid}`;
    
    const ws = new WebSocket(wsUrl);
    webSocketRef.current = ws;
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsWebSocketConnected(true);
      
      // Add system message about connection
      const systemMessage: Message = {
        id: `system-${Date.now()}`,
        role: 'system',
        content: 'Connected to healthcare assistant via WebSocket for real-time communication.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, systemMessage]);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          console.warn('WebSocket error:', data.error);
          setError(data.error);
          return;
        }
        
        // Add assistant message to chat
        const assistantMessage: Message = {
          id: `assistant-ws-${Date.now()}`,
          role: 'assistant',
          content: data.response,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        setIsLoading(false);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
        setError('Failed to process response from healthcare assistant');
        setIsLoading(false);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsWebSocketConnected(false);
      webSocketRef.current = null;
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error');
      setIsWebSocketConnected(false);
    };
  };

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    setError(null);
    
    // Generate a unique ID for the message
    const userMessageId = `user-${Date.now()}`;
    
    // Add user message to the chat
    const userMessage: Message = {
      id: userMessageId,
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      // Get patient info from local storage
      const storedPatient = localStorage.getItem('test_patient');
      if (!storedPatient) {
        throw new Error('Patient information not found');
      }
      
      const patientData = JSON.parse(storedPatient);
      
      // If WebSocket is connected, send message through it
      if (useWebSocket && isWebSocketConnected && webSocketRef.current) {
        const message = {
          message: input,
          user_id: patientData.id,
          user_info: patientData
        };
        
        webSocketRef.current.send(JSON.stringify(message));
        // Note: Don't set isLoading to false here - the WebSocket onmessage handler will do that
        return;
      }
      
      // Otherwise use HTTP API
      const chatRequest: ChatRequest = {
        message: input,
        session_id: sessionId || undefined,
        user_id: patientData.id,
        user_info: patientData
      };
      
      // Make API call to backend with a timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 100000); // 100 second timeout (increased 10x)
      
      const response = await fetch('/api/web-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatRequest),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      // Even if we get a non-200 response, try to parse it
      // Our API is designed to always return a valid response even on errors
      const data: ChatResponse = await response.json();
      
      // Check for error message from API
      if (data.error) {
        console.warn('API returned error:', data.error);
        throw new Error(data.error);
      }
      
      // Save session ID for future messages
      if (data.session_id && (!sessionId || sessionId !== data.session_id)) {
        setSessionId(data.session_id);
        localStorage.setItem('chat_session_id', data.session_id);
      }
      
      // Add assistant message to chat
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Error sending message:', err);
      
      let errorMessage = "I'm sorry, I'm having trouble processing your request right now. This test environment may have limited connectivity. Please try again later.";
      
      // Check if it's a timeout error
      if (err.name === 'AbortError') {
        errorMessage = "Sorry, the request took too long to process (over 100 seconds). Our test environment might be experiencing high load or complex processing requirements.";
        setError('Request timed out after 100 seconds. The server is still processing but took too long to respond.');
      } else {
        setError(err.message || 'Failed to communicate with the healthcare assistant');
      }
      
      // Add error message to chat
      const errorResponse: Message = {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleExitSimulation = () => {
    // Clear cookies and local storage
    Cookies.remove('patient_test_mode');
    localStorage.removeItem('test_patient');
    
    // Redirect back to login
    router.push('/login');
  };

  return (
    <Container maxWidth="md" sx={{ height: '100vh', display: 'flex', flexDirection: 'column', py: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <IconButton 
          onClick={handleExitSimulation}
          sx={{ mr: 2 }}
          aria-label="Back to login"
        >
          <ArrowBackIcon />
        </IconButton>
        
        <Typography variant="h5" component="h1" sx={{ flexGrow: 1 }}>
          Patient Healthcare Assistant
        </Typography>
        
        <Chip 
          icon={<InfoIcon />} 
          label="Test Mode" 
          color="warning" 
          variant="outlined" 
        />
      </Box>
      
      <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="subtitle2">
          This is a simulated patient experience. Your conversations will be stored to help improve our system.
        </Typography>
      </Alert>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
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
          mb: 2,
          bgcolor: 'background.default'
        }}
      >
        {messages.map(message => (
          <Box 
            key={message.id} 
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
              mb: 2,
              maxWidth: '100%'
            }}
          >
            {message.role === 'info' ? (
              <Alert severity="info" sx={{ width: '100%', mb: 1 }}>
                {message.content}
              </Alert>
            ) : message.role === 'system' ? (
              <Alert severity="warning" sx={{ width: '100%', mb: 1 }}>
                {message.content}
              </Alert>
            ) : (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                  <Avatar 
                    sx={{ 
                      mr: 1, 
                      bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                      width: 28,
                      height: 28
                    }}
                  >
                    {message.role === 'user' ? <PersonIcon fontSize="small" /> : <SentimentSatisfiedAltIcon fontSize="small" />}
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">
                    {message.role === 'user' ? 'You' : 'Healthcare Assistant'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </Typography>
                </Box>
                
                <Paper 
                  elevation={1}
                  sx={{
                    p: 2,
                    ml: message.role === 'user' ? 'auto' : 0,
                    mr: message.role === 'user' ? 0 : 'auto',
                    maxWidth: '80%',
                    bgcolor: message.role === 'user' ? 'primary.light' : 'background.paper',
                    color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                    borderRadius: 2
                  }}
                >
                  <Typography variant="body1">{message.content}</Typography>
                </Paper>
              </>
            )}
          </Box>
        ))}
        
        {isLoading && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar sx={{ mr: 1, bgcolor: 'secondary.main', width: 28, height: 28 }}>
              <SentimentSatisfiedAltIcon fontSize="small" />
            </Avatar>
            <CircularProgress size={20} sx={{ ml: 1 }} />
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Paper>
      
      {/* Message input */}
      <Paper 
        component="form" 
        elevation={3} 
        sx={{ 
          p: 2, 
          display: 'flex', 
          alignItems: 'center'
        }}
        onSubmit={handleSendMessage}
      >
        <TextField
          fullWidth
          placeholder="Type your health question or concern..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          variant="outlined"
          disabled={isLoading}
          InputProps={{
            sx: { borderRadius: 28, pr: 1 }
          }}
        />
        <Button 
          variant="contained" 
          color="primary" 
          disabled={isLoading || !input.trim()}
          type="submit"
          sx={{ 
            ml: 1, 
            borderRadius: '50%', 
            minWidth: 0, 
            width: 48, 
            height: 48,
            boxShadow: 2
          }}
        >
          {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
        </Button>
      </Paper>
      
      {/* Add WebSocket toggle */}
      <Box sx={{ position: 'absolute', top: 20, right: 20 }}>
        <FormControlLabel
          control={
            <Switch
              checked={useWebSocket}
              onChange={(e) => setUseWebSocket(e.target.checked)}
              color="primary"
            />
          }
          label={
            <Typography variant="body2" color="textSecondary">
              {isWebSocketConnected ? "WebSocket Connected" : "Use WebSocket"}
            </Typography>
          }
        />
      </Box>
    </Container>
  );
} 