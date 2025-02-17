from typing import Dict, List, Optional, Tuple
from langchain_openai import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.prompts import PromptTemplate
import os

from .vector_store import VectorStoreManager

class RAGChain:
    """Manages the RAG (Retrieval Augmented Generation) process."""
    
    DEFAULT_PROMPT = """Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    {context}
    
    Question: {question}
    Answer: """
    
    def __init__(
        self,
        vector_store: VectorStoreManager,
        model_deployment: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_template: Optional[str] = None
    ):
        """Initialize the RAG chain.
        
        Args:
            vector_store: Vector store manager instance
            model_deployment: Optional Azure model deployment name
            model_name: Optional model name
            prompt_template: Optional custom prompt template
        """
        self.vector_store = vector_store
        
        # Initialize language model
        self.llm = AzureChatOpenAI(
            deployment_name=model_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            model_name=model_name or os.getenv("LLM_MODEL"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        
        # Create prompt template
        self.prompt = PromptTemplate(
            template=prompt_template or self.DEFAULT_PROMPT,
            input_variables=["context", "question"]
        )
        
        # Initialize retrieval chain
        self.chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vector_store.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt}
        )
        
    async def query(
        self,
        question: str,
        filter: Optional[dict] = None
    ) -> Tuple[str, List[Document]]:
        """Query the RAG system.
        
        Args:
            question: User question
            filter: Optional filter for retrieval
            
        Returns:
            Tuple of (answer, source documents)
        """
        result = await self.chain.ainvoke({"query": question})
        return result["result"], result["source_documents"]
        
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
        self.chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.vector_store.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt}
        ) 