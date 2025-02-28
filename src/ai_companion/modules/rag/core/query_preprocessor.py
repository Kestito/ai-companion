"""Query preprocessing module with advanced Lithuanian language support."""

from typing import List, Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
import logging
import os
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LithuanianQueryPreprocessor:
    """Advanced query preprocessing with Lithuanian language support."""
    
    def __init__(
        self,
        model_deployment: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0
    ):
        """Initialize query preprocessor."""
        try:
            # Initialize LLM for query processing
            self.llm = AzureChatOpenAI(
                deployment_name=model_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                model_name=model_name or os.getenv("LLM_MODEL"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                temperature=temperature
            )
            
            # Initialize Lithuanian character mappings and common misspellings
            self.char_mappings = {
                'a': ['ą', 'a'],
                'c': ['č', 'c'],
                'e': ['ę', 'ė', 'e'],
                'i': ['į', 'i'],
                's': ['š', 's'],
                'u': ['ų', 'ū', 'u'],
                'z': ['ž', 'z'],
            }
            
            # Expanded misspellings with common real-world errors
            self.common_misspellings = {
                # POLA related
                'kortele': 'kortelė',
                'pola': 'POLA',
                'pola kortele': 'POLA kortelė',
                
                # Common question words
                'ka': 'ką',
                'kur': 'kur',
                'kaip': 'kaip',
                'kada': 'kada',
                'kodel': 'kodėl',
                'kiek': 'kiek',
                
                # Common location errors
                'vilnius': 'Vilnius',
                'kaunas': 'Kaunas',
                'klaipeda': 'Klaipėda',
                'klaipedoje': 'Klaipėdoje',
                'miegste': 'mieste',
                'miestas': 'miestas',
                
                # Medical terms
                'vezys': 'vėžys',
                'veziu': 'vėžiu',
                'vezio': 'vėžio',
                'smegenu': 'smegenų',
                'sergant': 'sergant',
                
                # Benefits/services
                'ismokos': 'išmokos',
                'paslaugos': 'paslaugos',
                'gydymas': 'gydymas',
                'savanoris': 'savanoris',
                
                # Common question patterns
                'kur gauti': 'kaip gauti',
                'kur rasti': 'kaip rasti',
                'kiek kainuoja': 'kaina',
            }
            
            # Entity recognition patterns
            self.entity_patterns = {
                'pola_card': r'(?i)pola\s*kort[eė]l[eė]',
                'cancer': r'(?i)v[eė][zž][yį]|onkologin[eė]|diagnoz[eė]',
                'brain': r'(?i)smegen[uų]',
                'contact': r'(?i)kontakt[aą]|susisiek[ti]|telefon[aą]|el[\.]*\s*pa[sš]t[aą]',
                'location': r'(?i)adres[aą]|viet[aą]|kur\s+yra|vilnius|kaunas|klaip[eė]d[ao]j?e?',
                'benefits': r'(?i)i[sš]mok[ao]s|privileg|mokes[čc]i[aų]|nuolaid[aų]',
                'volunteer': r'(?i)savanor[iį]|pagalb[aą]|padėt[iį]',
            }
            
            # LLM normalization prompt
            self.normalization_prompt = """
            You are a Lithuanian language correction assistant. 
            Your task is to correct the Lithuanian text by:
            1. Adding proper diacritical marks (ą, č, ę, ė, į, š, ų, ū, ž)
            2. Fixing misspellings
            3. Applying proper capitalization for names (like POLA, Vilnius, Klaipėda)
            
            Original text: "{text}"
            
            Provide ONLY the corrected text without explanations or comments.
            """
            
            logger.info("Lithuanian query preprocessor initialized with enhanced language support")
            
        except Exception as e:
            logger.error(f"Error initializing query preprocessor: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process_query(
        self,
        query: str,
        context_type: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs  # Add kwargs to handle additional parameters
    ) -> Dict[str, Any]:
        """Process and enhance Lithuanian query.
        
        Args:
            query: The query to process
            context_type: Optional type of context
            context: Optional context string
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Dictionary containing processed query information
        """
        try:
            # Basic validation
            if not query or not isinstance(query, str):
                return {
                    'success': False,
                    'error': 'Invalid query',
                    'enhanced_query': '',
                    'variations': [],
                    'intent': 'unknown'
                }
            
            # Clean query (whitespace, special chars)
            cleaned_query = self._clean_query(query)
            
            # Apply basic rule-based corrections
            corrected_query = self._correct_misspellings(cleaned_query)
            
            # Apply LLM-based normalization
            # We use try-except to fall back to rule-based if LLM normalization fails
            try:
                normalized_query = await self._normalize_with_llm(corrected_query)
                logger.info(f"LLM normalization: '{corrected_query}' -> '{normalized_query}'")
                if normalized_query and normalized_query.strip():
                    corrected_query = normalized_query
            except Exception as e:
                logger.warning(f"LLM normalization failed, falling back to rule-based: {str(e)}")
                # Continue with rule-based correction
            
            # Detect entities in the query
            entities = self._detect_entities(corrected_query)
            
            # Generate query variations
            variations = await self._generate_variations(corrected_query)
            
            # Classify intent
            intent = await self._classify_intent(corrected_query)
            
            # Enhance query with context
            enhanced_query = await self._enhance_query(corrected_query, context_type, entities)
            
            # Add the original query to variations if it's different from corrected
            if query.lower().strip() != corrected_query.lower().strip() and query.lower().strip() not in variations:
                variations.append(query.lower().strip())
            
            # Log the processing results
            logger.info(f"Query processing results:")
            logger.info(f"Original: '{query}'")
            logger.info(f"Corrected: '{corrected_query}'")
            logger.info(f"Enhanced: '{enhanced_query}'")
            logger.info(f"Variations: {variations[:3]}...")
            logger.info(f"Detected entities: {entities}")
            
            return {
                'success': True,
                'enhanced_query': enhanced_query,
                'variations': variations,
                'intent': intent,
                'entities': entities,
                'original_query': query,
                'corrected_query': corrected_query
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return {
                'success': True,  # Still return success to continue processing
                'enhanced_query': query,  # Use original query
                'variations': [query],  # Single variation
                'intent': 'unknown'
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'enhanced_query': '',
                'variations': [],
                'intent': 'unknown'
            }
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
    async def _normalize_with_llm(self, query: str) -> str:
        """Use LLM to normalize and correct Lithuanian text.
        
        Args:
            query: The query text to normalize
            
        Returns:
            Normalized text with proper Lithuanian diacritics and spelling
        """
        try:
            # Skip LLM processing for very short queries or those that look like they might be
            # commands or non-Lithuanian text
            if len(query) < 3 or not any(c.isalpha() for c in query):
                return query
                
            prompt = self.normalization_prompt.format(text=query)
            response = await self.llm.ainvoke(prompt)
            
            normalized_text = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
            # Validate the response - if it's empty or too different from the original, revert
            if not normalized_text or len(normalized_text) < len(query) // 2:
                logger.warning(f"LLM normalization returned suspicious result: '{normalized_text}'")
                return query
                
            return normalized_text
        except Exception as e:
            logger.error(f"Error in LLM normalization: {str(e)}")
            raise
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query text."""
        # Remove extra whitespace
        query = " ".join(query.split())
        # Keep special characters for LLM processing, just remove excessive punctuation
        query = re.sub(r'[!@#$%^&*(){}\[\]<>:;"\']', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        return query
    
    def _normalize_lithuanian_chars(self, text: str) -> str:
        """Normalize Lithuanian characters to their basic Latin equivalents."""
        normalized = text
        for latin, lithuanian_chars in self.char_mappings.items():
            for lithuanian in lithuanian_chars:
                normalized = normalized.replace(lithuanian, latin)
        return normalized
    
    def _correct_misspellings(self, query: str) -> str:
        """Correct common Lithuanian misspellings."""
        corrected = query.lower()
        
        # Apply common misspelling corrections
        for misspelling, correction in self.common_misspellings.items():
            corrected = re.sub(r'\b' + misspelling + r'\b', correction, corrected)
        
        # Special case for "POLA" to ensure correct capitalization
        if 'pola' in corrected.lower():
            corrected = re.sub(r'\bpola\b', 'POLA', corrected)
            if 'pola kortelė' in corrected.lower() or 'pola kortele' in corrected.lower():
                corrected = re.sub(r'(?i)pola\s+kort[eė]l[eė]', 'POLA kortelė', corrected)
        
        return corrected
    
    def _detect_entities(self, query: str) -> Dict[str, bool]:
        """Detect entities in the query."""
        entities = {}
        
        for entity_name, pattern in self.entity_patterns.items():
            entities[entity_name] = bool(re.search(pattern, query))
            
        return entities
    
    async def _generate_variations(self, query: str) -> List[str]:
        """Generate query variations to handle different ways users might phrase questions."""
        try:
            variations = [query]  # Always include original query
            
            # Add normalized version (without Lithuanian characters)
            normalized = self._normalize_lithuanian_chars(query)
            if normalized != query:
                variations.append(normalized)
            
            # Add common phrase variations
            phrase_variations = {
                "kaip": ["kokiu būdu", "kaip galima", "kokiu būdu galima"],
                "kur": ["kokioje vietoje", "kur galima", "kur yra"],
                "kada": ["kuriuo metu", "kada galima", "kokiu laiku"],
                "kiek kainuoja": ["kokia kaina", "kiek reikia mokėti", "kaina"],
                "gauti": ["įsigyti", "turėti", "prašyti"],
                "sergant": ["susirgus", "kai sergu", "gydant"],
                "išmokos": ["mokėjimai", "pašalpos", "kompensacijos"],
            }
            
            # Apply phrase variations
            for phrase, replacements in phrase_variations.items():
                if phrase in query:
                    for replacement in replacements:
                        variations.append(query.replace(phrase, replacement))
            
            # Handle specific entity variations
            if "pola" in query.lower() or "POLA" in query:
                # Add POLA-specific variations
                pola_variations = [
                    "POLA kortelė",
                    "POLA kortele",
                    "pola kortelė",
                    "pola kortele",
                    "POLA card",
                ]
                
                if "kortel" in query.lower():
                    # Add variations with the full POLA card phrase
                    variations.extend(pola_variations)
                else:
                    # Add variations just with POLA
                    variations.append("POLA")
            
            # Add variations for medical terms
            if any(term in query.lower() for term in ["vėžys", "vezys", "vežys", "vėžio", "vezio"]):
                cancer_variations = [
                    query.replace("vezys", "vėžys"),
                    query.replace("vežys", "vėžys"),
                    query.replace("vezio", "vėžio"),
                    query.replace("vežio", "vėžio"),
                ]
                variations.extend([v for v in cancer_variations if v not in variations])
            
            # Add variations for locations
            if any(city in query.lower() for city in ["vilnius", "kaunas", "klaipeda", "klaipėda"]):
                city_variations = [
                    query.replace("klaipeda", "Klaipėda"),
                    query.replace("klaipedoje", "Klaipėdoje"),
                    query.replace("vilnius", "Vilnius"),
                    query.replace("kaunas", "Kaunas"),
                ]
                variations.extend([v for v in city_variations if v not in variations])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_variations = []
            for v in variations:
                if v not in seen and v.strip():
                    unique_variations.append(v)
                    seen.add(v)
            
            return unique_variations
            
        except Exception as e:
            logger.error(f"Error generating variations: {str(e)}")
            return [query]  # Return original query on error
    
    async def _classify_intent(self, query: str) -> str:
        """Classify query intent."""
        try:
            query_lower = query.lower()
            
            # Enhanced rule-based intent classification
            if any(word in query_lower for word in ["kaip", "kokiu būdu", "kaip galima"]):
                return "how_to"
            elif any(word in query_lower for word in ["kur", "kokioje vietoje", "kur yra"]):
                return "location"
            elif any(word in query_lower for word in ["kada", "kuriuo metu", "kokiu laiku"]):
                return "time"
            elif any(word in query_lower for word in ["kas", "koks", "kokia"]):
                return "what"
            elif any(word in query_lower for word in ["kiek kainuoja", "kaina", "mokėti"]):
                return "price"
            elif any(word in query_lower for word in ["privalumai", "nauda", "naudinga", "išmokos"]):
                return "benefits"
            elif any(word in query_lower for word in ["vėžys", "vezys", "vežys", "liga", "sergant"]):
                return "medical"
            elif any(word in query_lower for word in ["savanoris", "savanoriai", "padėti"]):
                return "volunteer"
            else:
                return "general"
                
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return "unknown"
    
    async def _enhance_query(self, query: str, context_type: Optional[str] = None, entities: Dict[str, bool] = None) -> str:
        """Enhance query with context and entity information."""
        try:
            enhanced_query = query
            entities = entities or {}
            
            # Add context-specific enhancements
            if context_type == "pola" or entities.get('pola_card', False):
                if "pola" in query.lower() and "kortel" in query.lower():
                    # Make sure POLA is capitalized and kortelė has proper Lithuanian characters
                    enhanced_query = re.sub(r'(?i)pola\s*kort[eė]l[eė]', "POLA kortelė", enhanced_query)
                else:
                    enhanced_query = f"POLA kortelė {enhanced_query}"
            elif context_type == "technical":
                enhanced_query = f"techninė informacija {enhanced_query}"
            elif entities.get('cancer', False) and entities.get('brain', False):
                enhanced_query = f"smegenų vėžys {enhanced_query}"
            elif entities.get('benefits', False):
                if "vilnius" in query.lower() or "vilniaus" in query.lower():
                    enhanced_query = f"išmokos Vilniaus mieste {enhanced_query}"
            elif entities.get('volunteer', False):
                if "klaipeda" in query.lower() or "klaipėda" in query.lower():
                    enhanced_query = f"POLA savanoriai Klaipėdoje {enhanced_query}"
            
            return enhanced_query
            
        except Exception as e:
            logger.error(f"Error enhancing query: {str(e)}")
            return query  # Return original query on error 