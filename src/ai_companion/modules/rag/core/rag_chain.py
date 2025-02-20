from typing import Dict, List, Optional, Tuple, AsyncIterator
from langchain_openai import AzureChatOpenAI
from langchain.schema import Document
from langchain.prompts import PromptTemplate
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from .vector_store import VectorStoreManager, get_vector_store_instance

# Configure logging at module level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singleton instance
_rag_chain_instance = None

def get_rag_chain(
    model_deployment: Optional[str] = None,
    model_name: Optional[str] = None,
    prompt_template: Optional[str] = None
) -> 'RAGChain':
    """Get or create a singleton instance of RAGChain."""
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
    
    Papildomas kontekstas iš atminties:
    {memory_context}
    
    Atsakymas: """
    
    def __init__(
        self,
        vector_store: VectorStoreManager,
        model_deployment: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_template: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.1
    ):
        """Initialize the RAG chain."""
        self.vector_store = vector_store
        self.max_tokens = max_tokens
        
        # Initialize language model
        self.llm = AzureChatOpenAI(
            deployment_name=model_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            model_name=model_name or os.getenv("LLM_MODEL"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Create prompt template
        self.prompt = PromptTemplate(
            template=prompt_template or self.DEFAULT_PROMPT,
            input_variables=["context", "question", "memory_context"]
        )
        
        # Initialize retriever with basic configuration
        self.retriever = vector_store.vector_store.as_retriever(
            search_kwargs={"k": 5}
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def query(
        self,
        question: str,
        memory_context: str = "",
        filter: Optional[dict] = None
    ) -> Tuple[str, List[Document]]:
        """Query the RAG system with robust error handling."""
        try:
            # Get relevant documents
            docs = await self.retriever.aget_relevant_documents(question)
            
            if not docs:
                logger.info("No relevant documents found for query")
                return "Atsiprašau, bet neturiu pakankamai informacijos atsakyti į šį klausimą.", []
            
            # Format context from documents
            context_parts = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                source = metadata.get('url', 'Nežinomas šaltinis')
                date = metadata.get('processed_at', 'Data nenurodyta')
                context_parts.append(f"{i}. Šaltinis: {source} ({date})\n{doc.page_content}")
            
            context = "\n\n".join(context_parts)
            
            # Format prompt
            formatted_prompt = self.prompt.format(
                context=context,
                question=question,
                memory_context=memory_context or "Nėra papildomo konteksto."
            )
            
            # Get response from LLM
            response = await self.llm.ainvoke(formatted_prompt)
            
            logger.info(f"Successfully generated response for query: {question[:50]}...")
            return response.content, docs
            
        except Exception as e:
            logger.error(f"Error in RAG query: {str(e)}", exc_info=True)
            return "Atsiprašau, įvyko klaida ieškant informacijos. Prašome bandyti vėliau.", []
    
    def update_prompt(self, new_template: str) -> None:
        """Update the prompt template."""
        if "{context}" not in new_template or "{question}" not in new_template:
            raise ValueError("New template must contain {context} and {question} variables")
            
        self.prompt = PromptTemplate(
            template=new_template,
            input_variables=["context", "question", "memory_context"]
        )
