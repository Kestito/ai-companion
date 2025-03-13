import { scheduleService } from '@/lib/api/services/schedule.service';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
  API_ENDPOINTS: {
    SCHEDULED_MESSAGES: '/api/scheduled-messages',
  },
}));

describe('ScheduleService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockScheduledMessage = {
    id: '123',
    recipientId: '+37061234567',
    platform: 'whatsapp',
    message: 'Test message',
    scheduledTime: '2023-08-15T09:00:00Z',
    status: 'pending',
    createdAt: '2023-08-14T12:00:00Z',
  };

  test('createScheduledMessage should call API with correct data', async () => {
    // Setup
    (apiClient.post as jest.Mock).mockResolvedValue(mockScheduledMessage);
    
    const requestData = {
      recipientId: '+37061234567',
      platform: 'whatsapp',
      message: 'Test message',
      scheduledTime: new Date('2023-08-15T09:00:00Z'),
    };
    
    // Execute
    const result = await scheduleService.createScheduledMessage(requestData);
    
    // Assert
    expect(apiClient.post).toHaveBeenCalledWith(
      '/api/scheduled-messages',
      {
        ...requestData,
        scheduledTime: '2023-08-15T09:00:00.000Z',
      }
    );
    expect(result).toEqual(mockScheduledMessage);
  });

  test('getScheduledMessages should return list of messages', async () => {
    // Setup
    (apiClient.get as jest.Mock).mockResolvedValue([mockScheduledMessage]);
    
    // Execute
    const result = await scheduleService.getScheduledMessages();
    
    // Assert
    expect(apiClient.get).toHaveBeenCalledWith('/api/scheduled-messages');
    expect(result).toEqual([mockScheduledMessage]);
  });

  test('cancelScheduledMessage should call API with correct ID', async () => {
    // Setup
    (apiClient.delete as jest.Mock).mockResolvedValue({ success: true });
    
    // Execute
    await scheduleService.cancelScheduledMessage('123');
    
    // Assert
    expect(apiClient.delete).toHaveBeenCalledWith('/api/scheduled-messages/123');
  });
}); 