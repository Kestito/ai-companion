import logging
import uuid
from datetime import datetime
from typing import List, Optional

from langchain_core.messages import BaseMessage
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from langchain.schema import Document

from ai_companion.core.prompts import MEMORY_ANALYSIS_PROMPT
from ai_companion.modules.memory.long_term.vector_store import get_vector_store
from ai_companion.settings import settings


class MemoryAnalysis(BaseModel):
    """Result of analyzing a message for memory-worthy content."""

    is_important: bool = Field(
        ...,
        description="Whether the message is important enough to be stored as a memory",
    )
    formatted_memory: Optional[str] = Field(
        ..., description="The formatted memory to be stored"
    )


class MemoryManager:
    """Manager class for handling long-term memory operations."""

    def __init__(self):
        self.vector_store = get_vector_store()
        self.logger = logging.getLogger(__name__)
        self.llm = AzureChatOpenAI(
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            temperature=0.1,
        ).with_structured_output(MemoryAnalysis)
        self.has_greeted = False
        self.recent_memories = []  # Cache for recent memories
        self.memory_cache_size = 20  # Number of recent memories to keep in cache

    async def _analyze_memory(self, message: str) -> MemoryAnalysis:
        """Analyze a message to determine importance and format if needed."""
        prompt = MEMORY_ANALYSIS_PROMPT.format(message=message)
        return await self.llm.ainvoke(prompt)

    async def add_memory(self, content: str) -> None:
        """Add a new memory to the vector store with enhanced caching.
        
        Args:
            content: The content to store as a memory
        """
        try:
            # Track if this is a greeting
            if "labas" in content.lower():
                self.has_greeted = True
                
            memory_analysis = await self._analyze_memory(content)
            if memory_analysis.is_important and memory_analysis.formatted_memory:
                memory_id = str(uuid.uuid4())
                metadata = {
                    "id": memory_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "conversation_memory",
                    "is_greeting": "labas" in content.lower(),
                    "importance_score": 0.8  # Default importance score
                }
                
                # Store in vector store
                self.vector_store.store_memory(
                    text=memory_analysis.formatted_memory,
                    metadata=metadata
                )
                
                # Add to recent memories cache
                self.recent_memories.append({
                    "id": memory_id,
                    "content": memory_analysis.formatted_memory,
                    "timestamp": metadata["timestamp"]
                })
                
                # Maintain cache size
                if len(self.recent_memories) > self.memory_cache_size:
                    self.recent_memories.pop(0)
                
                self.logger.info(f"Added new memory: {memory_id}")
        except Exception as e:
            self.logger.error(f"Error adding memory: {e}", exc_info=True)

    def has_already_greeted(self) -> bool:
        """Check if we have already greeted the user in this session."""
        return self.has_greeted

    async def extract_and_store_memories(self, message: BaseMessage) -> None:
        """Extract important information from a message and store in vector store."""
        if message.type != "human":
            return

        try:
            await self.add_memory(message.content)
        except Exception as e:
            self.logger.error(f"Error extracting memories: {e}", exc_info=True)

    def get_relevant_memories(self, context: str) -> List[str]:
        """Retrieve relevant memories with enhanced context handling.
        
        This method combines vector search with recent memory cache for better context retention.
        """
        memories = []
        
        # First, check recent memories cache
        for memory in reversed(self.recent_memories):  # Most recent first
            memories.append(memory["content"])
        
        # Then get relevant memories from vector store
        vector_memories = self.vector_store.search_memories(
            context, 
            k=max(1, settings.MEMORY_TOP_K - len(memories))
        )
        
        # Combine and deduplicate memories
        seen = set()
        combined_memories = []
        
        for memory in memories + [m.text for m in vector_memories]:
            if memory not in seen:
                combined_memories.append(memory)
                seen.add(memory)
        
        if combined_memories:
            for memory in combined_memories:
                self.logger.debug(f"Retrieved memory: {memory[:100]}...")
                
        return combined_memories[:settings.MEMORY_TOP_K]

    def format_memories_for_prompt(self, memories: List[str]) -> str:
        """Format retrieved memories as bullet points with enhanced context."""
        if not memories:
            return ""
        
        formatted_memories = []
        for i, memory in enumerate(memories):
            # Add recency indicator for cached memories
            if i < len(self.recent_memories):
                formatted_memories.append(f"[Recent] - {memory}")
            else:
                formatted_memories.append(f"- {memory}")
                
        return "\n".join(formatted_memories)


def get_memory_manager() -> MemoryManager:
    """Get a MemoryManager instance."""
    return MemoryManager()
