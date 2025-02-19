import os
import sys
import json
import asyncio
from qdrant_client import QdrantClient, models
import requests
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    """Extract title and summary using GPT-4 with rate limiting."""
    await completions_limiter.acquire()
    
    system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
    Return a JSON object with 'title' and 'summary' keys.
    For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
    For the summary: Create a concise summary of the main points in this chunk.
    Keep both title and summary concise but informative.
    Include any relevant links found in the content in the summary."""

    try:
        links = extract_links(chunk)
        
        response = await db.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"URL: {url}\n\nContent:\n{chunk[:2000]}...\n\nLinks found: {links}"}
            ],
            response_format={ "type": "json_object" },
            max_tokens=500,
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
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

async def process_chunk(chunk: str, chunk_number: int, url: str, db: DatabaseClients) -> ProcessedChunk:
    """Process chunk with dimension verification."""
    token_count = len(chunk.split())
    if token_count > MAX_TOKENS_PER_CHUNK:
        logger.warning(f"Chunk {chunk_number} exceeds token limit, truncating...")
        chunk = ' '.join(chunk.split()[:MAX_TOKENS_PER_CHUNK])
    
    title_summary = await get_title_and_summary(chunk, url, db)
    embedding = await get_embedding(chunk, db)
    links = extract_links(chunk)
    
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
        links=links
    )

async def process_and_store_document(url: PolaURL, markdown: str, db: DatabaseClients):
    """Process and store document with optimized batch operations."""
    try:
        normalized_url = url.url.strip('/')
        content_hash = hashlib.md5(markdown.encode()).hexdigest()
        
        # Check if document exists in Supabase
        existing_doc = await db.supabase.table('documents').select('*').eq('content_hash', content_hash).execute()
        
        if existing_doc.data:
            logger.info(f"Document {normalized_url} already exists with hash {content_hash[:8]}, skipping")
            return
        
        # Process chunks in optimal batches
        chunks = chunk_text(markdown)
        processed_chunks = []
        
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_tasks = [
                process_chunk(chunk, idx + i, normalized_url, db)
                for idx, chunk in enumerate(batch)
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            processed_chunks.extend(batch_results)
        
        # Create document in Supabase
        doc_id = str(uuid.uuid4())
        document_data = {
            'id': doc_id,
            'url': normalized_url,
            'title': processed_chunks[0].title if processed_chunks else 'Untitled',
            'content_hash': content_hash,
            'language': 'lt',
            'source_type': 'priesvezi_docs' if 'priesvezi.lt' in normalized_url else 'pola_docs',
            'metadata': {
                'image_count': url.image_count,
                'last_modified': url.last_modified.isoformat(),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'chunk_count': len(processed_chunks)
            }
        }
        
        # Store document and chunks in Supabase
        await db.supabase.table('documents').insert(document_data).execute()
        
        # Prepare Qdrant points and chunk records
        qdrant_points = []
        chunk_records = []
        
        for chunk in processed_chunks:
            qdrant_point_id = str(uuid.uuid4())
            
            qdrant_points.append(
                models.PointStruct(
                    id=qdrant_point_id,
                    vector=chunk.embedding,
                    payload={
                        'document_id': doc_id,
                        'chunk_number': chunk.chunk_number,
                        'title': chunk.title,
                        'summary': chunk.summary,
                        'url': normalized_url,
                        'content': chunk.content,
                        'metadata': chunk.metadata
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
                'metadata': {
                    'title': chunk.title,
                    'summary': chunk.summary,
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
        await db.supabase.table('document_chunks').insert(chunk_records).execute()
        
        logger.info(f"Successfully processed {normalized_url}: {len(processed_chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Error processing {normalized_url}: {e}")
        raise

async def crawl_parallel(urls: List[PolaURL], max_concurrent: int = 5):
    """Crawl multiple URLs in parallel with optimized concurrency."""
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
        cache_mode=CacheMode.BYPASS
    )

    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    db = await DatabaseClients.get_instance()

    try:
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_url(pola_url: PolaURL):
            async with semaphore:
                try:
                    result = await crawler.arun(
                        url=pola_url.url,
                        config=crawl_config,
                        session_id="session1"
                    )
                    if result.success:
                        logger.info(f"Successfully crawled: {pola_url.url}")
                        await process_and_store_document(pola_url, result.markdown_v2.raw_markdown, db)
                    else:
                        logger.error(f"Failed to crawl: {pola_url.url} - Error: {result.error_message}")
                except Exception as e:
                    logger.error(f"Error processing {pola_url.url}: {str(e)}")
        
        # Process URLs in batches
        batch_size = 5
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} of {(len(urls) + batch_size - 1)//batch_size}")
            await asyncio.gather(*[process_url(url) for url in batch])
            await asyncio.sleep(1)
            
    finally:
        logger.info("Closing browser...")
        await crawler.close()
        logger.info("Browser closed.")

async def main():
    """Main execution with enhanced monitoring and error handling."""
    db = await DatabaseClients.get_instance()
    
    try:
        start_time = time.time()
        logger.info("Starting crawler process")
        
        # Get initial stats
        collection_info = db.qdrant.get_collection(COLLECTION_NAME)
        initial_points = collection_info.points_count
        
        # Get URLs and process
        urls = get_pola_urls()
        if not urls:
            logger.info("No URLs found to crawl")
            return
        
        logger.info(f"Found {len(urls)} URLs to crawl")
        await crawl_parallel(urls)
        
        # Get final stats
        collection_info = db.qdrant.get_collection(COLLECTION_NAME)
        final_points = collection_info.points_count
        
        execution_time = time.time() - start_time
        logger.info(f"""
        Crawl Summary:
        - Total URLs processed: {len(urls)}
        - Initial points: {initial_points}
        - Final points: {final_points}
        - New points added: {final_points - initial_points}
        - Total execution time: {execution_time:.2f}s
        """)
        
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())