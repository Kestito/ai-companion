import { getSupabaseClient, PUBLIC_SCHEMA } from '@/lib/supabase/client';

export interface Conversation {
  id: string;
  patient_id: string;
  created_at: string;
  updated_at: string;
  status: string;
  metadata?: Record<string, any>;
}

export interface ConversationDetail {
  id: string;
  conversation_id: string;
  content: string;
  role: string;
  created_at: string;
  metadata?: Record<string, any>;
}

/**
 * Fetches all conversations for a specific patient
 * @param patientId The ID of the patient
 * @returns An array of conversations
 */
export async function getConversationsByPatientId(patientId: string): Promise<Conversation[]> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from('conversations')
    .select('*')
    .eq('patient_id', patientId)
    .order('created_at', { ascending: false });
  
  if (error) {
    console.error('Error fetching conversations:', error);
    throw new Error(`Failed to fetch conversations: ${error.message}`);
  }
  
  return data as Conversation[];
}

/**
 * Fetches a specific conversation by its ID
 * @param conversationId The ID of the conversation
 * @returns The conversation details
 */
export async function getConversationById(conversationId: string): Promise<Conversation> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from('conversations')
    .select('*')
    .eq('id', conversationId)
    .single();
  
  if (error) {
    console.error('Error fetching conversation:', error);
    throw new Error(`Failed to fetch conversation: ${error.message}`);
  }
  
  return data as Conversation;
}

/**
 * Fetches all messages for a specific conversation
 * @param conversationId The ID of the conversation
 * @returns An array of conversation details (messages)
 */
export async function getConversationMessages(conversationId: string): Promise<ConversationDetail[]> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from('conversation_details')
    .select('*')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: true });
  
  if (error) {
    console.error('Error fetching conversation messages:', error);
    throw new Error(`Failed to fetch conversation messages: ${error.message}`);
  }
  
  return data as ConversationDetail[];
}

/**
 * Creates a new conversation for a patient
 * @param patientId The ID of the patient
 * @param metadata Optional metadata for the conversation
 * @returns The created conversation
 */
export async function createConversation(
  patientId: string, 
  metadata?: Record<string, any>
): Promise<Conversation> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from('conversations')
    .insert([
      { 
        patient_id: patientId,
        status: 'active',
        metadata
      }
    ])
    .select()
    .single();
  
  if (error) {
    console.error('Error creating conversation:', error);
    throw new Error(`Failed to create conversation: ${error.message}`);
  }
  
  return data as Conversation;
}

/**
 * Adds a new message to a conversation
 * @param conversationId The ID of the conversation
 * @param content The message content
 * @param role The role of the sender (user or assistant)
 * @param metadata Optional metadata for the message
 * @returns The created message
 */
export async function addMessageToConversation(
  conversationId: string,
  content: string,
  role: 'user' | 'assistant',
  metadata?: Record<string, any>
): Promise<ConversationDetail> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from('conversation_details')
    .insert([
      {
        conversation_id: conversationId,
        content,
        role,
        metadata
      }
    ])
    .select()
    .single();
  
  if (error) {
    console.error('Error adding message to conversation:', error);
    throw new Error(`Failed to add message to conversation: ${error.message}`);
  }
  
  // Update the conversation's updated_at timestamp
  await supabase
    .from('conversations')
    .update({ updated_at: new Date().toISOString() })
    .eq('id', conversationId);
  
  return data as ConversationDetail;
}

/**
 * Updates a conversation's status
 * @param conversationId The ID of the conversation 
 * @param status The new status
 * @returns The updated conversation
 */
export async function updateConversationStatus(
  conversationId: string,
  status: string
): Promise<Conversation> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from('conversations')
    .update({ status, updated_at: new Date().toISOString() })
    .eq('id', conversationId)
    .select()
    .single();
  
  if (error) {
    console.error('Error updating conversation status:', error);
    throw new Error(`Failed to update conversation status: ${error.message}`);
  }
  
  return data as Conversation;
} 