import { useState, useCallback, useEffect } from 'react';
import chatService from '@/lib/api/services/chat.service';
import { Chat, ChatMessage, ChatHistory } from '@/lib/api/types';

interface UseChatParams {
  chatId?: string;
  initialLoad?: boolean;
}

interface UseChatReturn {
  chat: Chat | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: Error | null;
  sendMessage: (content: string, metadata?: Record<string, any>) => Promise<ChatMessage | null>;
  refreshChat: () => Promise<void>;
  createChat: (name: string, initialMessage?: string) => Promise<Chat | null>;
  deleteChat: () => Promise<boolean>;
}

/**
 * Hook for managing chat operations
 * 
 * @param params - Chat parameters
 * @returns Chat state and operations
 */
export function useChat({ chatId, initialLoad = true }: UseChatParams = {}): UseChatReturn {
  const [chat, setChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [isCreating, setIsCreating] = useState<boolean>(false);

  // Load chat history when chatId changes or on mount if initialLoad is true
  useEffect(() => {
    if (chatId && initialLoad) {
      refreshChat();
    }
  }, [chatId, initialLoad]);

  /**
   * Refresh chat data and messages
   */
  const refreshChat = useCallback(async () => {
    if (!chatId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const history = await chatService.getChatHistory(chatId);
      setChat(history.chat);
      setMessages(history.messages);
    } catch (err) {
      console.error('Error fetching chat history:', err);
      setError(err instanceof Error ? err : new Error('Failed to load chat history'));
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);

  /**
   * Send a message in the current chat
   * 
   * @param content - Message content
   * @param metadata - Optional message metadata
   * @returns The sent message or null if error
   */
  const sendMessage = useCallback(async (
    content: string, 
    metadata?: Record<string, any>
  ): Promise<ChatMessage | null> => {
    if (!chatId) {
      setError(new Error('No active chat'));
      return null;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const message = await chatService.sendMessage(chatId, content, metadata);
      
      // Update messages in state
      setMessages(prev => [...prev, message]);
      
      return message;
    } catch (err) {
      console.error('Error sending message:', err);
      setError(err instanceof Error ? err : new Error('Failed to send message'));
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);

  /**
   * Create a new chat
   * 
   * @param name - The name of the chat
   * @param initialMessage - Optional initial message to send
   * @returns The created chat
   */
  const createChat = useCallback(
    async (name: string, initialMessage?: string): Promise<Chat> => {
      setIsCreating(true);
      setError(null);

      try {
        // Create the chat
        const newChat = await chatService.createChat({
          name
        });

        // If there's an initial message, send it
        if (initialMessage) {
          await chatService.sendMessage(newChat.id, initialMessage);
        }

        return newChat;
      } catch (err) {
        console.error('Error creating chat:', err);
        setError(err instanceof Error ? new Error(err.message) : new Error('Failed to create chat'));
        throw err;
      } finally {
        setIsCreating(false);
      }
    },
    [setIsCreating, setError]
  );

  /**
   * Delete the current chat
   * 
   * @returns Success status
   */
  const deleteChat = useCallback(async (): Promise<boolean> => {
    if (!chatId) {
      setError(new Error('No active chat'));
      return false;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await chatService.deleteChat(chatId);
      return result.success;
    } catch (err) {
      console.error('Error deleting chat:', err);
      setError(err instanceof Error ? err : new Error('Failed to delete chat'));
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);

  return {
    chat,
    messages,
    isLoading,
    error,
    sendMessage,
    refreshChat,
    createChat,
    deleteChat
  };
}

export default useChat; 