import os
from typing import Optional, List
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime
import logging
import time

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http import models
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
        try:
            self._validate_env_vars()
            self.qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=30,  # Increased timeout for more reliability
            )

            self.azure_client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            )

            self._initialized = True
            self.logger = logging.getLogger(__name__)
            self.logger.info("VectorStore initialized successfully")
        except Exception as e:
            self._initialized = False
            self.qdrant_client = None
            self.azure_client = None
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Failed to initialize VectorStore: {e}", exc_info=True)

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    def ensure_collection(self, collection_name: str) -> bool:
        """
        Ensures a collection exists, creates it if it doesn't.
        Returns True if successful, False otherwise.
        """
        try:
            if not self._initialized or not self.qdrant_client:
                self.logger.error("VectorStore not properly initialized")
                return False

            if not self._collection_exists(collection_name):
                return self._create_collection(collection_name)
            return True
        except Exception as e:
            self.logger.error(
                f"Error ensuring collection {collection_name}: {e}", exc_info=True
            )
            return False

    def _collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.
        """
        try:
            if not self._initialized or not self.qdrant_client:
                self.logger.error(
                    "Cannot check if collection exists - client not initialized"
                )
                return False

            collections = self.qdrant_client.get_collections().collections
            return any(collection.name == collection_name for collection in collections)
        except Exception as e:
            self.logger.error(
                f"Error checking if collection {collection_name} exists: {e}",
                exc_info=True,
            )
            return False

    def _create_collection(self, collection_name: str) -> bool:
        """
        Create a new collection.
        Returns True if successful, False otherwise.
        """
        try:
            if not self._initialized or not self.qdrant_client:
                self.logger.error("Cannot create collection - client not initialized")
                return False

            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=1536,  # OpenAI embedding size
                    distance=models.Distance.COSINE,
                ),
            )
            self.logger.info(f"Created collection: {collection_name}")
            return True
        except Exception as e:
            self.logger.error(
                f"Error creating collection {collection_name}: {e}", exc_info=True
            )
            return False

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a text.
        Returns None if embedding generation fails.
        """
        try:
            if not self._initialized or not self.azure_client:
                self.logger.error("Cannot generate embedding - client not initialized")
                return None

            response = self.azure_client.embeddings.create(
                input=text, model=settings.AZURE_EMBEDDING_DEPLOYMENT
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}", exc_info=True)
            return None

    def find_similar_memory(
        self, text: str, filter_conditions: Optional[dict] = None
    ) -> Optional[Memory]:
        """Find if a similar memory already exists.

        Args:
            text: The text to search for
            filter_conditions: Dictionary of conditions to filter search results (e.g. patient_id)

        Returns:
            Optional Memory if a similar one is found
        """
        results = self.search_memories(text, k=1, filter_conditions=filter_conditions)
        if results and results[0].score >= self.SIMILARITY_THRESHOLD:
            return results[0]
        return None

    def store_memory(self, text: str, metadata: dict) -> bool:
        """Store a new memory in the vector store or update if similar exists.

        Args:
            text: The text content of the memory
            metadata: Additional information about the memory (must include patient_id)

        Returns:
            bool: True if memory was stored successfully, False otherwise
        """
        try:
            if not self._initialized:
                self.logger.error("VectorStore not properly initialized")
                return False

            # Validate required metadata
            if "patient_id" not in metadata:
                self.logger.error("Missing required patient_id in memory metadata")
                return False

            # Check if collection exists, create if needed
            collection_exists = self.ensure_collection(self.COLLECTION_NAME)
            if not collection_exists:
                self.logger.error("Failed to ensure memory collection exists")
                return False

            # Only find similar memories for the same patient
            filter_conditions = {"patient_id": metadata["patient_id"]}
            similar_memory = self.find_similar_memory(text, filter_conditions)
            if similar_memory and similar_memory.id:
                self.logger.debug(f"Found similar memory with ID: {similar_memory.id}")
                metadata["id"] = similar_memory.id

            # Get embedding for text
            embedding = self._get_embedding(text)
            if not embedding:
                self.logger.error("Failed to generate embedding for memory")
                return False

            # Create point for Qdrant
            point = models.PointStruct(
                id=metadata.get("id", hash(text)),
                vector=embedding,
                payload={
                    "text": text,
                    **metadata,
                },
            )

            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[point],
            )
            self.logger.info(
                f"Successfully stored memory with ID: {point.id} for patient {metadata['patient_id']}"
            )
            return True

        except UnexpectedResponse as e:
            self.logger.error(
                f"Qdrant returned unexpected response while storing memory: {e}"
            )
            return False
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}", exc_info=True)
            return False

    def search_memories(
        self, query: str, k: int = 3, filter_conditions: Optional[dict] = None
    ) -> List[Memory]:
        """Search for relevant memories using the vector store.

        Args:
            query: The text to search for similar memories
            k: The number of results to return
            filter_conditions: Dictionary of conditions to filter search results

        Returns:
            List of Memory objects with similarity scores
        """
        try:
            if not self._initialized or not self.qdrant_client:
                self.logger.error(
                    "Cannot search memories - VectorStore not properly initialized"
                )
                return []

            if not query or not query.strip():
                self.logger.warning("Empty query provided for memory search")
                return []

            # Ensure collection exists
            collection_exists = self.ensure_collection(self.COLLECTION_NAME)
            if not collection_exists:
                self.logger.error(
                    "Failed to ensure memory collection exists for search"
                )
                return []

            # Get embedding for query
            embedding = self._get_embedding(query)
            if not embedding:
                self.logger.warning(
                    "Failed to generate embedding for memory search query"
                )
                return []

            # Prepare search filter if provided
            search_filter = None
            if filter_conditions:
                search_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),
                        )
                        for key, value in filter_conditions.items()
                    ]
                )

            # Execute search with retry logic
            max_retries = 2
            retry_count = 0
            last_error = None

            while retry_count <= max_retries:
                try:
                    search_results = self.qdrant_client.search(
                        collection_name=self.COLLECTION_NAME,
                        query_vector=embedding,
                        limit=k,
                        query_filter=search_filter,
                        with_payload=True,
                    )

                    memories = []
                    for result in search_results:
                        payload = result.payload
                        text = payload.pop("text", "")
                        memories.append(
                            Memory(text=text, metadata=payload, score=result.score)
                        )

                    self.logger.info(f"Found {len(memories)} memories for query")
                    return memories

                except UnexpectedResponse as e:
                    last_error = e
                    retry_count += 1
                    self.logger.warning(
                        f"Qdrant search attempt {retry_count}/{max_retries} failed: {e}. Retrying..."
                    )
                    # Add a short delay before retrying to allow potential transient issues to resolve
                    time.sleep(1.0)
                except Exception as e:
                    # For non-Qdrant specific exceptions, don't retry
                    self.logger.error(f"Error during memory search: {e}", exc_info=True)
                    return []

            # If we've exhausted all retries
            if last_error:
                self.logger.error(f"All retries failed for memory search: {last_error}")

            return []

        except Exception as e:
            self.logger.error(
                f"Unexpected error during memory search: {e}", exc_info=True
            )
            return []


@lru_cache
def get_vector_store() -> VectorStore:
    """Get a singleton instance of the VectorStore.

    Returns:
        VectorStore instance
    """
    return VectorStore()
