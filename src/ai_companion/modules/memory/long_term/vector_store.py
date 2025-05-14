import os
import asyncio
from typing import Optional, List, Dict, Any
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime
import logging

from qdrant_client import QdrantClient
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
    _initialization_lock = asyncio.Lock()

    def __new__(cls) -> "VectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Set up the logger first
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        self.qdrant_client = None
        self.azure_client = None

        # Note: Actual initialization is deferred to async_initialize()
        # This allows the constructor to return immediately without blocking

    async def async_initialize(self) -> bool:
        """
        Asynchronously initialize the VectorStore.
        Returns True if initialization was successful, False otherwise.
        """
        # Skip if already initialized
        if self._initialized:
            return True

        # Use a lock to prevent multiple concurrent initializations
        async with self._initialization_lock:
            # Double-check if initialized while waiting for lock
            if self._initialized:
                return True

            try:
                self._validate_env_vars()

                # Move the blocking QdrantClient initialization to a thread
                self.qdrant_client = await asyncio.to_thread(
                    lambda: QdrantClient(
                        url=settings.QDRANT_URL,
                        api_key=settings.QDRANT_API_KEY,
                        timeout=30,  # Increased timeout for more reliability
                        check_compatibility=False,  # Added to suppress version check warning
                    )
                )

                # Move the AzureOpenAI client initialization to a thread as well
                self.azure_client = await asyncio.to_thread(
                    lambda: AzureOpenAI(
                        api_key=settings.AZURE_OPENAI_API_KEY,
                        api_version=settings.AZURE_OPENAI_API_VERSION,
                        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    )
                )

                self._initialized = True
                self.logger.info("VectorStore initialized successfully")
                return True
            except Exception as e:
                self._initialized = False
                self.qdrant_client = None
                self.azure_client = None
                self.logger.error(
                    f"Failed to initialize VectorStore: {e}", exc_info=True
                )
                return False

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    async def ensure_collection(self, collection_name: str) -> bool:
        """
        Ensures a collection exists, creates it if it doesn't.
        Returns True if successful, False otherwise.
        """
        try:
            # Make sure we're initialized first
            if not self._initialized:
                initialized = await self.async_initialize()
                if not initialized:
                    self.logger.error("Failed to initialize VectorStore")
                    return False

            if not self.qdrant_client:
                self.logger.error("VectorStore not properly initialized")
                return False

            # Move collection existence check to a thread
            exists = await asyncio.to_thread(
                lambda: self._collection_exists(collection_name)
            )

            if not exists:
                # Move collection creation to a thread
                return await asyncio.to_thread(
                    lambda: self._create_collection(collection_name)
                )
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

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a text asynchronously.
        Returns None if embedding generation fails.
        """
        try:
            if not self._initialized or not self.azure_client:
                self.logger.error("Cannot generate embedding - client not initialized")
                return None

            # If text is empty, log and return None
            if not text or text.strip() == "":
                self.logger.warning("Empty text provided to _get_embedding, skipping")
                return None

            # Generate embedding
            response = self.azure_client.embeddings.create(
                input=text, model=settings.AZURE_EMBEDDING_DEPLOYMENT
            )

            # Verify the response has data
            if not response.data or len(response.data) == 0:
                self.logger.error("Azure OpenAI returned empty embedding data")
                return None

            # Verify the embedding exists and is not empty
            embedding = response.data[0].embedding
            if not embedding or len(embedding) == 0:
                self.logger.error("Azure OpenAI returned empty embedding vector")
                return None

            self.logger.debug(
                f"Successfully generated embedding of dimension {len(embedding)}"
            )
            return embedding
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}", exc_info=True)
            return None

    # Synchronous version removed as F811 indicated it was unused before async redefinition
    # def find_similar_memory(
    #     self, text: str, filter_conditions: Optional[dict] = None
    # ) -> Optional[Memory]:
    #     """Find if a similar memory already exists.
    #
    #     Args:
    #         text: The text to search for
    #         filter_conditions: Dictionary of conditions to filter search results (e.g. patient_id)
    #
    #     Returns:
    #         Optional Memory if a similar one is found
    #     """
    #     results = self.search_memories(text, k=1, filter_conditions=filter_conditions)
    #     if results and results[0].score >= self.SIMILARITY_THRESHOLD:
    #         return results[0]
    #     return None

    async def find_similar_memory(
        self, text: str, filter_conditions: Optional[dict] = None
    ) -> Optional[Memory]:
        """Find if a similar memory already exists.

        Args:
            text: The text to search for
            filter_conditions: Dictionary of conditions to filter search results (e.g. patient_id)

        Returns:
            Optional Memory if a similar one is found
        """
        results = await self.search_memories(
            text, k=1, filter_conditions=filter_conditions
        )
        if results and results[0].score >= self.SIMILARITY_THRESHOLD:
            return results[0]
        return None

    # Synchronous version removed as F811 indicated it was unused before async redefinition
    # def store_memory(self, text: str, metadata: dict) -> bool:
    #     """Store a new memory in the vector store or update if similar exists.
    #
    #     Args:
    #         text: The text content of the memory
    #         metadata: Additional information about the memory (must include patient_id)
    #
    #     Returns:
    #         bool: True if memory was stored successfully, False otherwise
    #     """
    #     try:
    #         if not self._initialized:
    #             self.logger.error("VectorStore not properly initialized")
    #             return False
    #
    #         # Validate required metadata
    #         if "patient_id" not in metadata:
    #             self.logger.error("Missing required patient_id in memory metadata")
    #             return False
    #
    #         # Check if collection exists, create if needed
    #         collection_exists = self.ensure_collection(self.COLLECTION_NAME)
    #         if not collection_exists:
    #             self.logger.error("Failed to ensure memory collection exists")
    #             return False
    #
    #         # Only find similar memories for the same patient
    #         filter_conditions = {"patient_id": metadata["patient_id"]}
    #         similar_memory = self.find_similar_memory(text, filter_conditions)
    #         if similar_memory and similar_memory.id:
    #             self.logger.debug(f"Found similar memory with ID: {similar_memory.id}")
    #             metadata["id"] = similar_memory.id
    #
    #         # Get embedding for text
    #         embedding = self._get_embedding(text)
    #         if not embedding:
    #             self.logger.error("Failed to generate embedding for memory")
    #             return False
    #
    #         # Create point for Qdrant
    #         point = models.PointStruct(
    #             id=metadata.get("id", hash(text)),
    #             vector=embedding,
    #             payload={
    #                 "text": text,
    #                 **metadata,
    #             },
    #         )
    #
    #         # Store in Qdrant
    #         self.qdrant_client.upsert(
    #             collection_name=self.COLLECTION_NAME,
    #             points=[point],
    #         )
    #         self.logger.info(
    #             f"Successfully stored memory with ID: {point.id} for patient {metadata['patient_id']}"
    #         )
    #         return True
    #
    #     except UnexpectedResponse as e:
    #         self.logger.error(
    #             f"Qdrant returned unexpected response while storing memory: {e}"
    #         )
    #         return False
    #     except Exception as e:
    #         self.logger.error(f"Error storing memory: {e}", exc_info=True)
    #         return False

    async def store_memory(self, text: str, metadata: dict) -> bool:
        """Store a new memory in the vector store or update if similar exists.

        Args:
            text: The text content of the memory
            metadata: Additional information about the memory (must include patient_id)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Make sure we're initialized
            if not self._initialized:
                initialized = await self.async_initialize()
                if not initialized:
                    self.logger.error("Failed to initialize VectorStore")
                    return False

            # Validate minimal metadata
            if "patient_id" not in metadata:
                self.logger.error("Missing required patient_id in memory metadata")
                return False

            # Add timestamp if not present
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.now().isoformat()

            # Ensure collection exists
            collection_name = self.COLLECTION_NAME
            collection_ready = await self.ensure_collection(collection_name)
            if not collection_ready:
                self.logger.error(f"Failed to ensure collection {collection_name}")
                return False

            # Get embedding for text
            embedding = await self._get_embedding(text)
            if embedding is None:
                self.logger.error("Failed to generate embedding for memory")
                return False

            # Generate ID based on content hash and timestamp to make it consistent
            import hashlib

            content_hash = hashlib.md5(
                f"{text}-{metadata['patient_id']}".encode()
            ).hexdigest()
            memory_id = f"mem-{content_hash}"
            metadata["id"] = memory_id

            # Check if similar memory exists with same patient context
            similar_memory = await self.find_similar_memory(
                text,
                filter_conditions={"patient_id": metadata["patient_id"]},
            )

            point_id = memory_id
            if similar_memory:
                # Update existing memory instead of creating new one
                point_id = similar_memory.id
                self.logger.info(f"Updating similar existing memory: {point_id}")

            # Store or update the memory using a thread
            _operation = await asyncio.to_thread(
                lambda: self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=[
                        models.PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={"text": text, "metadata": metadata},
                        )
                    ],
                )
            )

            self.logger.info(f"Memory stored successfully with ID: {point_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}", exc_info=True)
            return False

    # Synchronous version removed as F811 indicated it was unused before async redefinition
    # def search_memories(
    #     self, query: str, k: int = 3, filter_conditions: Optional[dict] = None
    # ) -> List[Memory]:
    #     """Search for relevant memories using the vector store.
    #
    #     Args:
    #         query: The text to search for similar memories
    #         k: The number of results to return
    #         filter_conditions: Dictionary of conditions to filter search results
    #
    #     Returns:
    #         List of Memory objects with similarity scores
    #     """
    #     try:
    #         if not self._initialized or not self.qdrant_client:
    #             self.logger.error(
    #                 "Cannot search memories - VectorStore not properly initialized"
    #             )
    #             return []
    #
    #         if not query or not query.strip():
    #             self.logger.warning("Empty query provided for memory search")
    #             return []
    #
    #         # Ensure collection exists
    #         collection_exists = self.ensure_collection(self.COLLECTION_NAME)
    #         if not collection_exists:
    #             self.logger.error(
    #                 "Failed to ensure memory collection exists for search"
    #             )
    #             return []
    #
    #         # Get embedding for query
    #         embedding = self._get_embedding(query)
    #         if not embedding:
    #             self.logger.warning(
    #                 "Failed to generate embedding for memory search query"
    #             )
    #             return []
    #
    #         # Prepare search filter if provided
    #         search_filter = None
    #         if filter_conditions:
    #             search_filter = models.Filter(
    #                 must=[
    #                     models.FieldCondition(
    #                         key=key,
    #                         match=models.MatchValue(value=value),
    #                     )
    #                     for key, value in filter_conditions.items()
    #                 ]
    #             )
    #
    #         # Execute search with retry logic
    #         max_retries = 2
    #         retry_count = 0
    #         last_error = None
    #
    #         while retry_count <= max_retries:
    #             try:
    #                 search_results = self.qdrant_client.search(
    #                     collection_name=self.COLLECTION_NAME,
    #                     query_vector=embedding,
    #                     limit=k,
    #                     query_filter=search_filter,
    #                     with_payload=True,
    #                 )
    #
    #                 memories = []
    #                 for result in search_results:
    #                     payload = result.payload
    #                     text = payload.pop("text", "")
    #                     memories.append(
    #                         Memory(text=text, metadata=payload, score=result.score)
    #                     )
    #
    #                 self.logger.info(f"Found {len(memories)} memories for query")
    #                 return memories
    #
    #             except UnexpectedResponse as e:
    #                 last_error = e
    #                 retry_count += 1
    #                 self.logger.warning(
    #                     f"Qdrant search attempt {retry_count}/{max_retries} failed: {e}. Retrying..."
    #                 )
    #                 # Add a short delay before retrying to allow potential transient issues to resolve
    #                 time.sleep(1.0)
    #             except Exception as e:
    #                 # For non-Qdrant specific exceptions, don't retry
    #                 self.logger.error(f"Error during memory search: {e}", exc_info=True)
    #                 return []
    #
    #         # If we've exhausted all retries
    #         if last_error:
    #             self.logger.error(f"All retries failed for memory search: {last_error}")
    #
    #         return []
    #
    #     except Exception as e:
    #         self.logger.error(
    #             f"Unexpected error during memory search: {e}", exc_info=True
    #         )
    #         return []

    async def search_memories(
        self, query: str, k: int = 3, filter_conditions: Optional[dict] = None
    ) -> List[Memory]:
        """Search for relevant memories based on semantic similarity.

        Args:
            query: The search query text
            k: Number of results to return
            filter_conditions: Dictionary of conditions to filter search results

        Returns:
            List of Memory objects ordered by relevance
        """
        try:
            # Make sure we're initialized
            if not self._initialized:
                initialized = await self.async_initialize()
                if not initialized:
                    self.logger.error("Failed to initialize VectorStore")
                    return []

            # Ensure collection exists
            collection_name = self.COLLECTION_NAME
            collection_ready = await self.ensure_collection(collection_name)
            if not collection_ready:
                self.logger.error(f"Collection {collection_name} not ready")
                return []

            # Get embedding for query
            query_embedding = await self._get_embedding(query)
            if query_embedding is None:
                self.logger.error("Failed to generate embedding for search query")
                return []

            # Build filter conditions
            search_filter = None
            if filter_conditions:
                # Use a thread for the filter building to avoid any potential blocking
                search_filter = await asyncio.to_thread(
                    lambda: self._build_filter_from_conditions(filter_conditions)
                )

            # Perform the search using a thread
            search_result = await asyncio.to_thread(
                lambda: self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=k,
                    query_filter=search_filter,
                    with_payload=True,
                )
            )

            # Convert results to Memory objects
            memories = []
            for point in search_result:
                payload = point.payload
                text = payload.get("text", "")
                metadata = payload.get("metadata", {})
                score = point.score

                memories.append(Memory(text=text, metadata=metadata, score=score))

            return memories
        except Exception as e:
            self.logger.error(f"Error searching memories: {e}", exc_info=True)
            return []

    def _build_filter_from_conditions(
        self, conditions: Dict[str, Any]
    ) -> Optional[models.Filter]:
        """
        Build a Qdrant filter from a dictionary of conditions.

        Args:
            conditions: Dictionary of field conditions to filter by

        Returns:
            Qdrant filter object
        """
        if not conditions:
            return None

        must_conditions = []

        # Convert each condition to a proper field condition
        for key, value in conditions.items():
            # Handle the "metadata." prefix if needed
            field_key = f"metadata.{key}" if not key.startswith("metadata.") else key

            if isinstance(value, list):
                # For list values, create OR condition
                should_conditions = [
                    models.FieldCondition(
                        key=field_key, match=models.MatchValue(value=v)
                    )
                    for v in value
                ]
                if should_conditions:
                    must_conditions.append(models.Filter(should=should_conditions))
            else:
                # For single values, create exact match condition
                must_conditions.append(
                    models.FieldCondition(
                        key=field_key, match=models.MatchValue(value=value)
                    )
                )

        if not must_conditions:
            return None

        return models.Filter(must=must_conditions)


@lru_cache
def get_vector_store() -> VectorStore:
    """
    Get or create a VectorStore instance.
    NOTE: This version does not initialize the store, call async_initialize() before using.
    """
    return VectorStore()


async def get_initialized_vector_store() -> VectorStore:
    """
    Get or create a fully initialized VectorStore instance.
    This async function ensures the vector store is properly initialized before returning.
    """
    store = get_vector_store()
    await store.async_initialize()
    return store
