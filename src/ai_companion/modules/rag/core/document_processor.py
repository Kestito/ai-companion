from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
import os

class DocumentProcessor:
    """Handles document processing and chunking for RAG system."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        base_dir: str = "data/documents"
    ):
        """Initialize the document processor.
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            base_dir: Base directory for document loading
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.base_dir = base_dir
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )
        
    def process_text(self, text: str, metadata: Optional[dict] = None) -> List[Document]:
        """Process a single text string into chunks.
        
        Args:
            text: Text content to process
            metadata: Optional metadata to attach to documents
            
        Returns:
            List of Document objects
        """
        return self.text_splitter.create_documents(
            texts=[text],
            metadatas=[metadata or {}]
        )
    
    def process_file(self, file_path: str) -> List[Document]:
        """Process a single file into chunks.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List of Document objects
        """
        loader = TextLoader(file_path)
        documents = loader.load()
        return self.text_splitter.split_documents(documents)
    
    def process_directory(self, directory: Optional[str] = None) -> List[Document]:
        """Process all documents in a directory.
        
        Args:
            directory: Optional directory path, defaults to base_dir
            
        Returns:
            List of Document objects
        """
        dir_path = directory or self.base_dir
        if not os.path.exists(dir_path):
            raise ValueError(f"Directory does not exist: {dir_path}")
            
        loader = DirectoryLoader(
            dir_path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True
        )
        documents = loader.load()
        return self.text_splitter.split_documents(documents) 