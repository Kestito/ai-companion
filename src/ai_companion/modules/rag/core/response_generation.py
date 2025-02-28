"""Response generation module with Lithuanian language support and fact-checking."""

from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
from langchain_openai import AzureChatOpenAI
import logging
import os
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from ai_companion.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LithuanianResponseGenerator:
    """Generate responses in Lithuanian with enhanced context awareness."""
    
    def __init__(self, model_deployment=None, model_name=None, temperature=0.0):
        self.llm = AzureChatOpenAI(
            deployment_name=model_deployment or settings.AZURE_OPENAI_DEPLOYMENT,
            model_name=model_name or settings.LLM_MODEL,
            temperature=temperature,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.logger = logging.getLogger(__name__)

    async def generate_response(
        self,
        query: str,
        documents: List[Document],
        context: str = "",
        **kwargs
    ) -> str:
        """Generate a response considering conversation history and context.
        
        Args:
            query: The user's query
            documents: Retrieved relevant documents
            context: Combined conversation history and memory context
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        try:
            # Extract chat history and memory context
            chat_history = ""
            memory_info = ""
            if context:
                parts = context.split("\nMemory Context:\n")
                if len(parts) > 1:
                    chat_history = parts[0].replace("Chat History:\n", "").strip()
                    memory_info = parts[1].strip()

            # Format documents
            doc_texts = []
            for doc in documents:
                text = doc.page_content if hasattr(doc, 'page_content') else doc.text
                metadata = doc.metadata or {}
                source = metadata.get('source', 'Unknown')
                doc_texts.append(f"Source ({source}): {text}")
            
            documents_text = "\n\n".join(doc_texts)

            # Create prompt with enhanced context
            prompt = f"""As a Lithuanian-speaking AI assistant, generate a response to the user's query.
            Consider the conversation history and memory context to maintain continuity.

            Chat History:
            {chat_history}

            Memory Context:
            {memory_info}

            Retrieved Information:
            {documents_text}

            User Query: {query}

            Instructions:
            1. Use the retrieved information to answer the query
            2. Maintain conversation context from chat history
            3. Consider memory context for personalization
            4. Respond in Lithuanian language
            5. Be concise but informative
            6. If information is unclear or missing, acknowledge it

            Response:"""

            # Generate response
            response = await self.llm.ainvoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            self.logger.error(f"Error generating response: {e}", exc_info=True)
            return "Atsiprašau, bet įvyko klaida generuojant atsakymą. Ar galėtumėte perfrazuoti klausimą?"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response_old(
        self,
        query: str,
        docs: List[Document],
        query_intent: Dict[str, str],
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Generate validated Lithuanian response with fact-checking."""
        try:
            if not docs:
                self.logger.warning("No documents provided for response generation")
                return self._create_no_context_response()
            
            try:
                # Extract key information
                key_info = await self._extract_key_info(query, docs)
            except Exception as e:
                self.logger.error(f"Error in key info extraction: {str(e)}")
                key_info = {
                    'facts': [],
                    'concepts': [],
                    'relationships': []
                }
            
            try:
                # Generate initial response
                initial_response = await self._generate_initial_response(
                    query,
                    docs,
                    key_info,
                    query_intent
                )
            except Exception as e:
                self.logger.error(f"Error generating initial response: {str(e)}")
                return self._create_error_response(str(e))
            
            try:
                # Validate response
                validation_result = await self._validate_response(
                    query,
                    initial_response,
                    docs,
                    confidence_threshold
                )
            except Exception as e:
                self.logger.error(f"Error in validation: {str(e)}")
                validation_result = {
                    'is_valid': True,
                    'confidence': 0.4,
                    'details': {},
                    'reason': None
                }
            
            if not validation_result['is_valid']:
                self.logger.warning(f"Response validation failed: {validation_result['reason']}")
                return self._create_fallback_response(validation_result['reason'])
            
            try:
                # Fact check response
                fact_check_result = await self._fact_check_response(
                    initial_response,
                    docs
                )
            except Exception as e:
                self.logger.error(f"Error in fact checking: {str(e)}")
                fact_check_result = {
                    'is_accurate': True,
                    'corrections': [],
                    'unsupported_claims': [],
                    'confidence': 0.4
                }
            
            if not fact_check_result['is_accurate']:
                self.logger.warning("Fact check failed, regenerating with corrections")
                try:
                    # Regenerate response with corrections
                    corrected_response = await self._regenerate_with_corrections(
                        query,
                        initial_response,
                        fact_check_result['corrections'],
                        docs
                    )
                    return corrected_response
                except Exception as e:
                    self.logger.error(f"Error regenerating response: {str(e)}")
                    # Fall back to initial response if regeneration fails
                    return {
                        'response': initial_response,
                        'confidence': validation_result['confidence'],
                        'sources': self._extract_sources(docs),
                        'key_info': key_info,
                        'fact_check': fact_check_result,
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {
                'response': initial_response,
                'confidence': validation_result['confidence'],
                'sources': self._extract_sources(docs),
                'key_info': key_info,
                'fact_check': fact_check_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in response generation: {str(e)}")
            return self._create_error_response(str(e))
    
    async def _extract_key_info(
        self,
        query: str,
        docs: List[Document]
    ) -> Dict[str, Any]:
        """Extract key information from Lithuanian documents."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a JSON generator. Output ONLY valid JSON without any additional text, newlines, or formatting."
                },
                {
                    "role": "user", 
                    "content": f"""Return a JSON object with exactly this structure:
{{
    "facts": ["fact1", "fact2"],
    "concepts": ["concept1", "concept2"],
    "relationships": ["relation1", "relation2"]
}}

Question: {query}

Context:
{[doc.page_content for doc in docs]}"""
                }
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Add debug logging
            self.logger.debug(f"Raw response before JSON parsing: {response.content}")
            
            # Clean the response content
            content = response.content.strip()
            if not content:
                self.logger.error("Received empty response from LLM")
                return {
                    'facts': [],
                    'concepts': [],
                    'relationships': []
                }
            
            # Remove any potential markdown code block markers
            content = content.replace('```json', '').replace('```', '')
            content = content.strip()
            
            try:
                key_info = json.loads(content)
                return key_info
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error: {str(e)}, Content: {content[:200]}...")
                return {
                    'facts': [],
                    'concepts': [],
                    'relationships': []
                }
            
        except Exception as e:
            self.logger.error(f"Error extracting key info: {str(e)}")
            return {
                'facts': [],
                'concepts': [],
                'relationships': []
            }
    
    async def _generate_initial_response(
        self,
        query: str,
        docs: List[Document],
        key_info: Dict[str, Any],
        query_intent: Dict[str, str]
    ) -> str:
        """Generate initial Lithuanian response."""
        try:
            # Prepare context
            facts = '\n'.join([f"- {fact}" for fact in key_info['facts']])
            concepts = '\n'.join([f"- {concept}" for concept in key_info['concepts']])
            
            generate_prompt = """Sugeneruok išsamų atsakymą į klausimą.
            
            Klausimas: {query}
            Klausimo tipas: {query_type}
            Klausimo tikslas: {query_intent}
            
            Pagrindiniai faktai:
            {facts}
            
            Pagrindinės sąvokos:
            {concepts}
            
            Kontekstas:
            {context}
            
            REIKALAVIMAI:
            1. Atsakyk tiksliai ir išsamiai
            2. Naudok tik pateiktą informaciją
            3. Cituok šaltinius kur tinkama
            4. Būk glaustas, bet išsamus
            5. Atitik klausimo tikslą
            6. Naudok tinkamą kalbą ir toną
            
            Atsakymas:"""
            
            response = await self.llm.ainvoke(
                generate_prompt.format(
                    query=query,
                    query_type=query_intent['type'],
                    query_intent=query_intent['intent'],
                    facts=facts,
                    concepts=concepts,
                    context=[doc.page_content for doc in docs]
                )
            )
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating initial response: {str(e)}")
            raise
    
    async def _validate_response(
        self,
        query: str,
        response: str,
        docs: List[Document],
        confidence_threshold: float
    ) -> Dict[str, Any]:
        """Validate Lithuanian response for accuracy and completeness."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a JSON validator. Output ONLY valid JSON without any additional text, newlines, or formatting."
                },
                {
                    "role": "user",
                    "content": f"""Return a JSON object with exactly this structure:
{{
    "tikslumas": 0.95,
    "išsamumas": 0.85,
    "aktualumas": 0.90,
    "šaltinių_pagrįstumas": 0.80
}}

Rate each field from 0 to 1 based on:

Question: {query}
Response to validate: {response}

Source documents:
{[doc.page_content for doc in docs]}"""
                }
            ]
            
            validation_response = await self.llm.ainvoke(messages)
            
            # Add debug logging
            self.logger.debug(f"Raw validation response: {validation_response.content}")
            
            # Clean the response content
            content = validation_response.content.strip()
            if not content:
                self.logger.error("Received empty validation response from LLM")
                return {
                    'is_valid': False,
                    'confidence': 0.0,
                    'reason': 'Empty validation response'
                }
            
            # Remove any potential markdown code block markers
            content = content.replace('```json', '').replace('```', '')
            content = content.strip()
            
            try:
                validation = json.loads(content)
                
                # Calculate overall confidence
                confidence = sum([
                    validation.get('tikslumas', 0),
                    validation.get('išsamumas', 0),
                    validation.get('aktualumas', 0),
                    validation.get('šaltinių_pagrįstumas', 0)
                ]) / 4
                
                return {
                    'is_valid': confidence >= confidence_threshold,
                    'confidence': confidence,
                    'details': validation,
                    'reason': 'Pasitikėjimo lygis žemiau slenksčio' if confidence < confidence_threshold else None
                }
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error in validation: {str(e)}, Content: {content[:200]}...")
                return {
                    'is_valid': False,
                    'confidence': 0.0,
                    'reason': f'Invalid JSON response: {str(e)}'
                }
            
        except Exception as e:
            self.logger.error(f"Error validating response: {str(e)}")
            return {
                'is_valid': False,
                'confidence': 0.0,
                'reason': str(e)
            }
    
    async def _fact_check_response(
        self,
        response: str,
        docs: List[Document]
    ) -> Dict[str, Any]:
        """Fact check Lithuanian response against source documents."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a JSON fact checker. Output ONLY valid JSON without any additional text, newlines, or formatting."
                },
                {
                    "role": "user",
                    "content": f"""Check these facts and return a JSON object with exactly this structure:
{{
    "yra_tikslus": true,
    "pataisymai": [],
    "nepagrįsti_teiginiai": [],
    "pasitikėjimas": 0.95
}}

Response to check:
{response}

Source documents:
{[doc.page_content for doc in docs]}"""
                }
            ]
            
            check_response = await self.llm.ainvoke(messages)
            
            # Add debug logging
            self.logger.debug(f"Raw fact check response: {check_response.content}")
            
            # Clean the response content
            content = check_response.content.strip()
            if not content:
                self.logger.error("Received empty fact check response from LLM")
                return {
                    'is_accurate': True,  # Default to true if check fails
                    'corrections': [],
                    'unsupported_claims': [],
                    'confidence': 0.8  # Reasonable default
                }
            
            # Remove any potential markdown code block markers
            content = content.replace('```json', '').replace('```', '')
            content = content.strip()
            
            try:
                fact_check = json.loads(content)
                return {
                    'is_accurate': fact_check.get('yra_tikslus', True),  # Default to true
                    'corrections': fact_check.get('pataisymai', []),
                    'unsupported_claims': fact_check.get('nepagrįsti_teiginiai', []),
                    'confidence': fact_check.get('pasitikėjimas', 0.8)  # Reasonable default
                }
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error in fact check: {str(e)}, Content: {content[:200]}...")
                return {
                    'is_accurate': True,  # Default to true if parsing fails
                    'corrections': [],
                    'unsupported_claims': [],
                    'confidence': 0.8  # Reasonable default
                }
            
        except Exception as e:
            self.logger.error(f"Error fact checking response: {str(e)}")
            return {
                'is_accurate': True,  # Default to true if check fails
                'corrections': [],
                'unsupported_claims': [],
                'confidence': 0.8  # Reasonable default
            }
    
    async def _regenerate_with_corrections(
        self,
        query: str,
        original_response: str,
        corrections: List[str],
        docs: List[Document]
    ) -> Dict[str, Any]:
        """Regenerate Lithuanian response with corrections."""
        try:
            corrections_text = '\n'.join([f"- {correction}" for correction in corrections])
            
            regenerate_prompt = """Sugeneruok atsakymą iš naujo su šiais pataisymais.
            
            Originalus klausimas: {query}
            Originalus atsakymas: {original_response}
            
            Reikalingi pataisymai:
            {corrections}
            
            Šaltinių dokumentai:
            {docs}
            
            Pataisytas atsakymas:"""
            
            response = await self.llm.ainvoke(
                regenerate_prompt.format(
                    query=query,
                    original_response=original_response,
                    corrections=corrections_text,
                    docs=[doc.page_content for doc in docs]
                )
            )
            corrected_response = response.content.strip()
            
            return {
                'response': corrected_response,
                'corrections_applied': corrections,
                'original_response': original_response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error regenerating response: {str(e)}")
            return self._create_error_response(str(e))
    
    def _extract_sources(self, docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract source information from documents."""
        try:
            sources = []
            for doc in docs:
                source = {
                    'content': doc.page_content[:200] + '...',  # Truncate for brevity
                    'metadata': doc.metadata
                }
                sources.append(source)
            return sources
        except Exception as e:
            self.logger.error(f"Error extracting sources: {str(e)}")
            return []
    
    def _create_no_context_response(self) -> Dict[str, Any]:
        """Create Lithuanian response for no context case."""
        return {
            'response': "Atsiprašau, bet neturiu pakankamai informacijos tiksliai atsakyti į jūsų klausimą.",
            'confidence': 0.0,
            'sources': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_fallback_response(self, reason: str) -> Dict[str, Any]:
        """Create Lithuanian fallback response."""
        return {
            'response': f"Atsiprašau, bet negaliu pateikti visiškai tikslaus atsakymo, nes: {reason}",
            'confidence': 0.0,
            'sources': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create Lithuanian error response."""
        return {
            'response': "Atsiprašau, bet įvyko klaida apdorojant jūsų klausimą. Prašome bandyti dar kartą.",
            'error': error,
            'confidence': 0.0,
            'timestamp': datetime.now().isoformat()
        }

    async def _generate_response(
        self,
        query: str,
        documents: List[Document],
        memory_context: Optional[str] = None
    ) -> str:
        """
        Generate a response based on the provided user query and relevant documents.

        Args:
            query: The user's query string
            documents: A list of Document objects containing relevant information
            memory_context: Optional conversation memory context

        Returns:
            str: The generated response text
        """
        try:
            # Log the number of documents passed to response generation
            self.logger.info(f"Generating response from {len(documents)} documents")

            # Format documents for the response
            formatted_documents = []
            vector_count = 0
            keyword_count = 0
            # Track URLs for source attribution
            source_urls = []

            for i, doc in enumerate(documents):
                # Get source type with fallback to 'vector' if not specified
                metadata = doc.metadata or {}
                search_type = metadata.get('search_type', 'vector')
                
                # Count by search type
                if search_type == 'vector':
                    vector_count += 1
                elif search_type == 'keyword':
                    keyword_count += 1
                
                # Collect URL and score for source attribution
                if 'url' in metadata and metadata['url']:
                    source_urls.append({
                        'url': metadata['url'],
                        'title': metadata.get('title', 'Unknown Source'),
                        'score': metadata.get('score', 0.0)
                    })
                    
                # Format document with page content and metadata
                formatted_doc = f"Document {i+1} [Source: {search_type}]:\n{doc.page_content}\n"
                formatted_documents.append(formatted_doc)

            formatted_docs_text = "\n".join(formatted_documents)

            # Construct prompt with Lithuanian language guidance
            system_message = """You are an AI assistant that provides helpful, accurate, and friendly responses to user questions.
You work for an organization helping Lithuanian cancer patients, so respond in Lithuanian language.
Make your response helpful, concise, accurate, and in a warm, empathetic tone appropriate for medical information.

Base your response ONLY on the provided documents. If you don't know or the documents don't contain relevant information, say so clearly.
DO NOT make up information or draw from knowledge outside the provided documents."""

            user_message = f"""Answer the following query: "{query}"

Based on these documents:
{formatted_docs_text}"""

            # Add memory context if provided
            if memory_context:
                user_message += f"\n\nConsider this conversation context when answering:\n{memory_context}"

            # Generate response with LLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.llm.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Format final response
            response_text = response_text.replace("\n\n", "\n")
            
            # Add source attribution
            source_summary = f"\n\nInformation retrieved from {len(documents)} documents"
            if vector_count > 0 and keyword_count > 0:
                source_summary += f" using semantic search (Qdrant) ({vector_count} results) and keyword search (Supabase) ({keyword_count} results)"
            elif vector_count > 0:
                source_summary += f" using semantic search (Qdrant) (Collection: Information)"
            elif keyword_count > 0:
                source_summary += f" using keyword search (Supabase) ({keyword_count} results)"
            
            # Add top 2 sources with URLs
            if source_urls:
                # Sort sources by score in descending order
                sorted_sources = sorted(source_urls, key=lambda x: x['score'], reverse=True)
                # Get top 2 sources
                top_sources = sorted_sources[:2]
                source_summary += "\n\nŠaltiniai:"
                for idx, source in enumerate(top_sources, 1):
                    source_summary += f"\n{idx}. {source['title']}: {source['url']}"
            
            response_text += source_summary
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"Error in response generation: {e}", exc_info=True)
            return f"Nepavyko sugeneruoti detalaus atsakymo. Bandykite dar kartą arba užduokite kitą klausimą.\n\nInformation retrieved from {len(documents)} documents using semantic search (Qdrant) (Collection: Information)." 