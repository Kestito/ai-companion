from typing import Dict, List, Optional, Tuple
from langchain_openai import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.prompts import PromptTemplate
import os
import logging

from .vector_store import VectorStoreManager, get_vector_store_instance

# Add singleton instance
_rag_chain_instance = None

def get_rag_chain(
    model_deployment: Optional[str] = None,
    model_name: Optional[str] = None,
    prompt_template: Optional[str] = None
) -> 'RAGChain':
    """Get or create a singleton instance of RAGChain.
    
    Args:
        model_deployment: Optional Azure model deployment name
        model_name: Optional model name
        prompt_template: Optional custom prompt template
        
    Returns:
        RAGChain instance
    """
    global _rag_chain_instance
    if _rag_chain_instance is None:
        vector_store = get_vector_store_instance()
        _rag_chain_instance = RAGChain(
            vector_store=vector_store,
            model_deployment=model_deployment,
            model_name=model_name,
            prompt_template=prompt_template
        )
    return _rag_chain_instance

class RAGChain:
    """Manages the RAG (Retrieval Augmented Generation) process."""
    
    DEFAULT_PROMPT = """Naudok pateiktą kontekstą, kad atsakytum į klausimą. 
    Jei nežinai atsakymo, taip ir pasakyk - nesugalvok atsakymo.
    Visada atsakyk lietuvių kalba.
    
    Kontekstas:
    {context}
    
    Klausimas: {question}
    
    Atsakymas: """
    
    def __init__(
        self,
        vector_store: VectorStoreManager,
        model_deployment: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_template: Optional[str] = None
    ):
        """Initialize the RAG chain."""
        self.vector_store = vector_store
        
        # Initialize language model
        self.llm = AzureChatOpenAI(
            deployment_name=model_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            model_name=model_name or os.getenv("LLM_MODEL"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.1
        )
        
        # Create prompt template
        self.prompt = PromptTemplate(
            template=prompt_template or self.DEFAULT_PROMPT,
            input_variables=["context", "question"]
        )
        
        # Initialize retrieval chain
        self.retriever = vector_store.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
    async def query(
        self,
        question: str,
        filter: Optional[dict] = None
    ) -> Tuple[str, List[Document]]:
        """Query the RAG system with proper error handling."""
        try:
            # First get relevant documents
            docs = await self.retriever.aget_relevant_documents(question)
            
            if not docs:
                return "Atsiprašau, bet neturiu pakankamai informacijos atsakyti į šį klausimą.", []
            
            # Format context from documents
            context = "\n".join(doc.page_content for doc in docs)
            
            # Format prompt
            formatted_prompt = self.prompt.format(
                context=context,
                question=question
            )
            
            # Get response from LLM
            response = await self.llm.ainvoke(formatted_prompt)
            
            return response.content, docs
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return "Atsiprašau, įvyko klaida ieškant informacijos. Prašome bandyti vėliau.", []
        
    def update_prompt(self, new_template: str) -> None:
        """Update the prompt template.
        
        Args:
            new_template: New prompt template string
        """
        self.prompt = PromptTemplate(
            template=new_template,
            input_variables=["context", "question"]
        )
        # Reinitialize chain with new prompt
        self.retriever = self.vector_store.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        ) 