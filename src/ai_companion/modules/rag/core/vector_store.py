from typing import List, Optional
from langchain_qdrant import QdrantVectorStore
from langchain_openai import AzureOpenAIEmbeddings
from langchain.schema import Document
from qdrant_client import QdrantClient, models
import os
import uuid
import hashlib

class VectorStoreManager:
    """Manages vector store operations using Qdrant."""
    
    def __init__(
        self,
        collection_name: str = "documents",
        embedding_deployment: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """Initialize the vector store manager.
        
        Args:
            collection_name: Name of the Qdrant collection
            embedding_deployment: Optional Azure embedding deployment name
            embedding_model: Optional embedding model name
        """
        self.collection_name = collection_name
        
        # Initialize embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            deployment=embedding_deployment or os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            model=embedding_model or os.getenv("EMBEDDING_MODEL"),
            api_version=os.getenv("AZURE_EMBEDDING_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            chunk_size=1000
        )
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Ensure collection exists
        self._ensure_collection()
        
        # Initialize vector store with custom id generator
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embeddings,
            content_payload_key="content",
            metadata_payload_key="metadata"
        )
    
    def _generate_document_id(self, document: Document) -> str:
        """Generate a deterministic UUID for a document.
        
        Args:
            document: Document to generate ID for
            
        Returns:
            UUID string
        """
        # Create a unique string from document content and metadata
        unique_str = f"{document.page_content}_{str(document.metadata)}"
        return str(uuid.UUID(hashlib.md5(unique_str.encode()).hexdigest()))
        
    def _ensure_collection(self) -> None:
        """Ensure the collection exists, create it if it doesn't."""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # Get sample embedding to determine dimensions
            sample_text = "sample text"
            sample_embedding = self.embeddings.embed_query(sample_text)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=len(sample_embedding),  # Use actual embedding dimensions
                    distance=models.Distance.COSINE
                )
            )
        
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store with proper ID generation.
        
        Args:
            documents: List of Document objects to add
        """
        try:
            # Add documents with generated IDs
            for doc in documents:
                doc_id = self._generate_document_id(doc)
                self.vector_store.add_documents([doc], ids=[doc_id])
            print(f"Successfully added {len(documents)} documents to collection {self.collection_name}")
        except Exception as e:
            print(f"Error adding documents to collection: {str(e)}")
            raise
        
    def similarity_search(
        self,
        query: str,
        k: int = 3,
        filter: Optional[dict] = None
    ) -> List[Document]:
        """Perform similarity search.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional filter conditions
            
        Returns:
            List of similar documents
        """
        return self.vector_store.similarity_search(
            query,
            k=k,
            filter=filter
        )
        
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
        
    def get_collection_info(self) -> dict:
        """Get information about the collection.
        
        Returns:
            Collection information
        """
        return self.client.get_collection(self.collection_name) 