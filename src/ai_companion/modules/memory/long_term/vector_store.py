import os
from typing import Optional, List
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import AzureOpenAI

from ai_companion.settings import settings


@dataclass
class Memory:
    """Represents a memory entry in the vector store."""

    text: str
    metadata: dict
    score: Optional[float] = None

    @property
    def id(self) -> Optional[str]:
        return self.metadata.get("id")

    @property
    def timestamp(self) -> Optional[datetime]:
        ts = self.metadata.get("timestamp")
        return datetime.fromisoformat(ts) if ts else None


class VectorStore:
    """A class to handle vector storage operations using Qdrant."""

    REQUIRED_ENV_VARS = [
        "QDRANT_URL",
        "QDRANT_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_EMBEDDING_DEPLOYMENT",
    ]
    EMBEDDING_MODEL = "text-embedding-3-small"
    COLLECTION_NAME = "long_term_memory"
    SIMILARITY_THRESHOLD = 0.9

    _instance: Optional["VectorStore"] = None
    _initialized: bool = False

    def __new__(cls) -> "VectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._validate_env_vars()
            self.client = QdrantClient(
                url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY
            )
            self.azure_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-02-15-preview",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            )
            self.logger = logging.getLogger(__name__)
            self._initialized = True

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    def _collection_exists(self) -> bool:
        """Check if the memory collection exists."""
        collections = self.client.get_collections().collections
        return any(col.name == self.COLLECTION_NAME for col in collections)

    def _create_collection(self) -> None:
        """Create a new collection for storing memories."""
        sample_embedding = self._get_embedding("sample text")
        self.client.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=len(sample_embedding),
                distance=Distance.COSINE,
            ),
        )

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding using Azure OpenAI."""
        response = self.azure_client.embeddings.create(
            model=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"), input=text
        )
        return response.data[0].embedding

    def find_similar_memory(self, text: str) -> Optional[Memory]:
        """Find if a similar memory already exists.

        Args:
            text: The text to search for

        Returns:
            Optional Memory if a similar one is found
        """
        results = self.search_memories(text, k=1)
        if results and results[0].score >= self.SIMILARITY_THRESHOLD:
            return results[0]
        return None

    def store_memory(self, text: str, metadata: dict) -> None:
        """Store a new memory in the vector store or update if similar exists.

        Args:
            text: The text content of the memory
            metadata: Additional information about the memory (timestamp, type, etc.)
        """
        try:
            if not self._collection_exists():
                self.logger.info("Creating new memory collection")
                self._create_collection()

            similar_memory = self.find_similar_memory(text)
            if similar_memory and similar_memory.id:
                self.logger.debug(f"Found similar memory with ID: {similar_memory.id}")
                metadata["id"] = similar_memory.id

            embedding = self._get_embedding(text)
            point = PointStruct(
                id=metadata.get("id", hash(text)),
                vector=embedding,
                payload={
                    "text": text,
                    **metadata,
                },
            )

            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[point],
            )
            self.logger.info(f"Successfully stored memory with ID: {point.id}")

        except Exception as e:
            self.logger.error(f"Error storing memory: {e}", exc_info=True)
            raise

    def search_memories(self, query: str, k: int = 3) -> List[Memory]:
        """Search for relevant memories using the vector store.

        Args:
            query: The search query
            k: Number of results to return

        Returns:
            List of Memory objects
        """
        try:
            if not self._collection_exists():
                self.logger.debug("No collection exists yet")
                return []

            # Get embedding for the query
            query_embedding = self._get_embedding(query)

            # Search using Qdrant client

            search_results = self.client.query_points(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_embedding,
                limit=k,
            )

            # Convert to Memory objects
            memories = []
            for result in search_results:
                memory = Memory(
                    text=result.payload.get("text", ""),
                    metadata={k: v for k, v in result.payload.items() if k != "text"},
                    score=result.score,
                )
                memories.append(memory)

            # Log found memories
            if memories:
                self.logger.debug(f"Found {len(memories)} relevant memories")
                for memory in memories:
                    self.logger.debug(
                        f"Memory score: {memory.score:.3f}, text: {memory.text[:100]}..."
                    )
            else:
                self.logger.debug("No relevant memories found")

            return memories

        except Exception as e:
            self.logger.error(f"Error searching memories: {e}", exc_info=True)
            return []


@lru_cache
def get_vector_store() -> VectorStore:
    """Get or create the VectorStore singleton instance."""
    return VectorStore()
