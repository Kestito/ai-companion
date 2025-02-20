from typing import List, Optional, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
import os
import logging
from datetime import datetime
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Enhanced document processing and chunking for RAG system."""
    
    def __init__(
        self,
        chunk_size: int = 512,  # Optimized for OpenAI embeddings
        chunk_overlap: int = 100,  # Balanced overlap for context
        base_dir: str = "data/documents",
        max_chunks: int = 1000,  # Limit chunks per document
        min_chunk_size: int = 100  # Minimum chunk size
    ):
        """Initialize the enhanced document processor."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.base_dir = base_dir
        self.max_chunks = max_chunks
        self.min_chunk_size = min_chunk_size
        
        # Initialize text splitter with enhanced configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
    
    def _enhance_metadata(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create enhanced metadata for document."""
        base_metadata = metadata or {}
        
        # Calculate content hash
        content_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Enhance with additional metadata
        enhanced_metadata = {
            **base_metadata,
            "content_hash": content_hash,
            "processed_at": datetime.now().isoformat(),
            "char_count": len(text),
            "word_count": len(text.split()),
            "language": base_metadata.get("language", "lt"),  # Default to Lithuanian
            "processor_version": "2.0",
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
        
        return enhanced_metadata
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Process text with enhanced metadata and chunking."""
        try:
            # Enhance metadata
            enhanced_metadata = self._enhance_metadata(text, metadata)
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Limit number of chunks
            if len(chunks) > self.max_chunks:
                logger.warning(f"Document exceeded max chunks ({len(chunks)}), truncating to {self.max_chunks}")
                chunks = chunks[:self.max_chunks]
            
            # Create documents with chunk-specific metadata
            documents = []
            for i, chunk in enumerate(chunks):
                if len(chunk) < self.min_chunk_size:
                    logger.debug(f"Skipping chunk {i} - too small ({len(chunk)} chars)")
                    continue
                    
                chunk_metadata = {
                    **enhanced_metadata,
                    "chunk_number": i,
                    "chunk_total": len(chunks),
                    "chunk_hash": hashlib.md5(chunk.encode()).hexdigest()
                }
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))
            
            logger.info(f"Processed text into {len(documents)} chunks")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process_file(
        self,
        file_path: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Process file with enhanced error handling and metadata."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get file metadata
            file_stats = os.stat(file_path)
            file_metadata = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": file_stats.st_size,
                "file_created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "file_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                **(additional_metadata or {})
            }
            
            # Load and process file
            loader = TextLoader(file_path)
            raw_documents = loader.load()
            
            processed_documents = []
            for doc in raw_documents:
                chunks = await self.process_text(
                    doc.page_content,
                    {**doc.metadata, **file_metadata}
                )
                processed_documents.extend(chunks)
            
            logger.info(f"Processed file {file_path} into {len(processed_documents)} chunks")
            return processed_documents
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process_directory(
        self,
        directory: Optional[str] = None,
        glob_pattern: str = "**/*.txt",
        batch_size: int = 10
    ) -> List[Document]:
        """Process directory with batching and enhanced error handling."""
        try:
            dir_path = directory or self.base_dir
            if not os.path.exists(dir_path):
                raise ValueError(f"Directory does not exist: {dir_path}")
            
            # Load files with progress tracking
            loader = DirectoryLoader(
                dir_path,
                glob=glob_pattern,
                loader_cls=TextLoader,
                show_progress=True
            )
            
            all_files = loader.load()
            processed_documents = []
            
            # Process in batches
            for i in range(0, len(all_files), batch_size):
                batch = all_files[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} of {(len(all_files) + batch_size - 1)//batch_size}")
                
                for doc in batch:
                    try:
                        chunks = await self.process_text(doc.page_content, doc.metadata)
                        processed_documents.extend(chunks)
                    except Exception as e:
                        logger.error(f"Error processing document in batch: {str(e)}")
                        continue
            
            logger.info(f"Processed {len(all_files)} files into {len(processed_documents)} chunks")
            return processed_documents
            
        except Exception as e:
            logger.error(f"Error processing directory {directory}: {str(e)}")
            raise
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about processor configuration."""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "max_chunks": self.max_chunks,
            "min_chunk_size": self.min_chunk_size,
            "base_dir": self.base_dir,
            "separators": self.text_splitter.separators,
            "version": "2.0"
        } 