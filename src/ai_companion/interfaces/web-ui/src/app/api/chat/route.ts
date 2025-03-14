import { NextRequest, NextResponse } from 'next/server';
import { getSupabaseClient } from '@/lib/supabase/client';
import { v4 as uuidv4 } from 'uuid';

// Define the types directly to avoid import issues
type MessageRole = 'system' | 'user' | 'assistant' | 'function' | 'tool';

interface Message {
  content: string;
  role: MessageRole;
  metadata?: Record<string, any>;
}

// Define additional types for our database schema
interface ConversationDetail {
  id?: string;
  conversation_id: string;
  message_content: string;
  message_type: string;
  sent_at: string;
  sender: 'user' | 'assistant' | 'system';
  metadata?: string;
}

interface DatabaseMessage {
  id?: string;
  patient_id?: string;
  conversation_id?: string;
  content: string;
  message_type: string;
  sent_at: string;
  read_at?: string;
  priority?: string;
  metadata?: string;
}

interface ConversationMessage {
  content: string;
  role: MessageRole;
  timestamp: string;
  metadata: Record<string, any>;
}

interface AICompanionState {
  messages: Message[];
  workflow?: string;
  patient_id?: string;
  context?: any;
  rag_context?: any[];
  rag_retry_count?: number;
  memory_context?: any;
  conversation_memory?: any;
  generated_summary?: string;
}

// Fallback responses when the backend is unavailable
const FALLBACK_RESPONSES = [
  "I understand your question. This test environment is currently running in standalone mode. Your message has been recorded for training purposes.",
  "Thanks for your message. I'm currently operating in offline mode, but I'm collecting these conversations to improve the system.",
  "I appreciate your question. The test mode is currently running without the backend connection, but this helps us test the user interface.",
  "Thank you for testing the patient interface. While I can't process your specific request right now, this interaction helps us improve the system.",
  "I see your message. The system is currently in demonstration mode with limited functionality, but all interactions are being saved to enhance our service."
];

// Get a random fallback response
function getFallbackResponse(): string {
  const index = Math.floor(Math.random() * FALLBACK_RESPONSES.length);
  return FALLBACK_RESPONSES[index];
}

// Initialize the API route handler
export async function POST(req: NextRequest) {
  console.log('==================== CHAT API JOURNEY ====================');
  console.log('[1] Chat API request received');
  
  try {
    // Parse the request body
    console.log('[2] Parsing request body');
    const body = await req.json();
    const { message, patient_id, platform, conversation_id, is_test_mode } = body;
    console.log(`[3] Request details: patient_id=${patient_id}, platform=${platform || 'web-ui'}, has_conversation_id=${!!conversation_id}, is_test_mode=${is_test_mode}`);
    console.log(`[4] Message: "${message.substring(0, 50)}${message.length > 50 ? '...' : ''}"`);
    
    // Validate required fields
    if (!message || !patient_id) {
      console.log('[ERROR] Missing required fields');
      return NextResponse.json(
        { error: 'Message and patient_id are required' },
        { status: 400 }
      );
    }
    
    // Get Supabase client
    console.log('[5] Getting Supabase client');
    const supabase = getSupabaseClient();
    
    // Check if required tables exist by making test queries to conform to proper schema
    console.log('[6] Checking database schema validity');
    let conversationsSchemaValid = true;
    let conversationDetailsSchemaValid = true;
    let messagesSchemaValid = true;
    
    try {
      // Test conversations table
      console.log('[7] Testing conversations table...');
      const { error: conversationsError } = await supabase
        .from('conversations')
        .select('id, patient_id')
        .limit(1);
      
      if (conversationsError) {
        console.warn('[8] Conversations table validation ERROR:', conversationsError.message);
        conversationsSchemaValid = false;
      } else {
        console.log('[8] Conversations table is valid');
      }
      
      // Test conversation_details table (which is the primary table according to schema)
      console.log('[9] Testing conversation_details table...');
      const { error: detailsError } = await supabase
        .from('conversation_details')
        .select('id, conversation_id, message_content')
        .limit(1);
      
      if (detailsError) {
        console.warn('[10] Conversation_details table validation ERROR:', detailsError.message);
        conversationDetailsSchemaValid = false;
      } else {
        console.log('[10] Conversation_details table is valid');
      }
      
      // Test messages table
      console.log('[11] Testing messages table...');
      const { error: messagesError } = await supabase
        .from('messages')
        .select('id, conversation_id, content, message_type')
        .limit(1);
      
      if (messagesError) {
        console.warn('[12] Messages table validation ERROR:', messagesError.message);
        messagesSchemaValid = false;
      } else {
        console.log('[12] Messages table is valid');
      }
    } catch (e) {
      console.warn('[ERROR] Error checking tables:', e);
      conversationsSchemaValid = false;
      conversationDetailsSchemaValid = false;
      messagesSchemaValid = false;
    }
    
    console.log(`[13] Schema validation results: conversations=${conversationsSchemaValid}, conversation_details=${conversationDetailsSchemaValid}, messages=${messagesSchemaValid}`);
    
    // Get or create conversation
    let activeConversationId = conversation_id;
    
    if (!activeConversationId) {
      console.log('[14] No conversation ID provided, creating new conversation');
      
      // If conversations schema is invalid, just generate a temporary ID
      if (!conversationsSchemaValid) {
        activeConversationId = `temp-${uuidv4()}`;
        console.log(`[15] Using temporary conversation ID due to schema issues: ${activeConversationId}`);
      } else {
        try {
          // Create a new conversation record
          console.log('[15] Creating new conversation record in database');
          const conversationData = {
            patient_id: patient_id,
            start_time: new Date().toISOString(),
            end_time: new Date().toISOString(), 
            platform: platform || 'web-ui',
            conversation_type: 'patient_chat',
            status: 'active'
          };
          
          console.log('[16] Conversation data:', JSON.stringify(conversationData, null, 2));
          
          const { data, error } = await supabase
            .from('conversations')
            .insert(conversationData)
            .select('id')
            .single();
            
          if (!error && data) {
            activeConversationId = data.id;
            console.log(`[17] Successfully created conversation with ID: ${activeConversationId}`);
            
            // If conversation_details table is valid, create a record there too
            if (conversationDetailsSchemaValid) {
              console.log('[18] Creating initial conversation_details record');
              const detailsData = {
                conversation_id: activeConversationId,
                message_content: 'Started from web-ui patient chat',
                message_type: 'system',
                sent_at: new Date().toISOString(),
                sender: 'system',
                metadata: JSON.stringify({
                  is_test_mode: is_test_mode === true,
                  platform: platform || 'web-ui'
                })
              };
              
              // Don't wait for this to complete to avoid blocking
              supabase
                .from('conversation_details')
                .insert(detailsData)
                .then(({ error }) => {
                  if (error) console.warn('[19] Error creating conversation_details:', error.message);
                  else console.log('[19] Successfully created conversation_details record');
                });
            }
          } else {
            console.warn('[17] Failed to create conversation record:', error?.message);
            // Generate a temporary conversation ID if database insert failed
            activeConversationId = `temp-${uuidv4()}`;
            console.log(`[18] Using temporary conversation ID: ${activeConversationId}`);
          }
        } catch (err) {
          console.error('[ERROR] Error creating conversation:', err);
          // Generate a temporary conversation ID if database operation failed
          activeConversationId = `temp-${uuidv4()}`;
          console.log(`[FALLBACK] Using temporary conversation ID: ${activeConversationId}`);
        }
      }
    } else {
      console.log(`[14] Using existing conversation ID: ${activeConversationId}`);
      
      if (conversationsSchemaValid) {
        // Only try to update if the schema is valid
        try {
          // Update the conversation end_time (equivalent to last_message_at)
          console.log('[15] Updating existing conversation timestamp');
          await supabase
            .from('conversations')
            .update({
              end_time: new Date().toISOString()
            })
            .eq('id', activeConversationId);
          console.log('[16] Successfully updated conversation timestamp');
        } catch (err) {
          console.warn('[16] Error updating conversation timestamp:', err);
          // Continue anyway
        }
      }
    }
    
    // Store the user message in the messages table if valid
    console.log('[20] Storing user message');
    let messageId = uuidv4();
    const timestamp = new Date().toISOString();
    
    if (messagesSchemaValid) {
      try {
        console.log('[21] Inserting message into messages table');
        const { data, error } = await supabase
          .from('messages')
          .insert({
            id: messageId,
            patient_id: patient_id,
            content: message,
            message_type: 'text',
            sent_at: timestamp,
            read_at: timestamp,
            priority: 'normal',
            metadata: JSON.stringify({
              platform: platform || 'web-ui',
              is_test_mode: is_test_mode === true
            })
          })
          .select('id')
          .single();
          
        if (!error && data) {
          messageId = data.id;
          console.log(`[22] Successfully inserted message with ID: ${messageId}`);
        } else {
          console.warn('[22] Error inserting message:', error?.message);
        }
      } catch (err) {
        console.warn('[ERROR] Error storing message:', err);
        // Continue anyway since this is a test environment
      }
    } else {
      console.log('[21] Messages table invalid, skipping message storage');
    }
    
    // Store in conversation_details to maintain the relationship
    if (conversationDetailsSchemaValid) {
      try {
        console.log('[23] Inserting user message into conversation_details');
        await supabase
          .from('conversation_details')
          .insert({
            conversation_id: activeConversationId,
            message_content: message,
            message_type: 'user',
            sent_at: timestamp,
            sender: 'user',
            metadata: JSON.stringify({
              platform: platform || 'web-ui',
              patient_id: patient_id,
              is_test_mode: is_test_mode === true,
              message_id: messageId
            })
          });
        console.log('[24] Successfully inserted into conversation_details');
      } catch (err) {
        console.warn('[ERROR] Error storing conversation details:', err);
        // Continue anyway
      }
    } else {
      console.log('[23] Conversation_details table invalid, skipping storage');
    }
    
    // Try to call the AI companion API, use fallback if it fails
    console.log('[25] Preparing to get AI response');
    let assistantResponse = '';
    let useGraphAPI = true;
    
    try {
      // Fetch conversation history for context
      console.log('[26] Fetching conversation history for context');
      let conversationMessages: ConversationMessage[] = [];
      
      if (conversationDetailsSchemaValid) {
        // Prefer conversation_details for history as it's the main conversation table
        console.log('[27] Fetching from conversation_details table');
        const { data: details } = await supabase
          .from('conversation_details')
          .select('*')
          .eq('conversation_id', activeConversationId)
          .order('sent_at', { ascending: true })
          .limit(10);
          
        if (details && details.length > 0) {
          console.log(`[28] Found ${details.length} messages in conversation history`);
          conversationMessages = details.map(detail => ({
            content: detail.message_content,
            role: detail.sender === 'user' ? 'user' : 'assistant',
            timestamp: detail.sent_at,
            metadata: detail.metadata ? JSON.parse(detail.metadata) : {}
          }));
        } else {
          console.log('[28] No conversation history found in conversation_details');
        }
      } else if (messagesSchemaValid) {
        // Fallback to messages table if conversation_details is not available
        console.log('[27] Conversation_details invalid, trying messages table instead');
        const { data: messages } = await supabase
          .from('messages')
          .select('*')
          .order('sent_at', { ascending: true })
          .limit(10);
          
        if (messages && messages.length > 0) {
          console.log(`[28] Found ${messages.length} messages in history from messages table`);
          conversationMessages = messages.map(msg => ({
            content: msg.content,
            role: msg.message_type === 'user' ? 'user' : 'assistant',
            timestamp: msg.sent_at,
            metadata: msg.metadata ? JSON.parse(msg.metadata) : {}
          }));
        } else {
          console.log('[28] No conversation history found in messages table');
        }
      } else {
        console.log('[27] Both conversation tables invalid, using just current message');
      }
      
      // If we couldn't get history, just use the current message
      if (conversationMessages.length === 0) {
        console.log('[29] Using only current message as context');
        conversationMessages = [{
          content: message,
          role: 'user',
          timestamp: timestamp,
          metadata: {
            platform: platform || 'web-ui',
            patient_id: patient_id,
            is_test_mode: is_test_mode === true
          }
        }];
      }
      
      // Prepare input for the graph
      console.log('[30] Preparing graph API input');
      const graphInput: AICompanionState = {
        messages: conversationMessages.map(msg => ({
          content: msg.content,
          role: msg.role,
          metadata: {
            platform: platform || 'web-ui',
            user_id: patient_id,
            patient_id: patient_id,
            is_test_mode: is_test_mode === true
          }
        })),
        patient_id: patient_id,
        workflow: 'conversation'
      };
      
      // Check if NEXT_PUBLIC_API_BASE is set
      const apiBase = process.env.NEXT_PUBLIC_API_BASE;
      if (!apiBase) {
        console.warn('[31] NEXT_PUBLIC_API_BASE environment variable not set, using fallback response');
        useGraphAPI = false;
        throw new Error('API base URL not configured');
      }
      
      // Add timeout to fetch to avoid long waits
      console.log(`[31] Calling graph API at ${apiBase}/api/v1/conversation`);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      // Call the graph API endpoint
      try {
        const graphResponse = await fetch(
          `${apiBase}/api/v1/conversation`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(graphInput),
            signal: controller.signal
          }
        );
        
        clearTimeout(timeoutId);
        
        if (!graphResponse.ok) {
          console.error(`[32] Graph API error: ${graphResponse.status}`);
          throw new Error(`Graph API error: ${graphResponse.status}`);
        }
        
        const graphResult = await graphResponse.json();
        assistantResponse = graphResult.response || "I'm sorry, I couldn't process your request at this time.";
        console.log(`[33] Received response from graph API: "${assistantResponse.substring(0, 50)}${assistantResponse.length > 50 ? '...' : ''}"`);
      } catch (fetchError: any) {
        if (fetchError.name === 'AbortError') {
          console.warn('[ERROR] Graph API request timed out after 5 seconds');
        } else {
          console.error('[ERROR] Error calling graph API:', fetchError);
        }
        throw fetchError; // Re-throw to be caught by outer try/catch
      }
      
    } catch (error) {
      console.warn('[ERROR] Using fallback response due to error:', error);
      
      // Generate response based on message content for a more tailored experience
      console.log('[FALLBACK] Generating content-aware fallback response');
      if (message.toLowerCase().includes('hello') || 
          message.toLowerCase().includes('hi') || 
          message.toLowerCase().includes('hey')) {
        console.log('[FALLBACK] Detected greeting, using greeting response');
        assistantResponse = "Hello! I'm operating in test mode right now, but I'm collecting these conversations to improve our healthcare assistant.";
      } else if (message.toLowerCase().includes('help') || 
                message.toLowerCase().includes('can you')) {
        console.log('[FALLBACK] Detected help request, using help response');
        assistantResponse = "I understand you're looking for assistance. While I'm in test mode with limited capabilities right now, I'd normally be able to help with health-related questions and concerns.";
      } else if (message.toLowerCase().includes('symptom') || 
                message.toLowerCase().includes('pain') || 
                message.toLowerCase().includes('feel')) {
        console.log('[FALLBACK] Detected symptom mention, using symptom response');
        assistantResponse = "I notice you're mentioning something about your health. In normal operation, I'd be able to ask follow-up questions about your symptoms and provide relevant information.";
      } else if (message.toLowerCase().includes('appointment') || 
                message.toLowerCase().includes('schedule') || 
                message.toLowerCase().includes('book')) {
        console.log('[FALLBACK] Detected appointment request, using appointment response');
        assistantResponse = "I see you're interested in scheduling an appointment. The full system would help connect you with a healthcare provider.";
      } else {
        console.log('[FALLBACK] No specific pattern detected, using generic fallback');
        assistantResponse = getFallbackResponse();
      }
      console.log(`[FALLBACK] Using fallback response: "${assistantResponse.substring(0, 50)}${assistantResponse.length > 50 ? '...' : ''}"`);
    }
    
    // Store the assistant response in conversation_details
    console.log('[34] Storing assistant response');
    const assistantMessageId = uuidv4();
    const assistantTimestamp = new Date().toISOString();
    
    // Store in messages table if valid
    if (messagesSchemaValid) {
      try {
        console.log('[35] Inserting assistant response into messages table');
        await supabase
          .from('messages')
          .insert({
            id: assistantMessageId,
            patient_id: patient_id,
            content: assistantResponse,
            message_type: 'assistant',
            sent_at: assistantTimestamp,
            read_at: null, // Not read yet by patient
            priority: 'normal',
            metadata: JSON.stringify({
              platform: platform || 'web-ui',
              is_test_mode: is_test_mode === true,
              used_graph_api: useGraphAPI
            })
          });
        console.log('[36] Successfully stored assistant message');
      } catch (err) {
        console.warn('[ERROR] Error storing assistant message:', err);
      }
    } else {
      console.log('[35] Messages table invalid, skipping storage');
    }
    
    // Store in conversation_details to maintain relationship structure
    if (conversationDetailsSchemaValid) {
      try {
        console.log('[37] Inserting assistant response into conversation_details');
        await supabase
          .from('conversation_details')
          .insert({
            conversation_id: activeConversationId,
            message_content: assistantResponse,
            message_type: 'assistant',
            sent_at: assistantTimestamp,
            sender: 'assistant',
            metadata: JSON.stringify({
              platform: platform || 'web-ui',
              patient_id: patient_id,
              is_test_mode: is_test_mode === true,
              used_graph_api: useGraphAPI,
              message_id: assistantMessageId
            })
          });
        console.log('[38] Successfully stored assistant response in conversation_details');
      } catch (err) {
        console.warn('[ERROR] Error storing conversation details for assistant:', err);
      }
    } else {
      console.log('[37] Conversation_details table invalid, skipping storage');
    }
    
    // Return the response
    console.log('[39] Returning response to client');
    console.log('==================== END CHAT API JOURNEY ====================');
    return NextResponse.json({
      message: assistantResponse,
      conversation_id: activeConversationId
    });
    
  } catch (error: any) {
    console.error('[CRITICAL ERROR] Error in chat API:', error);
    
    // Even if everything fails, return a fallback response rather than an error
    console.log('[CRITICAL FALLBACK] Generating emergency response');
    const fallbackResponse = "I'm sorry, I encountered an issue processing your message. This is a test environment that helps us improve our system. Please try again later.";
    console.log('==================== END CHAT API JOURNEY (ERROR) ====================');
    return NextResponse.json({
      message: fallbackResponse,
      conversation_id: `error-${uuidv4()}`
    });
  }
} 