"""
Memory caching module for efficient conversation history retrieval.

This module provides a tiered in-memory LRU cache for storing recent conversation
messages to minimize database calls and improve response time.
"""

import asyncio
import logging
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class MemoryCache:
    """
    Enhanced LRU cache with tiered structure for storing recent conversation messages.
    
    Provides fast in-memory access to recent conversations with
    automatic expiration, session-based indexing, and multiple caching layers:
    - Hot cache: Most frequently accessed sessions (fastest access)
    - Main cache: Regular LRU cache for active sessions
    - Archive cache: Recently expired items that may be needed again
    
    This tiered approach optimizes retrieval speed while maximizing memory efficiency.
    """
    
    def __init__(
        self, 
        max_conversations: int = 100,
        max_messages_per_conversation: int = 10,
        default_ttl_minutes: int = 60,
        cleanup_interval_seconds: int = 300,
        hot_cache_size: int = 10,
        archive_ttl_minutes: int = 120
    ):
        """
        Initialize the tiered memory cache.
        
        Args:
            max_conversations: Maximum number of conversations to keep in main cache
            max_messages_per_conversation: Maximum messages to keep per conversation
            default_ttl_minutes: Default time-to-live in minutes for cached items
            cleanup_interval_seconds: Interval between cache cleanup runs
            hot_cache_size: Size of the hot cache for frequent sessions
            archive_ttl_minutes: How long to keep items in archive after expiration
        """
        # Main LRU cache
        self._cache: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
        
        # Hot cache for most frequently accessed sessions
        self._hot_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._access_counts: Dict[str, int] = {}
        
        # Archive cache for recently evicted items that might be needed again
        self._archive_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        
        # Configuration
        self._max_conversations = max_conversations
        self._max_messages_per_conversation = max_messages_per_conversation
        self._default_ttl_minutes = default_ttl_minutes
        self._cleanup_interval = cleanup_interval_seconds
        self._hot_cache_size = hot_cache_size
        self._archive_ttl_minutes = archive_ttl_minutes
        
        # Tracking state
        self._modified_sessions: Set[str] = set()  # Track modified sessions that need DB sync
        self._last_sync_time: Dict[str, float] = {}  # Track last sync time per session
        self._lock = asyncio.Lock()
        
        # Metrics tracking
        self._hit_count = 0
        self._miss_count = 0
        self._hot_cache_hits = 0
        self._archive_cache_hits = 0
        
        # Start background cleanup task
        self._cleanup_task = None
        self._running = True
    
    async def start(self):
        """Start the background cleanup task."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Tiered memory cache background cleanup task started")
    
    async def stop(self):
        """Stop the background cleanup task."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Tiered memory cache background cleanup task stopped")
    
    async def _cleanup_loop(self):
        """Background task to periodically clean up expired cache entries."""
        try:
            while self._running:
                await self._cleanup_expired()
                await asyncio.sleep(self._cleanup_interval)
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired messages from all cache tiers."""
        now = time.time()
        to_remove_main = []
        to_remove_hot = []
        to_remove_archive = []
        to_archive = {}
        
        async with self._lock:
            # Clean main cache
            for session_id, messages in self._cache.items():
                # Filter out expired messages
                valid_messages = []
                for msg in messages:
                    if msg.get("expires_at", 0) > now:
                        valid_messages.append(msg)
                
                if not valid_messages:
                    # Archive the session before removing it from main cache
                    to_archive[session_id] = messages
                    to_remove_main.append(session_id)
                else:
                    self._cache[session_id] = valid_messages
            
            # Clean hot cache
            for session_id, messages in self._hot_cache.items():
                # Filter out expired messages
                valid_messages = []
                for msg in messages:
                    if msg.get("expires_at", 0) > now:
                        valid_messages.append(msg)
                
                if not valid_messages:
                    to_remove_hot.append(session_id)
                else:
                    self._hot_cache[session_id] = valid_messages
            
            # Clean archive cache
            for session_id, (archive_time, _) in self._archive_cache.items():
                if now > archive_time + (self._archive_ttl_minutes * 60):
                    to_remove_archive.append(session_id)
            
            # Remove empty sessions from all caches
            for session_id in to_remove_main:
                del self._cache[session_id]
                self._modified_sessions.discard(session_id)
                self._last_sync_time.pop(session_id, None)
            
            for session_id in to_remove_hot:
                del self._hot_cache[session_id]
                self._access_counts.pop(session_id, None)
                self._modified_sessions.discard(session_id)
                self._last_sync_time.pop(session_id, None)
            
            for session_id in to_remove_archive:
                del self._archive_cache[session_id]
            
            # Add expired but potentially useful sessions to archive
            for session_id, messages in to_archive.items():
                self._archive_cache[session_id] = (now, messages)
        
        if to_remove_main or to_remove_hot or to_remove_archive:
            logger.debug(
                f"Cleaned up cache: removed {len(to_remove_main)} main, "
                f"{len(to_remove_hot)} hot, {len(to_remove_archive)} archive sessions"
            )
    
    async def add_message(
        self,
        session_id: str,
        message: Dict[str, Any],
        ttl_minutes: Optional[int] = None
    ) -> bool:
        """
        Add a message to the conversation cache.
        
        Args:
            session_id: Unique identifier for the conversation
            message: Message data to cache
            ttl_minutes: Time-to-live in minutes for this message
            
        Returns:
            True if the message was successfully added
        """
        if not message:
            return False
        
        ttl = ttl_minutes or self._default_ttl_minutes
        expires_at = time.time() + (ttl * 60)
        
        # Add expiration time to message
        message_copy = message.copy()
        message_copy["expires_at"] = expires_at
        message_copy["added_to_cache_at"] = time.time()
        
        async with self._lock:
            # Check if session is in hot cache
            if session_id in self._hot_cache:
                messages = self._hot_cache[session_id]
                messages.append(message_copy)
                
                # Limit messages in hot cache
                if len(messages) > self._max_messages_per_conversation:
                    messages = messages[-self._max_messages_per_conversation:]
                
                self._hot_cache[session_id] = messages
                self._access_counts[session_id] += 1
                self._modified_sessions.add(session_id)
                return True
            
            # If session was in archive, move it back to main cache
            if session_id in self._archive_cache:
                _, archived_messages = self._archive_cache.pop(session_id)
                
                # Keep only non-expired messages
                now = time.time()
                valid_archived = [msg for msg in archived_messages 
                                 if msg.get("expires_at", 0) > now]
                
                # Combine with new message
                combined_messages = valid_archived + [message_copy]
                if len(combined_messages) > self._max_messages_per_conversation:
                    combined_messages = combined_messages[-self._max_messages_per_conversation:]
                
                # Add to main cache
                if session_id in self._cache:
                    del self._cache[session_id]  # Remove if exists to move to end
                
                self._cache[session_id] = combined_messages
                self._access_counts[session_id] = 1
                self._modified_sessions.add(session_id)
                
                # If cache is too large, evict oldest
                self._evict_if_needed()
                
                return True
            
            # Move this session to the end (most recently used)
            if session_id in self._cache:
                messages = self._cache.pop(session_id)
                self._access_counts[session_id] = self._access_counts.get(session_id, 0) + 1
            else:
                messages = []
                self._access_counts[session_id] = 1
            
            # Add message to list and limit to max messages
            messages.append(message_copy)
            if len(messages) > self._max_messages_per_conversation:
                messages = messages[-self._max_messages_per_conversation:]
            
            # Put back in cache
            self._cache[session_id] = messages
            
            # Check if this session should be promoted to hot cache
            self._update_hot_cache(session_id)
            
            # If cache is too large, remove oldest session
            self._evict_if_needed()
            
            # Mark this session as modified
            self._modified_sessions.add(session_id)
        
        return True
    
    def _update_hot_cache(self, session_id: str):
        """Update hot cache based on access patterns."""
        # If this session is accessed frequently, move to hot cache
        access_count = self._access_counts.get(session_id, 0)
        
        if access_count >= 3 and session_id not in self._hot_cache:
            # Find candidate for hot cache
            if len(self._hot_cache) >= self._hot_cache_size:
                # Find least accessed hot cache item
                min_session = min(
                    self._hot_cache.keys(), 
                    key=lambda s: self._access_counts.get(s, 0)
                )
                min_count = self._access_counts.get(min_session, 0)
                
                # Only replace if this session has higher access count
                if access_count > min_count:
                    # Move min session back to regular cache
                    self._cache[min_session] = self._hot_cache.pop(min_session)
                    
                    # Move this session to hot cache
                    self._hot_cache[session_id] = self._cache.pop(session_id)
            else:
                # Hot cache has space, just add
                self._hot_cache[session_id] = self._cache.pop(session_id)
    
    def _evict_if_needed(self):
        """Evict oldest entries if cache exceeds size limit."""
        # If main cache is too large, move oldest to archive
        if len(self._cache) > self._max_conversations:
            oldest_session = next(iter(self._cache))
            oldest_messages = self._cache.pop(oldest_session)
            
            # Archive the evicted session
            self._archive_cache[oldest_session] = (time.time(), oldest_messages)
            
            # Clean up tracking for evicted session
            self._access_counts.pop(oldest_session, 0)
            self._modified_sessions.discard(oldest_session)
            self._last_sync_time.pop(oldest_session, None)
            
            logger.debug(f"Moved oldest session {oldest_session} from main cache to archive")
        
        # Keep archive cache size reasonable
        max_archive = min(self._max_conversations * 2, 1000)  # Cap at 1000 entries
        if len(self._archive_cache) > max_archive:
            # Remove oldest archived items
            to_remove = sorted(
                self._archive_cache.items(),
                key=lambda x: x[1][0]  # Sort by archive timestamp
            )[:len(self._archive_cache) - max_archive]
            
            for session_id, _ in to_remove:
                del self._archive_cache[session_id]
    
    async def get_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get cached messages for a session from the appropriate cache tier.
        
        Args:
            session_id: Unique identifier for the conversation
            limit: Maximum number of messages to return
            
        Returns:
            List of message data dictionaries, newest first
        """
        async with self._lock:
            # Check hot cache first (fastest access)
            if session_id in self._hot_cache:
                self._access_counts[session_id] += 1
                self._hit_count += 1
                self._hot_cache_hits += 1
                messages = self._hot_cache[session_id]
                return list(reversed(messages[-limit:]))
            
            # Then check main cache
            if session_id in self._cache:
                # Move to end of OrderedDict (most recently used)
                messages = self._cache.pop(session_id)
                self._cache[session_id] = messages
                
                # Update access count and check for promotion to hot cache
                self._access_counts[session_id] = self._access_counts.get(session_id, 0) + 1
                self._update_hot_cache(session_id)
                
                self._hit_count += 1
                return list(reversed(messages[-limit:]))
            
            # Check archive cache for recently evicted sessions
            if session_id in self._archive_cache:
                archived_time, messages = self._archive_cache.pop(session_id)
                
                # Filter out expired messages
                now = time.time()
                valid_messages = [msg for msg in messages if msg.get("expires_at", 0) > now]
                
                if valid_messages:
                    # Move back to main cache since it's accessed again
                    self._cache[session_id] = valid_messages
                    self._access_counts[session_id] = 1
                    
                    # If cache too large after this addition, evict oldest
                    self._evict_if_needed()
                    
                    self._hit_count += 1
                    self._archive_cache_hits += 1
                    return list(reversed(valid_messages[-limit:]))
            
            # Session not in any cache
            self._miss_count += 1
            return []
    
    async def has_session(self, session_id: str) -> bool:
        """Check if a session exists in any cache tier."""
        async with self._lock:
            return (session_id in self._cache 
                    or session_id in self._hot_cache 
                    or session_id in self._archive_cache)
    
    async def get_modified_sessions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all sessions that have been modified since last sync.
        
        Returns:
            Dictionary of session_id -> messages for all modified sessions
        """
        modified_data = {}
        
        async with self._lock:
            for session_id in list(self._modified_sessions):
                if session_id in self._hot_cache:
                    modified_data[session_id] = self._hot_cache[session_id]
                elif session_id in self._cache:
                    modified_data[session_id] = self._cache[session_id]
            
            # Clear modified sessions since we're returning them all
            self._modified_sessions.clear()
        
        return modified_data
    
    async def mark_synced(self, session_id: str):
        """Mark a session as synced with the database."""
        async with self._lock:
            self._modified_sessions.discard(session_id)
            self._last_sync_time[session_id] = time.time()
    
    async def clear(self):
        """Clear all cache data from all tiers."""
        async with self._lock:
            self._cache.clear()
            self._hot_cache.clear() 
            self._archive_cache.clear()
            self._modified_sessions.clear()
            self._last_sync_time.clear()
            self._access_counts.clear()
            
            # Reset metrics
            self._hit_count = 0
            self._miss_count = 0
            self._hot_cache_hits = 0
            self._archive_cache_hits = 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about the cache tiers."""
        async with self._lock:
            # Calculate hit ratio
            total_accesses = self._hit_count + self._miss_count
            hit_ratio = self._hit_count / total_accesses if total_accesses > 0 else 0
            
            # Get size of each cache
            main_cache_size = len(self._cache)
            main_cache_messages = sum(len(messages) for messages in self._cache.values())
            hot_cache_size = len(self._hot_cache)
            hot_cache_messages = sum(len(messages) for messages in self._hot_cache.values())
            archive_cache_size = len(self._archive_cache)
            archive_cache_messages = sum(len(messages) for _, messages in self._archive_cache.values())
            
            total_modified = len(self._modified_sessions)
            
            return {
                # Cache sizes
                "main_cache_sessions": main_cache_size,
                "main_cache_messages": main_cache_messages,
                "hot_cache_sessions": hot_cache_size,
                "hot_cache_messages": hot_cache_messages,
                "archive_cache_sessions": archive_cache_size,
                "archive_cache_messages": archive_cache_messages,
                "total_sessions": main_cache_size + hot_cache_size + archive_cache_size,
                "total_messages": main_cache_messages + hot_cache_messages + archive_cache_messages,
                
                # Performance metrics
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_ratio": hit_ratio,
                "hot_cache_hits": self._hot_cache_hits,
                "archive_cache_hits": self._archive_cache_hits,
                
                # Tracking
                "total_modified_sessions": total_modified,
                
                # Configuration
                "max_conversations": self._max_conversations,
                "max_messages_per_conversation": self._max_messages_per_conversation,
                "default_ttl_minutes": self._default_ttl_minutes,
                "cleanup_interval_seconds": self._cleanup_interval,
                "hot_cache_size": self._hot_cache_size,
                "archive_ttl_minutes": self._archive_ttl_minutes,
            } 