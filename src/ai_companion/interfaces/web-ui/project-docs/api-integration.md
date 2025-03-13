# API Integration

## Overview

This document outlines the standard approach for integrating with backend API services in the web-ui frontend. We use a combination of custom hooks and service classes to create a clean separation of concerns and reusable API interaction patterns.

## Recommended API Structure

Our API structure follows a clean separation between:

1. **API Routes** in `/src/ai_companion/interfaces/web-ui/src/app/api/` 
   - These handle HTTP requests and interact with the database
   - Implement RESTful endpoints (GET, POST, PUT, DELETE)
   - Handle authentication and authorization
   - Perform data validation
   - Return standardized responses

2. **API Services** in `/src/ai_companion/interfaces/web-ui/src/lib/api/services/` 
   - These provide a clean interface for components to interact with the API
   - Abstract away HTTP request details
   - Handle data transformation between frontend and API
   - Provide type safety with TypeScript interfaces
   - Centralize error handling

This separation provides several benefits:
- Better security by keeping database interactions server-side
- Improved maintainability with clear separation of concerns
- Enhanced flexibility to change the underlying data source without affecting components
- Consistent error handling and response formatting

## Directory Structure

```
src/
├── app/
│   └── api/                      # Next.js API Routes (server-side)
│       ├── scheduled-checks/     # Scheduled checks API endpoints
│       │   ├── route.ts          # GET/POST handlers for collection
│       │   └── [id]/             # Dynamic route for individual items
│       │       └── route.ts      # GET/PUT/DELETE handlers for item
│       └── scheduled-messages/   # Scheduled messages API endpoints
│           ├── route.ts
│           └── [id]/
│               └── route.ts
├── lib/
│   └── api/
│       ├── client.ts             # Base API client configuration
│       ├── endpoints.ts          # API endpoint constants
│       ├── types.ts              # API request/response types
│       └── services/             # Client-side service layer
│           ├── auth.service.ts   # Authentication-related API calls
│           ├── chat.service.ts   # Chat-related API calls
│           ├── scheduledChecks.service.ts # Scheduled checks API calls
│           └── user.service.ts   # User-related API calls
├── hooks/
│   └── api/
│       ├── useAuth.ts            # Authentication hooks
│       ├── useChat.ts            # Chat interaction hooks
│       └── useUser.ts            # User data hooks
```

## API Client

The base API client provides consistent error handling, authentication, and request formatting:

```typescript
// lib/api/client.ts
import { getSupabaseClient } from '@/src/lib/supabase/client';

export class ApiError extends Error {
  status: number;
  data?: any;
  
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

export const apiClient = {
  async get<T>(url: string, options?: RequestInit): Promise<T> {
    const supabase = getSupabaseClient();
    const { data: session } = await supabase.auth.getSession();
    const token = session?.session?.access_token;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...(options?.headers || {})
      },
      ...options
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(
        error.message || 'Failed to fetch data',
        response.status,
        error
      );
    }
    
    return await response.json();
  },
  
  async post<T>(url: string, body: any, options?: RequestInit): Promise<T> {
    const supabase = getSupabaseClient();
    const { data: session } = await supabase.auth.getSession();
    const token = session?.session?.access_token;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...(options?.headers || {})
      },
      body: JSON.stringify(body),
      ...options
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(
        error.message || 'Failed to post data',
        response.status,
        error
      );
    }
    
    return await response.json();
  },
  
  // Similar implementations for put, delete, etc.
};
```

## Service Layer

Services handle specific API interactions and transform data:

```typescript
// lib/api/services/chat.service.ts
import { apiClient } from '../client';
import { API_ENDPOINTS } from '../endpoints';
import { 
  ChatMessage, 
  SendMessageRequest, 
  ChatHistory 
} from '../types';

export const chatService = {
  async getChatHistory(chatId: string): Promise<ChatHistory> {
    return apiClient.get<ChatHistory>(
      `${API_ENDPOINTS.CHAT}/${chatId}/history`
    );
  },
  
  async sendMessage(request: SendMessageRequest): Promise<ChatMessage> {
    return apiClient.post<ChatMessage>(
      API_ENDPOINTS.CHAT_MESSAGES,
      request
    );
  },
  
  async getChatList(): Promise<{ id: string; name: string; lastMessage: string }[]> {
    return apiClient.get<{ id: string; name: string; lastMessage: string }[]>(
      API_ENDPOINTS.CHAT_LIST
    );
  }
};
```

## Custom Hooks

Hooks provide React components with access to API functionality:

```typescript
// hooks/api/useChat.ts
import { useState, useCallback } from 'react';
import { chatService } from '@/src/lib/api/services/chat.service';
import { ChatMessage, SendMessageRequest, ChatHistory } from '@/src/lib/api/types';

export function useChat(chatId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const fetchChatHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const history = await chatService.getChatHistory(chatId);
      setMessages(history.messages);
      return history;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch chat history'));
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);
  
  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const request: SendMessageRequest = {
        chatId,
        content,
        timestamp: new Date().toISOString()
      };
      
      const newMessage = await chatService.sendMessage(request);
      
      setMessages(prev => [...prev, newMessage]);
      return newMessage;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to send message'));
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);
  
  return {
    messages,
    isLoading,
    error,
    fetchChatHistory,
    sendMessage
  };
}
```

## Usage Example

Example of using the API hooks in a component:

```tsx
import { useChat } from '@/src/hooks/api/useChat';

export const ChatComponent = ({ chatId }: { chatId: string }) => {
  const { 
    messages, 
    isLoading, 
    error, 
    fetchChatHistory, 
    sendMessage 
  } = useChat(chatId);
  
  useEffect(() => {
    fetchChatHistory();
  }, [fetchChatHistory]);
  
  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
  };
  
  if (isLoading && messages.length === 0) {
    return <div>Loading chat...</div>;
  }
  
  if (error && messages.length === 0) {
    return <div>Error: {error.message}</div>;
  }
  
  return (
    <div>
      {messages.map((message) => (
        <div key={message.id}>{message.content}</div>
      ))}
      <MessageInput onSend={handleSendMessage} />
    </div>
  );
};
```

## Error Handling

1. **API Layer**: Returns appropriate HTTP status codes and error messages
2. **Service Layer**: Transforms API errors into application-specific errors
3. **Component Layer**: Displays appropriate error messages to users

## Best Practices

1. Use TypeScript for all API interfaces and responses
2. Keep service functions small and focused on a single responsibility
3. Use custom hooks to manage loading/error states
4. Implement proper error handling at all levels
5. Maintain a consistent naming convention
6. Document expected request and response formats 

## Migration from Direct Database Access

### Previous Approach: Direct Supabase Access

Previously, some parts of the application used direct Supabase client calls from components or service files:

```typescript
// Old approach in patientService.ts
export async function fetchScheduledChecks(patientId: string): Promise<ScheduledCheck[]> {
  const supabase = getSupabaseClient();
  try {
    const { data, error } = await supabase
      .from('scheduled_checks')
      .select('*')
      .eq('patient_id', patientId)
      .order('next_scheduled', { ascending: true });
    
    if (error) {
      throw error;
    }
    
    return (data || []).map((check) => ({
      id: check.id,
      title: check.title,
      // ... mapping other fields
    }));
  } catch (err) {
    console.error('Error fetching scheduled checks:', err);
    return [];
  }
}
```

### New Approach: API Service Layer

The recommended approach is to use the API service layer that interacts with Next.js API routes:

1. **API Route (Server-side)**:
```typescript
// app/api/scheduled-checks/route.ts
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const patientId = searchParams.get('patientId');
    
    if (!patientId) {
      return NextResponse.json(
        { error: 'Patient ID is required' },
        { status: 400 }
      );
    }
    
    const supabase = createClient();
    
    const { data, error } = await supabase
      .from('scheduled_checks')
      .select('*')
      .eq('patient_id', patientId)
      .order('next_scheduled', { ascending: true });
    
    if (error) {
      console.error('Error fetching scheduled checks:', error);
      return NextResponse.json(
        { error: 'Failed to fetch scheduled checks' },
        { status: 500 }
      );
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in scheduled checks API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

2. **API Service (Client-side)**:
```typescript
// lib/api/services/scheduledChecks.service.ts
export async function fetchScheduledChecks(patientId: string): Promise<ScheduledCheck[]> {
  try {
    const response = await fetch(API_ENDPOINTS.SCHEDULED_CHECKS.BY_PATIENT(patientId));
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to fetch scheduled checks');
    }
    
    const data = await response.json();
    
    return (data || []).map((check: any) => ({
      id: check.id,
      title: check.title,
      // ... mapping other fields
    }));
  } catch (err) {
    console.error('Error fetching scheduled checks:', err);
    return [];
  }
}
```

3. **Component Usage**:
```typescript
import { scheduledChecksService } from '@/lib/api';

function ScheduledChecksTab({ patientId }: { patientId: string }) {
  const [scheduledChecks, setScheduledChecks] = useState<ScheduledCheck[]>([]);
  
  useEffect(() => {
    const loadScheduledChecks = async () => {
      const data = await scheduledChecksService.fetchScheduledChecks(patientId);
      setScheduledChecks(data);
    };
    
    loadScheduledChecks();
  }, [patientId]);
  
  // ... rest of component
}
```

### Benefits of the New Approach

1. **Security**: Database credentials are only used server-side
2. **Separation of Concerns**: Clear distinction between data access and UI logic
3. **Maintainability**: Easier to update database schema without affecting components
4. **Consistency**: Standardized error handling and response formats
5. **Scalability**: Better support for caching, middleware, and other API features

When implementing new features or refactoring existing ones, always prefer the API service approach over direct database access. 