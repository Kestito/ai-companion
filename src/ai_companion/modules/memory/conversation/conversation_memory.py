"""
Conversation Memory Manager for AI Companion.

This module provides functionality for storing and retrieving complete conversation histories
with support for different channels and media types.
"""
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ai_companion.settings import settings
from ai_companion.utils.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class MediaType(str, Enum):
    """Media types supported in conversation messages."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"

class ChannelType(str, Enum):
    """Channel types for conversations."""
    DIRECT = "direct"
    GROUP = "group"
    BROADCAST = "broadcast"

class MessageWithMedia(BaseModel):
    """Message model with media support."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    type: str  # 'human' or 'ai'
    media_type: MediaType = MediaType.TEXT
    media_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationMemory(BaseModel):
    """Model for conversation memory entries."""
    id: Optional[str] = None
    user_id: str
    session_id: str
    interface_type: str
    channel: ChannelType = ChannelType.DIRECT
    conversation_history: List[MessageWithMedia] = Field(default_factory=list)
    raw_conversation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None

class ConversationMemoryManager:
    """Manager for conversation memory operations."""
    
    def __init__(self):
        """Initialize the conversation memory manager."""
        self.supabase = get_supabase_client()
        self.schema = "USERS"  # Use USERS schema for all operations
    
    async def store_conversation(
        self,
        user_id: str,
        session_id: str,
        interface_type: str,
        messages: List[Union[Dict[str, Any], MessageWithMedia]],
        channel: ChannelType = ChannelType.DIRECT,
        metadata: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None
    ) -> str:
        """
        Store a conversation in the database.
        
        Args:
            user_id: The user ID
            session_id: The session ID
            interface_type: The interface type (e.g., 'whatsapp', 'telegram')
            messages: List of messages to store
            channel: The conversation channel type
            metadata: Additional metadata for the conversation
            summary: Optional conversation summary
            
        Returns:
            The conversation ID
        """
        # Process messages to ensure they're in the correct format
        processed_messages = []
        media_items = []
        
        for msg in messages:
            if isinstance(msg, dict):
                # Convert dict to MessageWithMedia
                if "media_type" not in msg:
                    msg["media_type"] = MediaType.TEXT
                message = MessageWithMedia(**msg)
            else:
                message = msg
            
            processed_messages.append(message.model_dump())
            
            # Track media items for separate storage
            if message.media_type != MediaType.TEXT and message.media_url:
                media_items.append({
                    "message_id": message.message_id,
                    "media_type": message.media_type,
                    "media_url": message.media_url,
                    "media_metadata": message.metadata.get("media_metadata", {})
                })
        
        # Create raw conversation log
        raw_conversation = "\n".join([
            f"[{msg.timestamp.isoformat()}] {msg.type}: {msg.content}"
            for msg in processed_messages
        ])
        
        # Check if conversation already exists
        existing_conversation = await self.supabase.table(f"{self.schema}.conversation_memory") \
            .select("id") \
            .eq("user_id", user_id) \
            .eq("session_id", session_id) \
            .eq("interface_type", interface_type) \
            .eq("channel", channel) \
            .execute()
        
        conversation_data = {
            "user_id": user_id,
            "session_id": session_id,
            "interface_type": interface_type,
            "channel": channel,
            "conversation_history": processed_messages,
            "raw_conversation": raw_conversation,
            "metadata": metadata or {},
            "summary": summary,
            "updated_at": datetime.now().isoformat(),
            "last_active_at": datetime.now().isoformat()
        }
        
        if existing_conversation.data and len(existing_conversation.data) > 0:
            # Update existing conversation
            conversation_id = existing_conversation.data[0]["id"]
            await self.supabase.table(f"{self.schema}.conversation_memory") \
                .update(conversation_data) \
                .eq("id", conversation_id) \
                .execute()
            logger.info(f"Updated existing conversation: {conversation_id}")
        else:
            # Create new conversation
            conversation_data["created_at"] = datetime.now().isoformat()
            result = await self.supabase.table(f"{self.schema}.conversation_memory") \
                .insert(conversation_data) \
                .execute()
            conversation_id = result.data[0]["id"]
            logger.info(f"Created new conversation: {conversation_id}")
        
        # Store media items
        if media_items:
            for media_item in media_items:
                await self.supabase.table(f"{self.schema}.conversation_media") \
                    .insert({
                        "conversation_id": conversation_id,
                        "message_id": media_item["message_id"],
                        "media_type": media_item["media_type"],
                        "media_url": media_item["media_url"],
                        "media_metadata": media_item.get("media_metadata", {})
                    }) \
                    .execute()
            logger.info(f"Stored {len(media_items)} media items for conversation: {conversation_id}")
        
        return conversation_id
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationMemory]:
        """
        Retrieve a conversation by ID.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            The conversation memory object or None if not found
        """
        result = await self.supabase.table(f"{self.schema}.conversation_memory") \
            .select("*") \
            .eq("id", conversation_id) \
            .execute()
        
        if not result.data:
            return None
        
        conversation_data = result.data[0]
        
        # Get media items
        media_result = await self.supabase.table(f"{self.schema}.conversation_media") \
            .select("*") \
            .eq("conversation_id", conversation_id) \
            .execute()
        
        # Add media information to messages
        if media_result.data:
            media_by_message_id = {item["message_id"]: item for item in media_result.data}
            
            for message in conversation_data["conversation_history"]:
                if message["message_id"] in media_by_message_id:
                    media_item = media_by_message_id[message["message_id"]]
                    message["media_type"] = media_item["media_type"]
                    message["media_url"] = media_item["media_url"]
                    if "media_metadata" in media_item and media_item["media_metadata"]:
                        if "metadata" not in message:
                            message["metadata"] = {}
                        message["metadata"]["media_metadata"] = media_item["media_metadata"]
        
        return ConversationMemory(**conversation_data)
    
    async def get_conversations_by_user(
        self, 
        user_id: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[ConversationMemory]:
        """
        Retrieve conversations for a user.
        
        Args:
            user_id: The user ID
            limit: Maximum number of conversations to return
            offset: Offset for pagination
            
        Returns:
            List of conversation memory objects
        """
        result = await self.supabase.table(f"{self.schema}.conversation_memory") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("last_active_at", desc=True) \
            .limit(limit) \
            .offset(offset) \
            .execute()
        
        return [ConversationMemory(**item) for item in result.data]
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Media items will be deleted automatically due to CASCADE constraint
            await self.supabase.table(f"{self.schema}.conversation_memory") \
                .delete() \
                .eq("id", conversation_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False
    
    async def update_summary(self, conversation_id: str, summary: str) -> bool:
        """
        Update the summary for a conversation.
        
        Args:
            conversation_id: The conversation ID
            summary: The new summary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.supabase.table(f"{self.schema}.conversation_memory") \
                .update({"summary": summary}) \
                .eq("id", conversation_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating summary for conversation {conversation_id}: {e}")
            return False

# Helper functions for creating messages

def create_text_message(
    content: str, 
    sender_type: str, 
    metadata: Optional[Dict[str, Any]] = None
) -> MessageWithMedia:
    """
    Create a text message.
    
    Args:
        content: The message content
        sender_type: 'human' or 'ai'
        metadata: Additional metadata
        
    Returns:
        A MessageWithMedia object
    """
    return MessageWithMedia(
        content=content,
        type=sender_type,
        media_type=MediaType.TEXT,
        metadata=metadata or {}
    )

def create_image_message(
    content: str,
    sender_type: str,
    image_url: str,
    thumbnail_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> MessageWithMedia:
    """
    Create an image message.
    
    Args:
        content: The message content
        sender_type: 'human' or 'ai'
        image_url: URL to the image
        thumbnail_url: Optional thumbnail URL
        metadata: Additional metadata
        
    Returns:
        A MessageWithMedia object
    """
    meta = metadata or {}
    meta["media_metadata"] = {
        "thumbnail_url": thumbnail_url
    }
    
    return MessageWithMedia(
        content=content,
        type=sender_type,
        media_type=MediaType.IMAGE,
        media_url=image_url,
        metadata=meta
    )

def create_audio_message(
    content: str,
    sender_type: str,
    audio_url: str,
    duration_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> MessageWithMedia:
    """
    Create an audio message.
    
    Args:
        content: The message content
        sender_type: 'human' or 'ai'
        audio_url: URL to the audio file
        duration_seconds: Optional duration in seconds
        metadata: Additional metadata
        
    Returns:
        A MessageWithMedia object
    """
    meta = metadata or {}
    meta["media_metadata"] = {
        "duration_seconds": duration_seconds
    }
    
    return MessageWithMedia(
        content=content,
        type=sender_type,
        media_type=MediaType.AUDIO,
        media_url=audio_url,
        metadata=meta
    )

def create_video_message(
    content: str,
    sender_type: str,
    video_url: str,
    thumbnail_url: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> MessageWithMedia:
    """
    Create a video message.
    
    Args:
        content: The message content
        sender_type: 'human' or 'ai'
        video_url: URL to the video file
        thumbnail_url: Optional thumbnail URL
        duration_seconds: Optional duration in seconds
        metadata: Additional metadata
        
    Returns:
        A MessageWithMedia object
    """
    meta = metadata or {}
    meta["media_metadata"] = {
        "thumbnail_url": thumbnail_url,
        "duration_seconds": duration_seconds
    }
    
    return MessageWithMedia(
        content=content,
        type=sender_type,
        media_type=MediaType.VIDEO,
        media_url=video_url,
        metadata=meta
    )

def create_document_message(
    content: str,
    sender_type: str,
    document_url: str,
    file_name: Optional[str] = None,
    file_size: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> MessageWithMedia:
    """
    Create a document message.
    
    Args:
        content: The message content
        sender_type: 'human' or 'ai'
        document_url: URL to the document
        file_name: Optional file name
        file_size: Optional file size in bytes
        metadata: Additional metadata
        
    Returns:
        A MessageWithMedia object
    """
    meta = metadata or {}
    meta["media_metadata"] = {
        "file_name": file_name,
        "file_size": file_size
    }
    
    return MessageWithMedia(
        content=content,
        type=sender_type,
        media_type=MediaType.DOCUMENT,
        media_url=document_url,
        metadata=meta
    )

def get_conversation_memory_manager() -> ConversationMemoryManager:
    """
    Get a conversation memory manager instance.
    
    Returns:
        A ConversationMemoryManager instance
    """
    return ConversationMemoryManager() 