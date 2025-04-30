import logging
import uuid
from datetime import datetime
from typing import List, Optional

from langchain_core.messages import BaseMessage
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field

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

    async def _analyze_memory(self, message: str, metadata: dict) -> MemoryAnalysis:
        """Analyze a message to determine importance and format if needed."""
        prompt = MEMORY_ANALYSIS_PROMPT.format(message=message)
        return await self.llm.ainvoke(prompt)

    async def add_memory(self, content: str, metadata: dict) -> None:
        """Add a human message to long-term memory.

        Args:
            content: Text content of the message
            metadata: Must contain patient_id and other context information
        """
        # Validate required metadata
        if not metadata or "patient_id" not in metadata:
            self.logger.error("Missing required patient_id in memory metadata")
            raise ValueError("Patient ID is required for memory storage")

        try:
            # Analyze message for importance
            analysis = await self._analyze_memory(content, metadata)

            # Only store important memories
            if analysis.is_important:
                # Use formatted memory if provided, otherwise use original content
                memory_content = analysis.formatted_memory or content

                # Add timestamp and updated metadata to ensure traceability
                memory_metadata = {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "type": "human_message",
                    "is_formatted": analysis.formatted_memory is not None,
                    **metadata,  # Include all provided metadata, especially patient_id
                }

                # Store in vector store
                self.vector_store.store_memory(memory_content, memory_metadata)

                # Also keep in recent memory cache
                self.recent_memories.append(
                    {"content": memory_content, "metadata": memory_metadata}
                )

                # Limit recent memories cache size
                if len(self.recent_memories) > self.memory_cache_size:
                    self.recent_memories.pop(0)  # Remove oldest memory

                self.logger.info(
                    f"Stored memory for patient {metadata.get('patient_id')}"
                )

        except Exception as e:
            self.logger.error(f"Error adding memory: {e}", exc_info=True)

    def has_already_greeted(self) -> bool:
        """Check if we have already greeted the user in this session."""
        return self.has_greeted

    async def extract_and_store_memories(self, message: BaseMessage) -> None:
        """Extract important information from a message and store in vector store."""
        if message.type != "human":
            return

        # Extract metadata from message
        metadata = getattr(message, "metadata", {}) or {}

        # Validate required metadata
        if "patient_id" not in metadata:
            self.logger.error("Missing required patient_id in message metadata")
            return

        try:
            await self.add_memory(message.content, metadata)
        except Exception as e:
            self.logger.error(f"Error extracting memories: {e}", exc_info=True)

    def get_relevant_memories(self, context: str, patient_id: str) -> List[str]:
        """Retrieve relevant memories with patient context isolation.

        Args:
            context: The query or context to find relevant memories for
            patient_id: The patient ID to filter memories by (REQUIRED)

        Returns:
            List of relevant memories for this patient only
        """
        if not patient_id:
            self.logger.error("Patient ID is required for memory retrieval")
            return []

        memories = []

        # First, check recent memories cache (filtered by patient_id)
        for memory in reversed(self.recent_memories):  # Most recent first
            memory_patient_id = memory.get("metadata", {}).get("patient_id")
            if memory_patient_id == patient_id:
                memories.append(memory["content"])

        # Then get relevant memories from vector store (with patient filter)
        filter_conditions = {"patient_id": patient_id}
        vector_memories = self.vector_store.search_memories(
            context,
            k=max(1, settings.MEMORY_TOP_K - len(memories)),
            filter_conditions=filter_conditions,
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
                self.logger.debug(
                    f"Retrieved memory for patient {patient_id}: {memory[:100]}..."
                )

        return combined_memories[: settings.MEMORY_TOP_K]

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
