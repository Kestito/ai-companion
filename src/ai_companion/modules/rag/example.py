import os
from pathlib import Path
from dotenv import load_dotenv

from core.document_processor import DocumentProcessor
from core.vector_store import VectorStoreManager
from core.rag_chain import RAGChain

def main():
    """Example usage of the RAG system."""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    print("Initializing RAG components...")
    
    # Create document processor
    doc_processor = DocumentProcessor(
        chunk_size=1000,
        chunk_overlap=200,
        base_dir="data/documents"
    )
    
    # Create vector store manager
    vector_store = VectorStoreManager(
        collection_name="test_documents"
    )
    
    # Create RAG chain
    rag_chain = RAGChain(
        vector_store=vector_store
    )
    
    # Process and index some example documents
    print("\nProcessing example documents...")
    
    # Create example documents directory if it doesn't exist
    docs_dir = Path("data/documents")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create an example document
    example_doc = docs_dir / "example.txt"
    example_content = """
    This is an example document about artificial intelligence.
    AI systems can be broadly categorized into narrow AI and general AI.
    Narrow AI is designed for specific tasks, while general AI aims to match human intelligence.
    Machine learning is a subset of AI that focuses on learning from data.
    Deep learning is a type of machine learning that uses neural networks.
    """
    example_doc.write_text(example_content)
    
    # Process and index the documents
    documents = doc_processor.process_directory()
    vector_store.add_documents(documents)
    
    print(f"Indexed {len(documents)} document chunks")
    
    # Example queries
    example_queries = [
        "What is the difference between narrow AI and general AI?",
        "What is machine learning?",
        "How does deep learning relate to AI?"
    ]
    
    print("\nTesting example queries:")
    for query in example_queries:
        print(f"\nQuery: {query}")
        answer, sources = rag_chain.query(query)
        print(f"Answer: {answer}")
        print("\nSources:")
        for source in sources:
            print(f"- {source.page_content[:100]}...")

if __name__ == "__main__":
    main() 