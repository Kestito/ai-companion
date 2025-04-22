import { fetcher } from '@/lib/fetcher';

export interface ScheduledMessage {
  id: string;
  patient_id: string;
  message_content: string;
  scheduled_time: string;
  status: 'pending' | 'sent' | 'failed' | 'cancelled';
  recurrence?: {
    type: 'daily' | 'weekly' | 'monthly';
    days?: number[];
    time?: string;
  } | null;
  created_at: string;
}

export interface ScheduleInput {
  patientId: string;
  messageContent: string;
  scheduledTime: string;
  recurrence?: {
    type: 'daily' | 'weekly' | 'monthly';
    days?: number[];
    time?: string;
  };
}

// Fetch all scheduled messages
export async function getScheduledMessages(patientId?: string): Promise<ScheduledMessage[]> {
  try {
    console.log('Fetching scheduled messages', patientId ? `for patient ${patientId}` : 'for all patients');
    const url = patientId 
      ? `/api/telegram-scheduler?patientId=${encodeURIComponent(patientId)}`
      : '/api/telegram-scheduler';
    
    const data = await fetcher(url);
    console.log('Raw response data:', data);
    console.log('Received scheduled messages:', data.messages?.length || 0);
    
    // Check both messages and schedules properties
    if (data.messages) {
      console.log('Using data.messages');
      return data.messages;
    } else if (data.schedules) {
      console.log('Using data.schedules');
      return data.schedules;
    } else {
      console.log('No messages or schedules found in response');
      return [];
    }
  } catch (error) {
    console.error('Error fetching scheduled messages:', error);
    throw new Error('Failed to fetch scheduled messages');
  }
}

// Create a new scheduled message
export async function createScheduledMessage(schedule: ScheduleInput): Promise<ScheduledMessage> {
  try {
    console.log('Creating new scheduled message:', schedule);
    const data = await fetcher('/api/telegram-scheduler', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(schedule),
    });
    
    console.log('Response from create schedule:', data);
    
    // Check for both messageData (new format) and schedule (old format)
    if (data.messageData) {
      console.log('Using data.messageData');
      return data.messageData;
    } else if (data.schedule) {
      console.log('Using data.schedule');
      return data.schedule;
    } else {
      console.error('No message data found in response');
      throw new Error('No message data found in response');
    }
  } catch (error) {
    console.error('Error creating scheduled message:', error);
    throw new Error('Failed to create scheduled message');
  }
}

// Cancel a scheduled message
export async function cancelScheduledMessage(id: string): Promise<void> {
  try {
    console.log('Cancelling scheduled message:', id);
    await fetcher(`/api/telegram-scheduler?id=${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
    console.log('Successfully cancelled message');
  } catch (error) {
    console.error('Error cancelling scheduled message:', error);
    throw new Error('Failed to cancel scheduled message');
  }
}

// Update a scheduled message
export async function updateScheduledMessage(
  id: string, 
  updates: Partial<Omit<ScheduleInput, 'patientId'>> & { status?: string }
): Promise<ScheduledMessage> {
  try {
    console.log('Updating scheduled message:', id, updates);
    const data = await fetcher('/api/telegram-scheduler', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ id, ...updates }),
    });
    
    console.log('Response from update schedule:', data);
    
    // Check for both messageData (new format) and schedule (old format)
    if (data.messageData) {
      console.log('Using data.messageData');
      return data.messageData;
    } else if (data.schedule) {
      console.log('Using data.schedule');
      return data.schedule;
    } else {
      console.error('No message data found in response');
      throw new Error('No message data found in response');
    }
  } catch (error) {
    console.error('Error updating scheduled message:', error);
    throw new Error('Failed to update scheduled message');
  }
}

// Send a scheduled message immediately
export async function sendScheduledMessageNow(id: string): Promise<void> {
  try {
    console.log('Sending scheduled message immediately:', id);
    const data = await fetcher(`/api/telegram-scheduler/send-now`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ id }),
    });
    
    console.log('Send immediate response:', data);
    
    if (!data.success) {
      throw new Error(data.error || 'Failed to send message immediately');
    }
    
    console.log('Successfully sent message');
  } catch (error) {
    console.error('Error sending scheduled message:', error);
    throw new Error('Failed to send scheduled message');
  }
} 