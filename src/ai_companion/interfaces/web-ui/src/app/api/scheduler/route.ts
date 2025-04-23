import { NextRequest, NextResponse } from 'next/server';

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
}

// Convert frontend format to backend format
const convertToBackendFormat = (data: ScheduleData) => {
  // Extract recurrence pattern if present
  let recurrencePattern: RecurrencePattern | null = null;
  if (data.recurrence) {
    const { type } = data.recurrence;
    
    recurrencePattern = {
      type,
      interval: 1
    };
    
    // Add type-specific fields
    if (type === 'weekly' && data.recurrence.days && Array.isArray(data.recurrence.days)) {
      recurrencePattern.days = data.recurrence.days;
    } else if (type === 'monthly') {
      recurrencePattern.day = parseInt(data.recurrence.monthDay || '1', 10);
    } else if (type === 'custom') {
      recurrencePattern.minutes = parseInt(data.recurrence.minutes || '60', 10);
    }
  }
  
  return {
    chat_id: parseInt(data.chatId, 10),
    message_content: data.messageContent,
    scheduled_time: data.scheduledTime,
    patient_id: data.patientId || null,
    recurrence_pattern: recurrencePattern,
    priority: data.priority || 1,
    metadata: data.metadata || {}
  };
};

// Convert backend format to frontend format
const convertToFrontendFormat = (data: any): ScheduleMessage => {
  // Create recurrence object if applicable
  let recurrence: any = null;
  if (data.metadata?.recurrence) {
    const metadata_recurrence = data.metadata.recurrence as BackendRecurrenceData;
    const recurType = metadata_recurrence.type;
    recurrence = {
      type: recurType
    };
    
    if (recurType === 'weekly' && metadata_recurrence.days) {
      recurrence.days = metadata_recurrence.days;
    } else if (recurType === 'monthly' && metadata_recurrence.day) {
      recurrence.monthDay = metadata_recurrence.day.toString();
    } else if (recurType === 'custom' && metadata_recurrence.minutes) {
      recurrence.minutes = metadata_recurrence.minutes.toString();
    }
  }
  
  return {
    id: data.id,
    chatId: data.chat_id,
    patientId: data.patient_id,
    messageContent: data.message_content,
    scheduledTime: data.scheduled_time,
    status: data.status,
    recurrence,
    createdAt: data.created_at,
    attempts: data.attempts,
    priority: data.priority,
    isRecurring: !!recurrence
  };
};

// GET handler to list scheduled messages
export async function GET(request: NextRequest) {
  console.log('API called: GET /api/scheduler');
  
  try {
    // Get query parameters
    const url = new URL(request.url);
    const patientId = url.searchParams.get('patientId');
    const chatId = url.searchParams.get('chatId');
    const status = url.searchParams.get('status');
    
    // Construct backend API URL
    let apiUrl = `${getApiUrl()}scheduler/messages`;
    const params = new URLSearchParams();
    
    if (chatId) {
      params.append('chat_id', chatId);
    }
    
    if (status) {
      params.append('status', status);
    }
    
    if (params.toString()) {
      apiUrl += `?${params.toString()}`;
    }
    
    console.log('Fetching from backend URL:', apiUrl);
    
    // Make request to backend
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      console.error('Backend API error:', response.status, response.statusText);
      return NextResponse.json(
        { error: `Backend API returned ${response.status}: ${response.statusText}` },
        { status: response.status }
      );
    }
    
    // Parse response
    const data = await response.json();
    console.log('Received scheduled messages from backend:', data.length);
    
    // Convert data to frontend format
    const messages = data.map(convertToFrontendFormat);
    
    // Filter by patientId if requested
    const filteredMessages = patientId 
      ? messages.filter((msg: ScheduleMessage) => msg.patientId === patientId)
      : messages;
    
    return NextResponse.json({ messages: filteredMessages });
  } catch (error) {
    console.error('Error processing request:', error);
    return NextResponse.json(
      { error: 'Failed to fetch scheduled messages' },
      { status: 500 }
    );
  }
}

// POST handler to create a scheduled message
export async function POST(request: NextRequest) {
  console.log('API called: POST /api/scheduler');
  
  try {
    // Parse request body
    const requestData = await request.json();
    console.log('Request data:', requestData);
    
    // Convert to backend format
    const backendData = convertToBackendFormat(requestData);
    console.log('Converted to backend format:', backendData);
    
    // Make request to backend
    const response = await fetch(`${getApiUrl()}scheduler/messages`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(backendData)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', response.status, errorText);
      return NextResponse.json(
        { error: `Backend API returned ${response.status}: ${errorText}` },
        { status: response.status }
      );
    }
    
    // Get the created message ID
    const messageId = await response.json();
    
    // Fetch the complete message details
    const getResponse = await fetch(`${getApiUrl()}scheduler/messages/${messageId}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    if (!getResponse.ok) {
      console.error('Failed to fetch created message details:', getResponse.status);
      return NextResponse.json(
        { id: messageId, success: true },
        { status: 201 }
      );
    }
    
    // Parse and return the created message
    const messageData = await getResponse.json();
    const frontendData = convertToFrontendFormat(messageData);
    
    return NextResponse.json(
      { messageData: frontendData, id: messageId, success: true },
      { status: 201 }
    );
  } catch (error) {
    console.error('Error processing request:', error);
    return NextResponse.json(
      { error: `Failed to create scheduled message: ${(error as Error).message}` },
      { status: 500 }
    );
  }
}

// DELETE handler to cancel a scheduled message
export async function DELETE(request: NextRequest) {
  console.log('API called: DELETE /api/scheduler');
  
  try {
    // Get query parameters
    const url = new URL(request.url);
    const messageId = url.searchParams.get('id');
    
    if (!messageId) {
      return NextResponse.json(
        { error: 'Message ID is required' },
        { status: 400 }
      );
    }
    
    // Make request to backend
    const response = await fetch(`${getApiUrl()}scheduler/messages/${messageId}`, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      console.error('Backend API error:', response.status, response.statusText);
      return NextResponse.json(
        { error: `Backend API returned ${response.status}: ${response.statusText}` },
        { status: response.status }
      );
    }
    
    // Return success
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error processing request:', error);
    return NextResponse.json(
      { error: 'Failed to cancel scheduled message' },
      { status: 500 }
    );
  }
}

// PATCH handler to update a scheduled message
export async function PATCH(request: NextRequest) {
  console.log('API called: PATCH /api/scheduler');
  
  try {
    // Parse request body
    const requestData = await request.json();
    console.log('Request data:', requestData);
    
    if (!requestData.id) {
      return NextResponse.json(
        { error: 'Message ID is required' },
        { status: 400 }
      );
    }
    
    // Convert to backend format
    const backendData = convertToBackendFormat(requestData);
    
    // Make request to backend
    const response = await fetch(`${getApiUrl()}scheduler/messages/${requestData.id}`, {
      method: 'PUT',  // FastAPI doesn't support PATCH directly
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(backendData)
    });
    
    if (!response.ok) {
      console.error('Backend API error:', response.status, response.statusText);
      return NextResponse.json(
        { error: `Backend API returned ${response.status}: ${response.statusText}` },
        { status: response.status }
      );
    }
    
    // Get the updated message
    const messageId = requestData.id;
    const getResponse = await fetch(`${getApiUrl()}scheduler/messages/${messageId}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    if (!getResponse.ok) {
      console.error('Failed to fetch updated message details:', getResponse.status);
      return NextResponse.json({ success: true });
    }
    
    // Parse and return the updated message
    const messageData = await getResponse.json();
    const frontendData = convertToFrontendFormat(messageData);
    
    return NextResponse.json({ messageData: frontendData, success: true });
  } catch (error) {
    console.error('Error processing request:', error);
    return NextResponse.json(
      { error: 'Failed to update scheduled message' },
      { status: 500 }
    );
  }
} 