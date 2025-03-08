/**
 * Domain Models
 * Contains types for core business domain entities
 */

/**
 * Chat message types
 */
export enum MessageType {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
}

/**
 * Chat message structure
 */
export interface Message {
  id: string;
  type: MessageType;
  content: string;
  createdAt: string;
  metadata?: Record<string, unknown>;
}

/**
 * Chat conversation
 */
export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  userId: string;
}

/**
 * User preferences
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: boolean;
  textSize: 'small' | 'medium' | 'large';
}

/**
 * Analytics event
 */
export interface AnalyticsEvent {
  id: string;
  type: string;
  timestamp: string;
  userId?: string;
  properties: Record<string, unknown>;
}

/**
 * AI Assistant
 */
export interface Assistant {
  id: string;
  name: string;
  description: string;
  avatar?: string;
  capabilities: string[];
  isDefault?: boolean;
} 