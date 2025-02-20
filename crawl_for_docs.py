import os
import re
import sys
import json
import asyncio
from qdrant_client import QdrantClient, models
import requests
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv
from asyncio import Semaphore, Lock
import time
import logging
from supabase import create_client, Client
from openai import AsyncAzureOpenAI
from langchain.schema import Document
from tenacity import retry, stop_after_attempt, wait_exponential
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import xml.etree.ElementTree as ET
import aiohttp
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants aligned with OpenAI embeddings and Qdrant configuration
VECTOR_SIZE = 1536  # Must match Qdrant vector size
MAX_TOKENS_PER_CHUNK = 8191  # OpenAI's limit is 8192, leave 1 for safety
OPTIMAL_TOKENS_PER_VECTOR = 512  # OpenAI's recommended tokens per embedding
OVERLAP_TOKENS = 100  # Overlap for context continuity
COLLECTION_NAME = "Information"
BATCH_SIZE = 50  # Optimal batch size for vector operations

print("Debug: Script started")
print("Debug: Imports completed")
logger.info("Debug: Script started in logger")

class URLTracker:
    """Tracks processed URLs to avoid redundant processing."""
    
    def __init__(self, storage_file: str = "processed_urls.json"):
        print("Debug: Initializing URLTracker")
        self.storage_file = storage_file
        self.processed_urls = {}
        print(f"Debug: Loading URLs from {self.storage_file}")
        self._load_processed_urls()
        print("Debug: URLTracker initialization complete")
    
    def _load_processed_urls(self):
        """Load processed URLs from JSON file."""
        try:
            if os.path.exists(self.storage_file):
                print(f"Debug: Found existing file {self.storage_file}")
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.processed_urls = json.load(f)
                logger.info(f"Loaded {len(self.processed_urls)} processed URLs from storage")
            else:
                print(f"Debug: No existing file {self.storage_file}, creating new")
                self.processed_urls = {}
                self._save_processed_urls_sync()
        except Exception as e:
            logger.error(f"Error loading processed URLs: {e}")
            print(f"Debug: Error loading URLs: {e}")
            self.processed_urls = {}
    
    def _save_processed_urls_sync(self):
        """Save processed URLs to JSON file synchronously."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_urls, f, indent=2, default=str)
            logger.info(f"Saved {len(self.processed_urls)} processed URLs to storage")
        except Exception as e:
            logger.error(f"Error saving processed URLs: {e}")
            print(f"Debug: Error saving URLs: {e}")
    
    async def mark_url_processed(self, url: str, status: str = "success", metadata: dict = None):
        """Mark URL as processed with status and metadata."""
        try:
            normalized_url = url.strip('/')
            self.processed_urls[normalized_url] = {
                "status": status,
                "last_processed": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            }
            self._save_processed_urls_sync()
        except Exception as e:
            logger.error(f"Error marking URL as processed: {e}")
            print(f"Debug: Error marking URL as processed: {e}")
    
    def is_url_processed(self, url: str) -> bool:
        """Check if URL has been processed."""
        try:
            normalized_url = url.strip('/')
            return normalized_url in self.processed_urls
        except Exception as e:
            logger.error(f"Error checking URL status: {e}")
            return False
    
    def get_url_status(self, url: str) -> dict:
        """Get processing status and metadata for a URL."""
        try:
            normalized_url = url.strip('/')
            return self.processed_urls.get(normalized_url, {})
        except Exception as e:
            logger.error(f"Error getting URL status: {e}")
            return {}
    
    async def mark_url_failed(self, url: str, error: str):
        """Mark URL as failed with error message."""
        await self.mark_url_processed(url, "failed", {"error": str(error)})
    
    def get_unprocessed_urls(self, urls: List[str]) -> List[str]:
        """Filter list to only unprocessed URLs."""
        try:
            return [url for url in urls if not self.is_url_processed(url.strip('/'))]
        except Exception as e:
            logger.error(f"Error getting unprocessed URLs: {e}")
            return []
    
    async def cleanup_old_entries(self, days: int = 30):
        """Remove entries older than specified days."""
        try:
            print("Debug: Starting cleanup of old entries")
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            self.processed_urls = {
                url: data for url, data in self.processed_urls.items()
                if datetime.fromisoformat(data['last_processed']) > cutoff
            }
            self._save_processed_urls_sync()
            print("Debug: Successfully cleaned up old entries")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            print(f"Debug: Error during cleanup: {e}")

# Initialize URL tracker as a global instance
url_tracker = URLTracker()

class DatabaseClients:
    _instance = None
    _lock = Lock()
    
    def __init__(self):
        self.openai = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        
        self.embeddings = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_EMBEDDINGS_DEPLOYMENT"),
            api_version=os.getenv("AZURE_EMBEDDING_API_VERSION")
        )
        
        self.qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=60
        )
        
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    @classmethod
    async def get_instance(cls) -> 'DatabaseClients':
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = DatabaseClients()
        return cls._instance

class TokenBucketRateLimiter:
    def __init__(self, tokens_per_minute: int, burst_size: int):
        self.tokens_per_minute = tokens_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.lock = Lock()
        
    async def acquire(self, tokens: int = 1):
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(
                self.burst_size,
                self.tokens + time_passed * (self.tokens_per_minute / 60.0)
            )
            
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) * 60.0 / self.tokens_per_minute
                await asyncio.sleep(wait_time)
                self.tokens = tokens
            
            self.tokens -= tokens
            self.last_update = now

# Initialize rate limiters
completions_limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_size=30)
embeddings_limiter = TokenBucketRateLimiter(tokens_per_minute=100, burst_size=50)

@dataclass
class PolaURL:
    url: str
    image_count: int
    last_modified: datetime
    
    @classmethod
    def from_string(cls, url: str, images: int, last_mod: str) -> 'PolaURL':
        try:
            last_modified = datetime.strptime(last_mod.strip(), "%Y-%m-%d %H:%M %z")
        except ValueError:
            last_modified = datetime.now(timezone.utc)
        return cls(url=url, image_count=images, last_modified=last_modified)

@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]
    semantic_context: str = ""
    links: List[str] = field(default_factory=list)
    chunk_hash: str = field(init=False)
    
    def __post_init__(self):
        self.chunk_hash = hashlib.md5(self.content.encode()).hexdigest()
        if len(self.embedding) != VECTOR_SIZE:
            raise ValueError(f"Embedding dimension mismatch: {len(self.embedding)} != {VECTOR_SIZE}")

def extract_links(text: str) -> List[str]:
    """Extract all URLs from text content."""
    import re
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return list(set(re.findall(url_pattern, text)))

def calculate_optimal_chunk_size(text: str) -> int:
    """Calculate optimal chunk size based on token and vector dimensions."""
    avg_tokens_per_char = len(text.split()) / len(text)
    optimal_chars = int(OPTIMAL_TOKENS_PER_VECTOR / avg_tokens_per_char)
    return optimal_chars

def chunk_text(text: str, chunk_size: Optional[int] = None) -> List[str]:
    """Split text into chunks with optimal size for embeddings."""
    if chunk_size is None:
        chunk_size = calculate_optimal_chunk_size(text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    lines = text.split('\n')
    
    for line in lines:
        line_tokens = len(line.split())
        
        if current_size + line_tokens > MAX_TOKENS_PER_CHUNK and current_chunk:
            overlap = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
            chunks.append('\n'.join(current_chunk))
            current_chunk = overlap.copy()
            current_size = sum(len(l.split()) for l in current_chunk)
        
        if line.startswith('#') or line.startswith('```'):
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        current_chunk.append(line)
        current_size += line_tokens
        
        if current_size >= OPTIMAL_TOKENS_PER_VECTOR and not line.startswith('```'):
            chunks.append('\n'.join(current_chunk))
            current_chunk = current_chunk[-2:]
            current_size = sum(len(l.split()) for l in current_chunk)
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_title_and_summary(chunk: str, url: str, db: DatabaseClients) -> Dict[str, str]:
    """Extract title and summary using GPT-4o with rate limiting."""
    await completions_limiter.acquire()
    
    system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
    Return a JSON object with 'title' and 'summary' keys. Use just text after Slapukų naudojimo tikslai svetainėje ends. Content start at [{title}] 
    
    Title requirements:
    1. Must be clear, descriptive, and specific to the content
    2. Must be in Lithuanian language
    3. Must NOT be generic (e.g., avoid 'Slapukų politika', 'Privatumo politika', etc.)
    4. Should capture the main topic or purpose of the content
    5. Should be 3-7 words long
    6. Must NOT be empty
    7. DO NOT INCLUDE Slapukų naudojimo tikslai svetainėje ir the title or summary
    8. DO NOT INCLUDE 

    
    Summary requirements:
    1. Must be 2-3 sentences long
    2. Must be in Lithuanian language
    3. Must capture the key points of the content
    4. Must be informative and specific
    5. Must NOT be generic
    6. Must NOT be empty
    
    Example output format:
    {
        "title": "Specific descriptive title in Lithuanian",
        "summary": "Detailed 2-3 sentence summary in Lithuanian"
    }"""

    try:
        links = extract_links(chunk)
        
        response = await db.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"URL: {url}\n\nContent:\n{chunk[:2000]}...\n\nLinks found: {links}"}
            ],
            response_format={ "type": "json_object" },
            max_tokens=500,
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # If GPT detected a policy page and returned empty strings, skip processing
        if (not result.get('title') and not result.get('summary')) or \
           (result.get('title') == '' and result.get('summary') == ''):
            logger.info(f"GPT detected policy/cookie content for {url}, skipping")
            return None
            
        # Validate response
        if not result.get('title') or not result.get('summary'):
            # Fallback values if GPT doesn't provide proper response
            page_type = "pola_docs" if "pola.lt" in url else "priesvezi_docs"
            result['title'] = result.get('title') or f"Dokumentas iš {url.split('/')[-2].replace('-', ' ').title()}"
            result['summary'] = result.get('summary') or f"Informacija iš {url}"
            
        if links:
            result['links'] = links
            
        logger.info(f"Processed title and summary for chunk from {url}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting title and summary for {url}: {e}")
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_embedding(text: str, db: DatabaseClients) -> List[float]:
    """Get embedding with size verification and rate limiting."""
    await embeddings_limiter.acquire()
    
    try:
        token_estimate = len(text.split())
        if token_estimate > MAX_TOKENS_PER_CHUNK:
            logger.warning(f"Text may exceed token limit: {token_estimate} tokens")
            text = ' '.join(text.split()[:MAX_TOKENS_PER_CHUNK])
        
        response = await db.embeddings.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        
        embedding = response.data[0].embedding
        
        if len(embedding) != VECTOR_SIZE:
            raise ValueError(f"Embedding size mismatch: got {len(embedding)}, expected {VECTOR_SIZE}")
        
        return embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_semantic_context(chunk: str, title: str, summary: str, url: str, db: DatabaseClients) -> str:
    """Generate semantic context for a chunk using GPT-4o."""
    await completions_limiter.acquire()
    
    system_prompt = """You are an AI that generates semantic context for document chunks.
    The semantic context should:
    1. Describe the broader context this chunk fits into
    2. Identify key themes and concepts
    3. Note any important relationships or dependencies
    4. Be concise (2-3 sentences)
    5. Be in Lithuanian language
    6. Focus on the main topic and its relationship to POLA organization
    7. Include relevant medical or healthcare context if present
    8. Highlight connections to cancer patient support if relevant

    Return only the semantic context in Lithuanian, no additional formatting or explanation.
    Example format: "Šis tekstas yra dalis POLA dokumentacijos, aprašančios [tema]. Jame aptariama [pagrindinė mintis]. Tekstas susietas su [kontekstas/ryšiai]."
    """

    try:
        # Generate cache key for deduplication
        cache_key = hashlib.md5(f"{url}:{chunk[:100]}".encode()).hexdigest()
        
        # Log the attempt
        logger.info(f"Generating semantic context for chunk from {url} (cache_key: {cache_key[:8]})")
        
        # Validate inputs
        if not chunk or not title or not summary:
            logger.warning(f"Missing required input for semantic context generation: chunk={bool(chunk)}, title={bool(title)}, summary={bool(summary)}")
            return ""
            
        response = await db.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Title: {title}\nSummary: {summary}\nURL: {url}\n\nContent:\n{chunk[:2000]}"}
            ],
            max_tokens=200,
            temperature=0.1,
            presence_penalty=0.6,  # Encourage more diverse responses
            frequency_penalty=0.3   # Reduce repetition
        )
        
        semantic_context = response.choices[0].message.content.strip()
        
        # Validate response
        if not semantic_context:
            logger.warning(f"Empty semantic context generated for {url}")
            return ""
            
        # Ensure response is in Lithuanian
        if not any(c.isalpha() for c in semantic_context):
            logger.warning(f"Invalid semantic context (no letters) for {url}")
            return ""
            
        logger.info(f"Successfully generated semantic context for chunk from {url} (cache_key: {cache_key[:8]})")
        return semantic_context
        
    except Exception as e:
        logger.error(f"Error getting semantic context for {url}: {str(e)}", exc_info=True)
        # Re-raise the exception to trigger retry
        raise

async def process_chunk(chunk: str, chunk_number: int, url: str, db: DatabaseClients) -> ProcessedChunk:
    """Process chunk with dimension verification."""
    try:
        token_count = len(chunk.split())
        if token_count > MAX_TOKENS_PER_CHUNK:
            logger.warning(f"Chunk {chunk_number} exceeds token limit, truncating...")
            chunk = ' '.join(chunk.split()[:MAX_TOKENS_PER_CHUNK])
        
        title_summary = await get_title_and_summary(chunk, url, db)
        if not title_summary:
            logger.warning(f"Failed to get title and summary for chunk {chunk_number} from {url}")
            return None
            
        embedding = await get_embedding(chunk, db)
        links = extract_links(chunk)
        
        # Generate semantic context with retries
        max_retries = 3
        semantic_context = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                semantic_context = await get_semantic_context(
                    chunk=chunk,
                    title=title_summary['title'],
                    summary=title_summary['summary'],
                    url=url,
                    db=db
                )
                if semantic_context:
                    break
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed to generate semantic context: {str(e)}")
                await asyncio.sleep(2)  # Wait before retry
        
        if not semantic_context:
            logger.error(f"Failed to generate semantic context after {max_retries} attempts: {str(last_error)}")
            semantic_context = ""  # Fallback to empty string
        
        return ProcessedChunk(
            url=url,
            chunk_number=chunk_number,
            title=title_summary['title'],
            summary=title_summary['summary'],
            content=chunk,
            metadata={
                'token_count': token_count,
                'vector_size': len(embedding),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'source_type': 'priesvezi_docs' if 'priesvezi.lt' in url else 'pola_docs',
                'language': 'lt',
                'links': links
            },
            embedding=embedding,
            semantic_context=semantic_context,
            links=links
        )
    except Exception as e:
        logger.error(f"Error processing chunk {chunk_number} from {url}: {str(e)}", exc_info=True)
        return None

async def process_and_store_document(url: PolaURL, markdown: str, db: DatabaseClients):
    """Process and store document with optimized batch operations."""
    try:
        normalized_url = url.url.strip('/')
        
        # Check if URL was already processed
        if url_tracker.is_url_processed(normalized_url):
            status = url_tracker.get_url_status(normalized_url)
            logger.info(f"Skipping already processed URL {normalized_url} with status: {status['status']}")
            return
        
        # Find the title marker and process only content after it
        title_marker = "[{title}]"
        content_start = markdown.find(title_marker)
        
        if content_start == -1:
            logger.info(f"No title marker found in {normalized_url}, skipping document")
            return
            
        # Extract only content after the title marker
        processed_markdown = markdown[content_start + len(title_marker):].strip()
        
        if not processed_markdown:
            logger.info(f"No content after title marker in {normalized_url}, skipping document")
            return

        content_hash = hashlib.md5(processed_markdown.encode()).hexdigest()
        
        # Check if document exists in Supabase with proper response handling
        existing_doc_response = db.supabase.table('documents').select('*').eq('content_hash', content_hash).execute()
        if existing_doc_response.data and len(existing_doc_response.data) > 0:
            logger.info(f"Document {normalized_url} already exists with hash {content_hash[:8]}, skipping")
            return
        
        # Process chunks in optimal batches
        chunks = chunk_text(processed_markdown)
        processed_chunks = []
        
        # Process each chunk only once
        processed_urls = set()
        
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_tasks = [
                process_chunk(chunk, idx + i, normalized_url, db)
                for idx, chunk in enumerate(batch)
                if normalized_url not in processed_urls
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            processed_chunks.extend([r for r in batch_results if r is not None])
            processed_urls.add(normalized_url)
        
        if not processed_chunks:
            logger.warning(f"No chunks processed for {normalized_url}")
            return
        
        # Find first meaningful chunk (not containing privacy policy)
        first_meaningful_chunk = None
        for chunk in processed_chunks:
            if chunk and chunk.title and chunk.summary:
                first_meaningful_chunk = chunk
                main_title_summary = {"title": chunk.title, "summary": chunk.summary}
                break
                
        if first_meaningful_chunk is None:
            logger.info(f"No meaningful content found in {normalized_url}, skipping")
            return
            
        # Create document in Supabase
        doc_id = str(uuid.uuid4())
        document_data = {
            'id': doc_id,
            'url': normalized_url,
            'title': main_title_summary['title'],
            'summary': main_title_summary['summary'],
            'content_hash': content_hash,
            'language': 'lt',
            'source_type': 'priesvezi_docs' if 'priesvezi.lt' in normalized_url else 'pola_docs',
            'metadata': {
                'image_count': url.image_count,
                'last_modified': url.last_modified.isoformat(),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'chunk_count': len(processed_chunks),
                'original_content_length': len(markdown),
                'processed_content_length': len(processed_markdown)
            }
        }
        
        # Store document in Supabase
        doc_insert_response = db.supabase.table('documents').insert(document_data).execute()
        if not doc_insert_response.data:
            raise Exception(f"Failed to insert document {doc_id} into Supabase")
        
        # Prepare Qdrant points and chunk records
        qdrant_points = []
        chunk_records = []
        
        for chunk in processed_chunks:
            if not chunk:  # Skip None chunks
                continue
                
            qdrant_point_id = str(uuid.uuid4())
            
            # Ensure chunk title and summary are not null
            chunk_title = chunk.title if chunk.title else main_title_summary['title']
            chunk_summary = chunk.summary if chunk.summary else "Dokumento dalis"
            
            qdrant_points.append(
                models.PointStruct(
                    id=qdrant_point_id,
                    vector=chunk.embedding,
                    payload={
                        'document_id': doc_id,
                        'chunk_number': chunk.chunk_number,
                        'title': chunk_title,
                        'summary': chunk_summary,
                        'url': normalized_url,
                        'content': chunk.content,
                        'metadata': chunk.metadata,
                        'semantic_context': chunk.semantic_context  # Add semantic context to Qdrant
                    }
                )
            )
            
            chunk_records.append({
                'id': str(uuid.uuid4()),
                'document_id': doc_id,
                'qdrant_point_id': qdrant_point_id,
                'chunk_number': chunk.chunk_number,
                'chunk_content': chunk.content,
                'chunk_hash': chunk.chunk_hash,
                'title': chunk_title,
                'summary': chunk_summary,
                'semantic_context': chunk.semantic_context,  # Add semantic context to chunk records
                'metadata': {
                    'title': chunk_title,
                    'summary': chunk_summary,
                    'semantic_context': chunk.semantic_context,
                    'links': chunk.links
                }
            })
        
        # Batch insert into Qdrant
        db.qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=qdrant_points,
            wait=True
        )
        
        # Batch insert chunks into Supabase
        chunks_insert_response = db.supabase.table('document_chunks').insert(chunk_records).execute()
        if not chunks_insert_response.data:
            raise Exception(f"Failed to insert chunks for document {doc_id} into Supabase")
        
        logger.info(f"Successfully processed {normalized_url}: {len(processed_chunks)} chunks")
        
        # Mark URL as processed on success
        await url_tracker.mark_url_processed(
            normalized_url, 
            "success",
            {
                "content_hash": content_hash,
                "chunks_processed": len(processed_chunks),
                "document_id": doc_id
            }
        )
        
    except Exception as e:
        # Mark URL as failed on error
        await url_tracker.mark_url_failed(normalized_url, str(e))
        logger.error(f"Error processing {normalized_url}: {str(e)}", exc_info=True)
        raise

async def crawl_parallel(urls: List[PolaURL], max_concurrent: int = 5):
    """Crawl multiple URLs in parallel with a concurrency limit."""
    # Filter out already processed URLs
    unprocessed_urls = [url for url in urls if not url_tracker.is_url_processed(url.url.strip('/'))]
    if not unprocessed_urls:
        logger.info("No new URLs to process")
        return
        
    logger.info(f"Processing {len(unprocessed_urls)} new URLs out of {len(urls)} total URLs")
    
    browser_config = BrowserConfig(
        headless=True,
        verbose=True,
        extra_args=[
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )
    
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS # Increased timeout to 60 seconds
    )

    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    db = await DatabaseClients.get_instance()

    try:
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_url(pola_url: PolaURL):
            async with semaphore:
                try:
                    # Add retry logic for each URL
                    for attempt in range(3):  # Try 3 times
                        try:
                            result = await crawler.arun(
                                url=pola_url.url,
                                config=crawl_config,
                                session_id=f"session_{attempt}"  # New session for each attempt
                            )
                            if result.success:
                                logger.info(f"Successfully crawled: {pola_url.url}")
                                # Filter out cookie/privacy policy content before processing
                                content = result.markdown_v2.raw_markdown
                                
                                await process_and_store_document(pola_url, content, db)
                                  # Success, exit retry loop
                            else:
                                logger.warning(f"Attempt {attempt + 1} failed for {pola_url.url}: {result.error_message}")
                                await asyncio.sleep(2)  # Wait before retry
                        except Exception as e:
                            logger.warning(f"Attempt {attempt + 1} error for {pola_url.url}: {str(e)}")
                            if attempt == 2:  # Last attempt
                                raise  # Re-raise on final attempt
                            await asyncio.sleep(2)  # Wait before retry
                except Exception as e:
                    logger.error(f"Error processing {pola_url.url}: {str(e)}")
        
        # Process URLs in smaller batches with longer delays
        batch_size = 3  # Reduced batch size for better stability
        for i in range(0, len(unprocessed_urls), batch_size):
            batch = unprocessed_urls[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} of {(len(unprocessed_urls) + batch_size - 1)//batch_size}")
            await asyncio.gather(*[process_url(url) for url in batch])
            await asyncio.sleep(2)  # Delay between batches
            
    finally:
        logger.info("Closing browser...")
        await crawler.close()
        logger.info("Browser closed.")

class SitemapProcessor:
    """Handles sitemap URL processing and state tracking."""
    
    def __init__(self, sitemap_urls: List[str], storage_file: str = "sitemap_state.json"):
        print("Debug: Initializing SitemapProcessor")
        self.sitemap_urls = sitemap_urls
        self.storage_file = storage_file
        self.lock = Lock()  # Add lock for thread safety
        print(f"Debug: Loading state from {self.storage_file}")
        self.state = self._load_state()
        print(f"Debug: SitemapProcessor initialized with {len(sitemap_urls)} sitemaps")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load sitemap processing state from JSON file."""
        try:
            if os.path.exists(self.storage_file):
                print(f"Debug: Found existing sitemap state file {self.storage_file}")
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                print(f"Debug: Loaded state with {len(state.get('sitemaps', {}))} sitemaps")
                return state
            else:
                print(f"Debug: No existing sitemap state file, creating new at {self.storage_file}")
                state = self._create_default_state()
                # Ensure the file is created immediately
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2, default=str)
                print("Debug: Created new sitemap state file")
                return state
        except Exception as e:
            print(f"Debug: Error loading sitemap state: {e}")
            state = self._create_default_state()
            try:
                # Try to create the file even after error
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2, default=str)
                print("Debug: Created new sitemap state file after error")
            except Exception as write_error:
                print(f"Debug: Failed to create sitemap state file: {write_error}")
            return state
    
    def _create_default_state(self) -> Dict[str, Any]:
        """Create default state structure."""
        print("Debug: Creating default state structure")
        return {
            "sitemaps": {},
            "last_run": None,
            "stats": {
                "total_urls_found": 0,
                "successful_crawls": 0,
                "failed_crawls": 0
            }
        }
    
    def _save_state(self, state: Dict[str, Any] = None):
        """Save current state to JSON file."""
        try:
            state = state or self.state
            print(f"Debug: Saving state to {self.storage_file}")
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, default=str)
            print(f"Debug: Successfully saved state with {len(state.get('sitemaps', {}))} sitemaps")
        except Exception as e:
            print(f"Debug: Error saving sitemap state: {e}")
            # Try to create directory if it doesn't exist
            try:
                os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2, default=str)
                print("Debug: Successfully saved state after creating directory")
            except Exception as write_error:
                print(f"Debug: Failed to save state even after creating directory: {write_error}")
    
    def update_sitemap_state(self, sitemap_url: str, urls_found: int, success: bool = True):
        """Update processing state for a sitemap."""
        print(f"Debug: Updating state for {sitemap_url} with {urls_found} URLs")
        self.state["sitemaps"][sitemap_url] = {
            "last_processed": datetime.now(timezone.utc).isoformat(),
            "urls_found": urls_found,
            "status": "success" if success else "failed"
        }
        self.state["last_run"] = datetime.now(timezone.utc).isoformat()
        self.state["stats"]["total_urls_found"] += urls_found
        if success:
            self.state["stats"]["successful_crawls"] += 1
        else:
            self.state["stats"]["failed_crawls"] += 1
        self._save_state()
        print(f"Debug: Successfully updated state for {sitemap_url}")
    
    def get_sitemap_state(self, sitemap_url: str) -> Dict[str, Any]:
        """Get processing state for a specific sitemap."""
        state = self.state["sitemaps"].get(sitemap_url, {})
        print(f"Debug: Retrieved state for {sitemap_url}: {state}")
        return state
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get overall processing statistics."""
        stats = self.state["stats"]
        print(f"Debug: Retrieved processing stats: {stats}")
        return stats

# Modify the main() function to use SitemapProcessor
async def main():
    """Main execution with enhanced monitoring and error handling."""
    print("Debug: Starting the crawler...")
    logger.info("Initializing crawler process")
    
    try:
        print("Debug: Initializing URL tracker cleanup")
        await url_tracker.cleanup_old_entries()
        print("Debug: URL tracker cleanup complete")
        
        print("Debug: Getting database instance")
        db = await DatabaseClients.get_instance()
        print("Debug: Database instance obtained")
        
        start_time = time.time()
        logger.info("Starting crawler process")
        print("Debug: Connecting to database...")
        
        try:
            print("Debug: Getting Qdrant collection info")
            collection_info = db.qdrant.get_collection(COLLECTION_NAME)
            initial_points = collection_info.points_count
            print(f"Debug: Initial points in collection: {initial_points}")
        except Exception as e:
            print(f"Debug: Error getting collection info: {e}")
            logger.error(f"Error getting collection info: {e}")
            initial_points = 0
        
        # Define sitemap URLs and initialize processor
        sitemap_urls = [
            "https://pola.lt/product-sitemap.xml",
            "https://pola.lt/page-sitemap.xml"
        ]
        
        print("Debug: Creating SitemapProcessor instance...")
        sitemap_processor = SitemapProcessor(sitemap_urls)
        print("Debug: SitemapProcessor instance created successfully")
        print("Debug: Starting to fetch sitemaps...")
        urls = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            for sitemap_url in sitemap_urls:
                try:
                    print(f"Debug: Starting to process sitemap: {sitemap_url}")
                    logger.info(f"Processing sitemap: {sitemap_url}")
                    
                    # Check previous state
                    previous_state = sitemap_processor.get_sitemap_state(sitemap_url)
                    print(f"Debug: Previous state for {sitemap_url}: {json.dumps(previous_state, indent=2)}")
                    
                    print(f"Debug: Sending GET request to {sitemap_url}")
                    async with session.get(sitemap_url, ssl=False) as response:
                        print(f"Debug: Received response from {sitemap_url}, status: {response.status}")
                        if response.status != 200:
                            error_msg = f"Error fetching sitemap {sitemap_url}, status: {response.status}"
                            print(f"Debug: {error_msg}")
                            logger.error(error_msg)
                            sitemap_processor.update_sitemap_state(sitemap_url, 0, False)
                            continue
                        
                        print(f"Debug: Reading response content from {sitemap_url}")
                        xml_content = await response.text()
                        print(f"Debug: Content length: {len(xml_content)} bytes")
                        
                        if not xml_content:
                            error_msg = f"Empty response from {sitemap_url}"
                            print(f"Debug: {error_msg}")
                            logger.error(error_msg)
                            sitemap_processor.update_sitemap_state(sitemap_url, 0, False)
                            continue
                        
                        try:
                            print(f"Debug: Parsing XML content from {sitemap_url}")
                            root = ET.fromstring(xml_content)
                            namespace = root.tag.split('}')[0] + '}' if '}' in root.tag else ''
                            print(f"Debug: XML namespace: {namespace}")
                            sitemap_urls_count = 0
                            
                            print(f"Debug: Starting URL extraction from {sitemap_url}")
                            for url_elem in root.findall(f".//{namespace}url"):
                                loc = url_elem.find(f"{namespace}loc").text
                                print(f"Debug: Found URL: {loc}")
                                last_mod_elem = url_elem.find(f"{namespace}lastmod")
                                last_mod = datetime.now(timezone.utc)
                                
                                if last_mod_elem is not None and last_mod_elem.text:
                                    try:
                                        last_mod = datetime.fromisoformat(last_mod_elem.text.replace('Z', '+00:00'))
                                        print(f"Debug: Last modified date for {loc}: {last_mod}")
                                    except ValueError as e:
                                        print(f"Debug: Invalid lastmod format for {loc}: {e}")
                                        last_mod = datetime.now(timezone.utc)
                                
                                urls.append(PolaURL(
                                    url=loc,
                                    image_count=0,
                                    last_modified=last_mod
                                ))
                                sitemap_urls_count += 1
                                
                                if sitemap_urls_count % 10 == 0:
                                    print(f"Debug: Processed {sitemap_urls_count} URLs from {sitemap_url}")
                            
                            print(f"Debug: Completed processing {sitemap_url}, found {sitemap_urls_count} URLs")
                            sitemap_processor.update_sitemap_state(sitemap_url, sitemap_urls_count, True)
                            logger.info(f"Successfully parsed sitemap {sitemap_url}: {sitemap_urls_count} URLs found")
                            
                        except ET.ParseError as e:
                            error_msg = f"XML parsing error for {sitemap_url}: {e}"
                            print(f"Debug: {error_msg}")
                            logger.error(error_msg)
                            sitemap_processor.update_sitemap_state(sitemap_url, 0, False)
                            continue
                            
                except Exception as e:
                    error_msg = f"Failed to process sitemap {sitemap_url}: {str(e)}"
                    print(f"Debug: {error_msg}")
                    logger.error(error_msg)
                    sitemap_processor.update_sitemap_state(sitemap_url, 0, False)
                    continue
        
        if not urls:
            print("Debug: No URLs found in sitemaps")
            logger.info("No URLs found in sitemaps")
            return
        
        # Get processing stats
        stats = sitemap_processor.get_processing_stats()
        print(f"Debug: Sitemap processing stats: {json.dumps(stats, indent=2)}")
        
        total_urls = len(urls)
        print(f"Debug: Total URLs found in all sitemaps: {total_urls}")
        logger.info(f"Total URLs found in all sitemaps: {total_urls}")
        
        print("Debug: Starting parallel crawling...")
        await crawl_parallel(urls)
        
        try:
            print("Debug: Getting final collection info")
            collection_info = db.qdrant.get_collection(COLLECTION_NAME)
            final_points = collection_info.points_count
        except Exception as e:
            print(f"Debug: Error getting final collection info: {e}")
            final_points = 0
        
        execution_time = time.time() - start_time
        summary = f"""
        Crawl Summary:
        - Total URLs processed: {total_urls}
        - Initial points: {initial_points}
        - Final points: {final_points}
        - New points added: {final_points - initial_points}
        - Total execution time: {execution_time:.2f}s
        """
        print(f"Debug: {summary}")
        logger.info(summary)
        
    except Exception as e:
        error_msg = f"Critical error in main execution: {str(e)}"
        print(f"Debug: Error: {error_msg}")
        logger.error(error_msg)
        raise
    finally:
        print("Debug: Crawler execution completed")

if __name__ == "__main__":
    print("Debug: About to start main()")
    try:
        asyncio.run(main())
        print("Debug: main() completed")
    except Exception as e:
        print(f"Debug: Error in main(): {str(e)}")
        logger.error(f"Debug: Error in main(): {str(e)}")
        raise