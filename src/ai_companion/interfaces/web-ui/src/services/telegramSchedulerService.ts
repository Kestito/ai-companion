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
    console.log('Received scheduled messages:', data.messages?.length || 0);
    return data.messages || [];
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
    
    console.log('Created schedule:', data.schedule);
    return data.schedule;
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
    
    console.log('Updated schedule:', data.schedule);
    return data.schedule;
  } catch (error) {
    console.error('Error updating scheduled message:', error);
    throw new Error('Failed to update scheduled message');
  }
}

// Send a scheduled message immediately
export async function sendScheduledMessageNow(id: string): Promise<void> {
  try {
    console.log('Sending scheduled message immediately:', id);
    await fetcher(`/api/telegram-scheduler/send-now`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ id }),
    });
    console.log('Successfully sent message');
  } catch (error) {
    console.error('Error sending scheduled message:', error);
    throw new Error('Failed to send scheduled message');
  }
} 