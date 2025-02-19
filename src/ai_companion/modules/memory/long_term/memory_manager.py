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

    async def _analyze_memory(self, message: str) -> MemoryAnalysis:
        """Analyze a message to determine importance and format if needed."""
        prompt = MEMORY_ANALYSIS_PROMPT.format(message=message)
        return await self.llm.ainvoke(prompt)

    async def add_memory(self, content: str) -> None:
        """Add a new memory to the vector store.
        
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
                    "is_greeting": "labas" in content.lower()
                }
                self.vector_store.store_memory(
                    text=memory_analysis.formatted_memory,
                    metadata=metadata
                )
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
        """Retrieve relevant memories based on the current context."""
        memories = self.vector_store.search_memories(context, k=settings.MEMORY_TOP_K)
        if memories:
            for memory in memories:
                self.logger.debug(
                    f"Memory: '{memory.text}' (score: {memory.score:.2f})"
                )
        return [memory.text for memory in memories]

    def format_memories_for_prompt(self, memories: List[str]) -> str:
        """Format retrieved memories as bullet points."""
        if not memories:
            return ""
        return "\n".join(f"- {memory}" for memory in memories)


def get_memory_manager() -> MemoryManager:
    """Get a MemoryManager instance."""
    return MemoryManager()
