# API Integration

## Overview

This document outlines the standard approach for integrating with backend API services in the web-ui frontend. We use a combination of custom hooks and service classes to create a clean separation of concerns and reusable API interaction patterns.

## Directory Structure

```
src/
├── lib/
│   └── api/
│       ├── client.ts             # Base API client configuration
│       ├── endpoints.ts          # API endpoint constants
│       ├── types.ts              # API request/response types
│       └── services/
│           ├── auth.service.ts   # Authentication-related API calls
│           ├── chat.service.ts   # Chat-related API calls
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

All API interactions should include proper error handling:

1. **Service Layer**: Transforms HTTP errors into ApiError instances
2. **Hook Layer**: Captures and exposes errors to components
3. **Component Layer**: Displays appropriate error messages to users

## Best Practices

1. Use TypeScript for all API interfaces and responses
2. Keep service functions small and focused on a single responsibility
3. Use custom hooks to manage loading/error states
4. Implement proper error handling at all levels
5. Maintain a consistent naming convention
6. Document expected request and response formats 