"""Enhanced retrieval system combining semantic and keyword search with multi-stage validation."""

from typing import List, Dict, Any, Tuple, Optional
from langchain.schema import Document
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedRetrieval:
    """Enhanced retrieval system with hybrid search and multi-stage validation."""
    
    def __init__(
        self,
        embeddings: Optional[AzureOpenAIEmbeddings] = None,
        model_deployment: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0
    ):
        """Initialize enhanced retrieval system."""
        try:
            # Initialize embeddings
            self.embeddings = embeddings or AzureOpenAIEmbeddings(
                deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
                model=os.getenv("EMBEDDING_MODEL"),
                api_version=os.getenv("AZURE_EMBEDDING_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY")
            )
            
            # Initialize LLM for validation
            self.llm = AzureChatOpenAI(
                deployment_name=model_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                model_name=model_name or os.getenv("LLM_MODEL"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                temperature=temperature
            )
            
            logger.info("Enhanced retrieval system initialized")
            
        except Exception as e:
            logger.error(f"Error initializing enhanced retrieval: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def hybrid_search(
        self,
        query: str,
        docs: List[Document],
        k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        min_score: float = 0.6
    ) -> List[Tuple[Document, float]]:
        """Perform hybrid search combining semantic and keyword matching."""
        try:
            if not query or not docs:
                return []
            
            # Get query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Get document embeddings
            doc_embeddings = []
            for doc in docs:
                if 'embedding' in doc.metadata:
                    doc_embeddings.append(doc.metadata['embedding'])
                else:
                    # Generate embedding if not present
                    embedding = await self.embeddings.aembed_documents([doc.page_content])
                    doc_embeddings.append(embedding[0])
            
            # Calculate semantic similarity scores
            semantic_scores = cosine_similarity([query_embedding], doc_embeddings)[0]
            
            # Calculate keyword similarity scores
            keyword_scores = self._calculate_keyword_scores(query, docs)
            
            # Combine scores
            combined_scores = (
                semantic_weight * semantic_scores +
                keyword_weight * keyword_scores
            )
            
            # Filter and sort results
            results = []
            for i, score in enumerate(combined_scores):
                if score >= min_score:
                    results.append((docs[i], float(score)))
            
            # Sort by score
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Return top k results
            return results[:k]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return []
    
    def _calculate_keyword_scores(
        self,
        query: str,
        docs: List[Document]
    ) -> np.ndarray:
        """Calculate keyword-based similarity scores."""
        try:
            query_terms = set(query.lower().split())
            scores = []
            
            for doc in docs:
                doc_terms = set(doc.page_content.lower().split())
                
                # Calculate Jaccard similarity
                intersection = len(query_terms & doc_terms)
                union = len(query_terms | doc_terms)
                score = intersection / union if union > 0 else 0
                
                scores.append(score)
            
            return np.array(scores)
            
        except Exception as e:
            logger.error(f"Error calculating keyword scores: {str(e)}")
            return np.zeros(len(docs))
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def validate_context(
        self,
        query: str,
        docs: List[Document],
        min_relevance: float = 0.7
    ) -> List[Document]:
        """Validate and filter context relevance."""
        try:
            if not docs:
                return []
            
            validation_prompt = f"""Rate the relevance of each document to the query on a scale of 0-1.
            Query: {query}
            
            Rate ONLY the relevance. Return a JSON array of scores.
            
            Documents:
            {[doc.page_content for doc in docs]}
            
            Scores (JSON array):"""
            
            # Get relevance scores
            response = await self.llm.ainvoke(validation_prompt)
            scores = eval(response.content.strip())
            
            # Filter relevant documents
            relevant_docs = []
            for doc, score in zip(docs, scores):
                if score >= min_relevance:
                    relevant_docs.append(doc)
            
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Error validating context: {str(e)}")
            return docs  # Return original docs on error
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def rerank_results(
        self,
        query: str,
        docs: List[Document]
    ) -> List[Document]:
        """Rerank results using cross-attention scoring."""
        try:
            if not docs:
                return []
            
            rerank_prompt = f"""Rerank these documents based on their relevance to the query.
            Return a JSON array of indices in order of relevance (most relevant first).
            
            Query: {query}
            
            Documents:
            {[doc.page_content for doc in docs]}
            
            Ranked indices (JSON array):"""
            
            # Get reranked indices
            response = await self.llm.ainvoke(rerank_prompt)
            indices = eval(response.content.strip())
            
            # Reorder documents
            reranked_docs = [docs[i] for i in indices]
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Error reranking results: {str(e)}")
            return docs  # Return original order on error 