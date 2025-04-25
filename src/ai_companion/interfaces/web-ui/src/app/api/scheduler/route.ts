import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Helper function to get the API URL
const getApiUrl = () => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return apiUrl.endsWith('/') ? apiUrl : `${apiUrl}/`;
};

// Define proper types for the recurrence data
interface RecurrencePattern {
  type: string;
  interval: number;
  days?: number[];
  day?: number;
  minutes?: number;
}

interface ScheduleData {
  chatId: string;
  messageContent: string;
  scheduledTime: string;
  patientId?: string;
  recurrence?: {
    type: string;
    days?: number[];
    monthDay?: string;
    minutes?: string;
  };
  priority?: number;
  metadata?: any;
  id?: string;
}

interface ScheduleMessage {
  id: string;
  chatId: string | number;
  patientId?: string;
  messageContent: string;
  scheduledTime: string;
  status: string;
  recurrence?: any;
  createdAt: string;
  attempts?: number;
  priority: number;
  isRecurring: boolean;
}

// Define proper types for backend recurrence data
interface BackendRecurrenceData {
  type: string;
  days?: number[];
  day?: number;
  minutes?: number;
  interval?: number;
}

// Custom fetch with timeout
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeout = 10000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

// Convert frontend recurrence format to backend format
const convertFrontendRecurrenceToBackend = (recurrence: any): BackendRecurrenceData | null => {
  if (!recurrence || !recurrence.type) {
    return null;
  }
  
  const { type } = recurrence;
  const result: BackendRecurrenceData = {
    type,
    interval: 1
  };
  
  // Add type-specific fields
  if (type === 'weekly' && recurrence.days && Array.isArray(recurrence.days)) {
    result.days = recurrence.days;
  } else if (type === 'monthly' && recurrence.monthDay) {
    result.day = parseInt(recurrence.monthDay, 10);
  } else if (type === 'custom' && recurrence.minutes) {
    result.minutes = parseInt(recurrence.minutes, 10);
  }
  
  return result;
};

// Check if the scheduler is running
async function isSchedulerRunning(): Promise<boolean> {
  try {
    const apiUrl = getApiUrl();
    const response = await fetchWithTimeout(`${apiUrl}monitor/health/telegram-scheduler-status`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    }, 5000); // Short timeout for health check
    
    if (!response.ok) {
      return false;
    }
    
    const data = await response.json();
    return data.status === 'running';
  } catch (error) {
    console.error('Error checking scheduler status:', error);
    return false;
  }
}

// Function to fetch scheduled messages from backend
async function fetchScheduledMessages(patientId?: string): Promise<any[]> {
  try {
    // Directly query the database to get scheduled messages
    console.log('Attempting to fetch scheduled messages from backend');
    
    // Construct the URL with patient ID filter if provided
    let url = `${getApiUrl()}scheduler/messages`;
    
    // Add patient_id as query parameter if provided
    const params = new URLSearchParams();
    if (patientId) {
      params.append('patient_id', patientId);
    }
    
    // Add the params to the URL if there are any
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    console.log('Fetching from backend URL:', url);
    
    // Make request with extended timeout
    const response = await fetchWithTimeout(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    }, 20000); // Increase timeout to 20 seconds
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', response.status, errorText);
      throw new Error(`Backend API returned ${response.status}: ${errorText}`);
    }
    
    // Parse and log the response
    const data = await response.json();
    console.log('Received data from backend:', data);
    
    // Handle both array and object with messages property
    if (Array.isArray(data)) {
      return data;
    } else if (data && Array.isArray(data.messages)) {
      return data.messages;
    } else if (data && Array.isArray(data.schedules)) {
      return data.schedules;
    } else {
      console.warn('Unexpected response format:', data);
      return [];
    }
  } catch (error) {
    console.error('Error fetching scheduled messages:', error);
    throw error;
  }
}

// Create a direct client here to avoid "use server" directive issues
const createSupabaseClient = async () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Missing Supabase credentials');
  }
  
  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false
    }
  });
};

// Scheduled messages table name without schema prefix
const SCHEDULED_MESSAGES_TABLE = 'scheduled_messages';

// GET /api/scheduler
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const patientId = searchParams.get('patientId');
    
    console.log('GET /api/scheduler - Fetching scheduled messages', patientId ? `for patient ${patientId}` : 'for all patients');

    const supabase = await createSupabaseClient();
    
    // Build the query
    let query = supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .select('*');
    
    // Add filters if patient ID is provided
    if (patientId) {
      query = query.eq('patient_id', patientId);
    }
    
    // Order by scheduled_time
    query = query.order('scheduled_time', { ascending: false });
    
    // Execute the query
    const { data, error } = await query;
    
    if (error) {
      console.error('Error fetching scheduled messages:', error);
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }
    
    // Process the messages to ensure consistent format
    const messages = data?.map(msg => ({
      ...msg,
      // Ensure these properties exist with defaults if not present
      platform: msg.platform || 'telegram',
      status: msg.status || 'pending',
      priority: msg.priority || 5
    })) || [];
    
    console.log(`GET /api/scheduler - Returning ${messages.length} messages`);
    
    // Always return in a consistent format
    return NextResponse.json({
      messages: messages,
      count: messages.length
    });
  } catch (error: any) {
    console.error('Failed to fetch scheduled messages:', error);
    return NextResponse.json(
      { error: 'Failed to fetch scheduled messages: ' + error.message },
      { status: 500 }
    );
  }
}

// POST /api/scheduler
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { patientId, chatId, messageContent, scheduledTime, platform, priority, delivery_window_seconds, recurrence } = body;
    
    if (!patientId || !chatId || !messageContent || !scheduledTime) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }
    
    const supabase = await createSupabaseClient();
    
    // Create metadata object with platform data
    const metadata: Record<string, any> = {
      platform_data: {
        chat_id: chatId
      }
    };
    
    // Add recurrence to metadata if provided
    if (recurrence) {
      metadata.recurrence = recurrence;
    }
    
    // Build the message object
    const messageObject = {
      patient_id: patientId,
      message_content: messageContent,
      scheduled_time: scheduledTime,
      status: 'pending',
      platform: platform || 'telegram',
      priority: priority || 5,
      delivery_window_seconds: delivery_window_seconds || 60,
      metadata
    };
    
    // Insert the message
    const { data, error } = await supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .insert(messageObject)
      .select()
      .single();
    
    if (error) {
      console.error('Error creating scheduled message:', error);
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({
      success: true,
      messageData: data
    });
  } catch (error: any) {
    console.error('Failed to create scheduled message:', error);
    return NextResponse.json(
      { error: 'Failed to create scheduled message: ' + error.message },
      { status: 500 }
    );
  }
}

// PATCH /api/scheduler
export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json();
    const { id, ...updates } = body;
    
    if (!id) {
      return NextResponse.json(
        { error: 'Missing message ID' },
        { status: 400 }
      );
    }
    
    const supabase = await createSupabaseClient();
    
    // Process updates
    const updateObject: any = {};
    
    // Process direct fields
    if (updates.messageContent) updateObject.message_content = updates.messageContent;
    if (updates.scheduledTime) updateObject.scheduled_time = updates.scheduledTime;
    if (updates.status) updateObject.status = updates.status;
    if (updates.priority) updateObject.priority = updates.priority;
    
    // Process metadata updates if needed
    if (updates.chatId || updates.recurrence) {
      // First get the current metadata
      const { data: currentData, error: fetchError } = await supabase
        .from(SCHEDULED_MESSAGES_TABLE)
        .select('metadata')
        .eq('id', id)
        .single();
      
      if (fetchError) {
        return NextResponse.json(
          { error: fetchError.message },
          { status: 500 }
        );
      }
      
      // Update metadata
      const metadata = currentData?.metadata || {};
      
      if (updates.chatId) {
        metadata.platform_data = {
          ...(metadata.platform_data || {}),
          chat_id: updates.chatId
        };
      }
      
      if (updates.recurrence) {
        metadata.recurrence = updates.recurrence;
      }
      
      updateObject.metadata = metadata;
    }
    
    // Update the message
    const { data, error } = await supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .update(updateObject)
      .eq('id', id)
      .select()
      .single();
    
    if (error) {
      console.error('Error updating scheduled message:', error);
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({
      success: true,
      messageData: data
    });
  } catch (error: any) {
    console.error('Failed to update scheduled message:', error);
    return NextResponse.json(
      { error: 'Failed to update scheduled message: ' + error.message },
      { status: 500 }
    );
  }
}

// DELETE /api/scheduler?id={messageId}
export async function DELETE(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const id = searchParams.get('id');
    
    if (!id) {
      return NextResponse.json(
        { error: 'Missing message ID' },
        { status: 400 }
      );
    }
    
    const supabase = await createSupabaseClient();
    
    const { error } = await supabase
      .from(SCHEDULED_MESSAGES_TABLE)
      .update({ status: 'cancelled' })
      .eq('id', id);
    
    if (error) {
      console.error('Error cancelling scheduled message:', error);
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }
    
    return NextResponse.json({ success: true, id });
  } catch (error: any) {
    console.error('Failed to cancel scheduled message:', error);
    return NextResponse.json(
      { error: 'Failed to cancel scheduled message: ' + error.message },
      { status: 500 }
    );
  }
} 