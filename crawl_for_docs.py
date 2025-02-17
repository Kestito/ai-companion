import os
import sys
import json
import asyncio
from qdrant_client import QdrantClient
import requests
import uuid
import hashlib
from xml.etree import ElementTree
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse
from dotenv import load_dotenv
from asyncio import Semaphore
import time

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from openai import AsyncAzureOpenAI
from langchain.schema import Document
from ai_companion.modules.rag.core.vector_store import VectorStoreManager

from sentence_transformers import SentenceTransformer
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PORT = "6333"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


load_dotenv()

# Initialize OpenAI client
openai_client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

embeddings_client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_EMBEDDINGS_DEPLOYMENT"),
    api_version=os.getenv("AZURE_EMBEDDING_API_VERSION")
)

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    port=QDRANT_PORT,
    api_key=QDRANT_API_KEY,
)

# Constants for rate limiting
COMPLETIONS_RPM = 60  # Rate limit for GPT-4 completions (requests per minute)
EMBEDDINGS_RPM = 100  # Rate limit for embeddings (requests per minute)

# Create semaphores for rate limiting
completions_semaphore = Semaphore(10)  # Allow 10 concurrent completion requests
embeddings_semaphore = Semaphore(20)   # Allow 20 concurrent embedding requests

# Add delay tracking
last_completion_time = 0
last_embedding_time = 0

COLLECTION_NAME = "Pola_docs"
VECTOR_SIZE = 1536  # Size of OpenAI embeddings

# Initialize VectorStoreManager
vector_store = VectorStoreManager(
    collection_name=os.getenv("COLLECTION_NAME", "Pola_docs"),
    embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
    embedding_model=os.getenv("EMBEDDING_MODEL")
)

@dataclass
class PolaURL:
    url: str
    image_count: int
    last_modified: datetime
    
    @classmethod
    def from_string(cls, url: str, images: int, last_mod: str) -> 'PolaURL':
        """Create PolaURL from raw string data"""
        try:
            last_modified = datetime.strptime(last_mod.strip(), "%Y-%m-%d %H:%M %z")
        except ValueError:
            last_modified = datetime.now(timezone.utc)
        return cls(url=url, image_count=images, last_modified=last_modified)

def get_pola_urls() -> List[PolaURL]:
    """Get manually defined list of POLA URLs."""
    existing_urls = set()
    
    try:
        # Proper Qdrant record check using scroll API
        records, _ = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,  # Adjust based on expected URL count
            with_payload=True,
            with_vectors=False
        )
        existing_urls = {record.payload['url'] for record in records}
    except Exception as e:
        print(f"Warning: Could not fetch existing URLs from Qdrant: {e}")
    
    urls_data = [
        ("https://pola.lt/", 0, "2025-01-30 21:09 +00:00"),
        ("https://pola.lt/apie-pola/", 0, "2019-04-08 21:17 +00:00"),
        ("https://pola.lt/pola-kortele/", 0, "2019-04-08 21:30 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2013-m-ataskaita/", 0, "2019-04-08 21:35 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2012-m-ataskaita/", 0, "2019-04-08 21:35 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2014-m-ataskaita/", 0, "2019-04-08 21:36 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2016-m-ataskaita/", 0, "2019-04-08 21:36 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2015-m-ataskaita/", 0, "2019-04-08 21:36 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/", 0, "2019-04-08 21:37 +00:00"),
        ("https://pola.lt/o-rake/kak-poyavlyaetsya-rak/", 0, "2019-04-08 21:42 +00:00"),
        ("https://pola.lt/o-rake/kak-rasprostranyaetsya-rak/", 0, "2019-04-08 21:42 +00:00"),
        ("https://pola.lt/o-rake/chto-proishodit-v-organizme-vo-vremya-rakovyh-zabolevanij/", 0, "2019-04-08 21:42 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2017-m-ataskaita/", 0, "2019-10-08 16:31 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2018-m-ataskaita/", 0, "2020-02-11 12:08 +00:00"),
        ("https://pola.lt/apie-pola/veiklos-ataskaitos/", 0, "2020-02-26 16:24 +00:00"),
        ("https://pola.lt/parduotuve/", 0, "2020-02-26 20:02 +00:00"),
        ("https://pola.lt/mano-paskyra/", 0, "2020-02-26 20:03 +00:00"),
        ("https://pola.lt/apmokejimas/", 0, "2020-11-12 09:01 +00:00"),
        ("https://pola.lt/prekiu-pristatymas-ir-grazinimas/", 0, "2021-01-06 05:46 +00:00"),
        ("https://pola.lt/savanoryste/", 0, "2021-01-25 08:49 +00:00"),
        ("https://pola.lt/privatumo-politika/", 0, "2021-06-21 08:56 +00:00"),
        ("https://pola.lt/pola-kortele/pola-korteles-suteikiamos-nemokamos-konsultacijos/", 0, "2022-02-08 13:36 +00:00"),
        ("https://pola.lt/krepselis/", 0, "2022-11-22 08:04 +00:00"),
        ("https://pola.lt/apie-pola/konsultuojantys-specialistai/", 0, "2023-01-22 07:36 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2022-m-ataskaita/", 0, "2023-05-22 16:21 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2019-m-ataskaita/", 0, "2023-05-22 16:24 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2020-m-ataskaita/", 0, "2023-05-22 16:44 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2021-m-ataskaita/", 0, "2023-05-22 16:59 +00:00"),
        ("https://pola.lt/parama/", 0, "2024-02-21 07:18 +00:00"),
        ("https://pola.lt/konsultacijos/", 0, "2024-03-12 18:14 +00:00"),
        ("https://pola.lt/apie-pola/komanda/", 0, "2024-10-01 05:40 +00:00"),
        ("https://pola.lt/kontaktai/", 0, "2024-10-01 05:42 +00:00"),
        ("https://pola.lt/veiklos-ataskaitos/2023-m-ataskaita/", 0, "2024-10-11 06:27 +00:00"),
        ("https://pola.lt/apie-pola/aktyviausi-pola-savanoriai/", 0, "2024-10-14 09:35 +00:00"),
        ("https://pola.lt/apie-pola/naryste/", 0, "2024-10-17 14:09 +00:00"),
        ("https://pola.lt/pola-kortele/kaip-gauti/", 0, "2024-11-12 09:17 +00:00"),
        ("https://pola.lt/renginiai/", 0, "2024-12-11 15:28 +00:00"),
        ("https://pola.lt/pola-kortele/apie-pola-kortele/", 1, "2024-12-18 14:33 +00:00"),
        ("https://pola.lt/verslo-parama/", 0, "2024-12-18 14:35 +00:00"),
        ("https://pola.lt/apie-pola/apie-pola/", 0, "2024-12-18 14:38 +00:00"),
        ("https://pola.lt/apie-pola/pola-draugai/", 0, "2024-12-18 14:44 +00:00"),
        ("https://pola.lt/apie-pola/kiti-apie-mus/", 49, "2024-12-18 14:54 +00:00"),
        ("https://pola.lt/apie-pola/pola-dokumentai/", 0, "2025-01-03 12:36 +00:00"),
        ("https://pola.lt/pola-kortele/atsiimk-susitikus-su-pola-atstovais/", 0, "2025-01-10 07:07 +00:00"),
        ("https://pola.lt/pola-kortele/pola-ambasadoriai/", 0, "2025-01-10 07:15 +00:00"),
        ("https://pola.lt/pola-kortele/pola-nuolaidos/", 0, "2025-01-21 07:00 +00:00"),
        ("https://pola.lt/apie-pola/projektai/", 0, "2025-01-21 09:12 +00:00"),
        ("https://pola.lt/pola-kortele/pola-kvietimai/", 0, "2025-01-28 19:38 +00:00"),
        ("https://pola.lt/pacientu-gidai/", 1, "2025-02-05 07:39 +00:00"),
        ("https://pola.lt/discounts/", 0, "2025-02-05 07:58 +00:00"),
        ("https://pola.lt/discounts/only-good-vibes/", 1, "2019-04-04 14:46 +00:00"),
        ("https://pola.lt/discounts/rovifarma-vaistine/", 0, "2019-04-04 15:01 +00:00"),
        ("https://pola.lt/discounts/mo-muziejus/", 1, "2025-02-05 07:58 +00:00"),
        ("https://pola.lt/en/discounts/", 0, "2025-02-05 07:58 +00:00"),
        ("https://pola.lt/ru/discounts/", 0, "2025-02-05 07:58 +00:00"),
        ("https://pola.lt/discounts/only-good-vibes/", 1, "2019-04-04 14:46 +00:00"),
        ("https://pola.lt/discounts/rovifarma-vaistine/", 0, "2019-04-04 15:01 +00:00"),
        ("https://pola.lt/discounts/grozio-salonas-anna/", 1, "2019-04-04 15:10 +00:00"),
        ("https://pola.lt/discounts/grozio-salonas-laura/", 1, "2019-04-04 15:21 +00:00"),
        ("https://pola.lt/discounts/grozio-salonas-jelena/", 1, "2019-04-15 07:02 +00:00"),
        ("https://pola.lt/discounts/albadenta/", 1, "2019-05-27 16:33 +00:00"),
        ("https://pola.lt/discounts/alytaus-prc/", 1, "2019-05-27 16:34 +00:00"),
        ("https://pola.lt/discounts/dantu-estetika/", 1, "2019-05-27 16:36 +00:00"),
        ("https://pola.lt/discounts/emandia/", 1, "2019-05-27 16:36 +00:00"),
        ("https://pola.lt/discounts/eurovaistine/", 1, "2019-05-27 16:37 +00:00"),
        ("https://pola.lt/discounts/fielmann/", 1, "2019-05-27 16:38 +00:00"),
        ("https://pola.lt/discounts/gmt-beauty/", 1, "2019-05-27 16:38 +00:00"),
        ("https://pola.lt/discounts/ne-tik-makaronai/", 1, "2019-05-27 16:42 +00:00"),
        ("https://pola.lt/discounts/optikos-pasaulis/", 1, "2019-05-27 16:43 +00:00"),
        ("https://pola.lt/discounts/peleda/", 1, "2019-05-27 16:44 +00:00"),
        ("https://pola.lt/discounts/pirmas-zingsnis/", 1, "2019-05-27 16:44 +00:00"),
        ("https://pola.lt/discounts/pprc/", 1, "2019-05-27 16:44 +00:00"),
        ("https://pola.lt/discounts/prc-taurage/", 1, "2019-05-27 16:44 +00:00"),
        ("https://pola.lt/discounts/romainiu/", 1, "2019-05-27 16:45 +00:00"),
        ("https://pola.lt/discounts/tulpe/", 1, "2019-05-27 16:46 +00:00"),
        ("https://pola.lt/discounts/valerijonas/", 1, "2019-05-27 16:47 +00:00"),
        ("https://pola.lt/discounts/vildega/", 1, "2019-05-27 16:47 +00:00"),
        ("https://pola.lt/discounts/medicina-practica/", 1, "2019-06-18 06:35 +00:00"),
        ("https://pola.lt/discounts/prodenta/", 1, "2019-06-18 08:07 +00:00"),
        ("https://pola.lt/discounts/uab-baltic-medics/", 1, "2019-06-18 08:12 +00:00"),
        ("https://pola.lt/discounts/spartakas/", 1, "2019-06-18 08:16 +00:00"),
        ("https://pola.lt/discounts/rinkis-eko/", 1, "2020-05-19 14:22 +00:00"),
        ("https://pola.lt/discounts/versalis/", 1, "2020-05-19 15:37 +00:00"),
        ("https://pola.lt/discounts/beautel/", 0, "2020-10-01 06:13 +00:00"),
        ("https://pola.lt/discounts/valdovu-rumu-muziejus/", 1, "2020-11-05 15:52 +00:00"),
        ("https://pola.lt/discounts/norfos-vaistine/", 1, "2020-11-26 09:28 +00:00"),
        ("https://pola.lt/discounts/lengvata-transportui/", 1, "2021-03-02 09:14 +00:00"),
        ("https://pola.lt/discounts/ort-optika/", 1, "2021-03-17 14:02 +00:00"),
        ("https://pola.lt/discounts/slaugivita/", 1, "2021-04-07 10:25 +00:00"),
        ("https://pola.lt/discounts/slaugyk-lt/", 1, "2021-04-21 09:21 +00:00"),
        ("https://pola.lt/discounts/medtest/", 1, "2021-04-21 09:29 +00:00"),
        ("https://pola.lt/discounts/ortopro/", 1, "2021-11-10 12:37 +00:00"),
        ("https://pola.lt/discounts/mano-vaistine/", 1, "2022-01-20 10:19 +00:00"),
        ("https://pola.lt/discounts/aerobikos-studija-audra/", 1, "2022-01-24 13:28 +00:00"),
        ("https://pola.lt/discounts/akiniai-visiems/", 1, "2022-01-24 14:04 +00:00"),
        ("https://pola.lt/discounts/anahata/", 1, "2022-01-24 14:15 +00:00"),
        ("https://pola.lt/discounts/camelia/", 1, "2022-01-24 14:29 +00:00"),
        ("https://pola.lt/discounts/gintarine-vaistine/", 1, "2022-01-25 06:40 +00:00"),
        ("https://pola.lt/discounts/grand-spa-lietuva/", 1, "2022-01-25 06:45 +00:00"),
        ("https://pola.lt/discounts/kvapu-namai/", 1, "2022-01-25 07:46 +00:00"),
        ("https://pola.lt/discounts/urticae/", 1, "2022-01-25 08:41 +00:00"),
        ("https://pola.lt/discounts/manikiuro-meistre-rita-bikeliene/", 0, "2022-01-25 10:00 +00:00"),
        ("https://pola.lt/discounts/mygym/", 1, "2022-02-28 17:02 +00:00"),
        ("https://pola.lt/discounts/vsi-kelmes-profesinio-rengimo-centras/", 1, "2022-02-28 17:24 +00:00"),
        ("https://pola.lt/discounts/aliejus/", 1, "2022-02-28 17:34 +00:00"),
        ("https://pola.lt/discounts/https-www-kemperiai365-lt-kemperiu-nuoma/", 1, "2022-03-02 12:31 +00:00"),
        ("https://pola.lt/discounts/optometrijos-centras/", 1, "2022-03-28 13:40 +00:00"),
        ("https://pola.lt/discounts/gamtos-maistas/", 1, "2022-04-01 10:22 +00:00"),
        ("https://pola.lt/discounts/maistas-sveikatai/", 1, "2022-04-01 10:23 +00:00"),
        ("https://pola.lt/discounts/pomi-t/", 1, "2022-04-01 10:24 +00:00"),
        ("https://pola.lt/discounts/ekspoziciju-centras-uab/", 1, "2022-04-01 10:39 +00:00"),
        ("https://pola.lt/discounts/audiomedika/", 1, "2022-05-02 11:06 +00:00"),
        ("https://pola.lt/discounts/vandens-jonizatoriai/", 1, "2022-05-02 11:27 +00:00"),
        ("https://pola.lt/discounts/teida-2/", 1, "2022-05-02 11:42 +00:00"),
        ("https://pola.lt/discounts/ori-diena/", 1, "2022-05-05 06:19 +00:00"),
        ("https://pola.lt/discounts/biofirst/", 1, "2022-05-09 08:18 +00:00"),
        ("https://pola.lt/discounts/estetines-chirurgijos-centras/", 1, "2022-05-09 08:19 +00:00"),
        ("https://pola.lt/discounts/fizio-medika/", 1, "2022-05-09 08:20 +00:00"),
        ("https://pola.lt/discounts/geroves-klinika/", 1, "2022-05-09 08:22 +00:00"),
        ("https://pola.lt/discounts/health-optimizing/", 1, "2022-05-09 08:24 +00:00"),
        ("https://pola.lt/discounts/innmed/", 1, "2022-05-09 08:25 +00:00"),
        ("https://pola.lt/discounts/naturalaus-gydymo-centras/", 1, "2022-05-09 08:26 +00:00"),
        ("https://pola.lt/discounts/osteomedika/", 1, "2022-05-09 08:27 +00:00"),
        ("https://pola.lt/discounts/uneja/", 1, "2022-05-09 08:29 +00:00"),
        ("https://pola.lt/discounts/privati-psichologe/", 1, "2022-05-09 08:30 +00:00"),
        ("https://pola.lt/discounts/paliesiaus-klinika/", 1, "2022-05-09 08:31 +00:00"),
        ("https://pola.lt/discounts/lorna-medicinos-centras/", 1, "2022-05-09 08:35 +00:00"),
        ("https://pola.lt/discounts/menas-buti/", 1, "2022-05-09 08:36 +00:00"),
        ("https://pola.lt/discounts/jauskis-geriau/", 1, "2022-05-09 08:39 +00:00"),
        ("https://pola.lt/discounts/kosmetologe-masazuotoja-jelena/", 1, "2022-05-09 08:42 +00:00"),
        ("https://pola.lt/discounts/dziugas-gym/", 1, "2022-05-09 08:43 +00:00"),
        ("https://pola.lt/discounts/slamutis/", 1, "2022-05-09 08:48 +00:00"),
        ("https://pola.lt/discounts/sveikuoliai/", 1, "2022-05-09 09:06 +00:00"),
        ("https://pola.lt/discounts/seimos-sveikatos-prieziuros-centras/", 1, "2022-05-09 09:10 +00:00"),
        ("https://pola.lt/discounts/gradiali-2/", 1, "2022-05-09 09:13 +00:00"),
        ("https://pola.lt/discounts/energetikas/", 1, "2022-05-09 09:18 +00:00"),
        ("https://pola.lt/discounts/savanoriu-kineziterapijos-klinika/", 1, "2022-05-10 06:46 +00:00"),
        ("https://pola.lt/discounts/ostemeda/", 1, "2022-05-11 07:53 +00:00"),
        ("https://pola.lt/discounts/innovita-klinika/", 1, "2022-08-01 12:56 +00:00"),
        ("https://pola.lt/discounts/pesciuju-turas/", 1, "2022-09-21 08:14 +00:00"),
        ("https://pola.lt/discounts/norsan/", 1, "2022-09-21 08:18 +00:00"),
        ("https://pola.lt/discounts/ramuneles-vaistine/", 1, "2022-10-07 09:56 +00:00"),
        ("https://pola.lt/discounts/medinet/", 1, "2022-10-13 13:12 +00:00"),
        ("https://pola.lt/discounts/daiveda/", 0, "2022-11-17 15:00 +00:00"),
        ("https://pola.lt/discounts/z-kazakeviciaus-implantologijos-centras/", 1, "2022-11-17 15:12 +00:00"),
        ("https://pola.lt/discounts/clinic-dpc/", 1, "2022-11-18 08:57 +00:00"),
        ("https://pola.lt/discounts/ignalinos-sporto-pramogu-centras/", 1, "2022-11-22 14:57 +00:00"),
        ("https://pola.lt/discounts/belonta/", 1, "2022-11-28 09:28 +00:00"),
        ("https://pola.lt/discounts/sveikatos-sprendimai/", 1, "2022-11-28 11:43 +00:00"),
        ("https://pola.lt/discounts/aconitum/", 1, "2022-11-28 11:49 +00:00"),
        ("https://pola.lt/discounts/biofarmacija/", 1, "2022-11-28 11:57 +00:00"),
        ("https://pola.lt/discounts/thymuskin/", 1, "2022-11-28 12:15 +00:00"),
        ("https://pola.lt/discounts/hairclinic/", 1, "2022-11-28 12:47 +00:00"),
        ("https://pola.lt/discounts/medicinos-strategija-cosme-lt/", 1, "2022-11-28 14:52 +00:00"),

    ]
    
    # Filter out URLs that already exist in DB
    filtered_urls = []
    for url_data in urls_data:
        url, images, last_mod = url_data
        if url not in existing_urls:
            filtered_urls.append(PolaURL.from_string(url, images, last_mod))
        else:
            print(f"Skipping existing URL: {url}")
    
    return filtered_urls

@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]
    semantic_context: str = ""  # Added for semantic context

def chunk_text(text: str, chunk_size: int = 2000) -> List[str]:
    """Split text into chunks with improved semantic boundaries.
    
    This implementation:
    1. Respects markdown headers
    2. Maintains code block integrity
    3. Preserves semantic context
    4. Uses overlapping windows for better context
    """
    chunks = []
    current_chunk = []
    current_size = 0
    overlap_size = 200  # Overlap between chunks
    
    # Split into lines while preserving markdown structure
    lines = text.split('\n')
    
    for line in lines:
        line_size = len(line)
        
        # Start new chunk if current is too big
        if current_size + line_size > chunk_size and current_chunk:
            # Add overlap from previous chunk
            overlap = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
            chunks.append('\n'.join(current_chunk))
            current_chunk = overlap.copy()  # Start with overlap
            current_size = sum(len(l) for l in current_chunk)
        
        # Special handling for headers and code blocks
        if line.startswith('#') or line.startswith('```'):
            if current_chunk:  # End current chunk at semantic boundary
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        current_chunk.append(line)
        current_size += line_size
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

async def get_title_and_summary(chunk: str, url: str) -> Dict[str, str]:
    """Extract title and summary using GPT-4 with rate limiting."""
    global last_completion_time
    
    async with completions_semaphore:
        # Ensure minimum delay between requests (60/RPM seconds)
        current_time = time.time()
        time_since_last = current_time - last_completion_time
        if time_since_last < (60 / COMPLETIONS_RPM):
            await asyncio.sleep((60 / COMPLETIONS_RPM) - time_since_last)
        
        system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
        Return a JSON object with 'title' and 'summary' keys.
        For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
        For the summary: Create a concise summary of the main points in this chunk.
        Keep both title and summary concise but informative."""
        
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"URL: {url}\n\nContent:\n{chunk[:1000]}..."}
                ],
                response_format={ "type": "json_object" }
            )
            last_completion_time = time.time()
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error getting title and summary: {e}")
            return {"title": "Error processing title", "summary": "Error processing summary"}

async def get_embedding(text: str) -> List[float]:
    """Get embedding vector from OpenAI with rate limiting."""
    global last_embedding_time
    
    async with embeddings_semaphore:
        # Ensure minimum delay between requests (60/RPM seconds)
        current_time = time.time()
        time_since_last = current_time - last_embedding_time
        if time_since_last < (60 / EMBEDDINGS_RPM):
            await asyncio.sleep((60 / EMBEDDINGS_RPM) - time_since_last)
        
        try:
            response = await embeddings_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )

            last_embedding_time = time.time()
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0] * 1536  # Return zero vector on error

async def process_chunk(chunk: str, chunk_number: int, url: PolaURL) -> Document:
    """Process a single chunk of text into a Document."""
    # Get title and summary
    extracted = await get_title_and_summary(chunk, url.url)
    
    # Get embedding
    embedding = await get_embedding(chunk)
    
    # Create rich metadata
    metadata = {
        "source": "pola_docs",
        "chunk_number": chunk_number,
        "chunk_size": len(chunk),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "url": url.url,
        "url_path": urlparse(url.url).path,
        "image_count": url.image_count,
        "last_modified": url.last_modified.isoformat(),
        "title": extracted['title'],
        "summary": extracted['summary'],
        "content_type": "webpage",
        "language": "lt",  # Lithuanian content
        "domain": urlparse(url.url).netloc,
        "section": urlparse(url.url).path.strip("/").split("/")[0] or "home"
    }
    
    # Create enhanced content with semantic markers
    enhanced_content = f"""Title: {extracted['title']}
Summary: {extracted['summary']}
URL: {url.url}
Content:
{chunk}"""
    
    return Document(
        page_content=enhanced_content,
        metadata=metadata
    )

async def process_and_store_document(url: PolaURL, markdown: str):
    """Process a document and store its chunks."""
    try:
        # Split into chunks
        chunks = chunk_text(markdown)
        
        # Process chunks in parallel
        tasks = [
            process_chunk(chunk, i, url) 
            for i, chunk in enumerate(chunks)
        ]
        processed_chunks = await asyncio.gather(*tasks)
        
        # Store documents using VectorStoreManager
        vector_store.add_documents(processed_chunks)
        print(f"Successfully stored {len(processed_chunks)} chunks for {url.url}")
    except Exception as e:
        print(f"Error processing document {url.url}: {str(e)}")
        return

async def crawl_parallel(urls: List[PolaURL], max_concurrent: int = 5):
    """Crawl multiple URLs in parallel with a concurrency limit."""
    # Create browser configuration with longer timeout and retry settings
    browser_config = BrowserConfig(
        headless=True,
        verbose=True,  # Enable verbose logging
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

    # Create the crawler instance with a single browser
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        # Create a semaphore to limit concurrency
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
                        print(f"Successfully crawled: {pola_url.url}")
                        await process_and_store_document(pola_url, result.markdown_v2.raw_markdown)
                    else:
                        print(f"Failed to crawl: {pola_url.url} - Error: {result.error_message}")
                except Exception as e:
                    print(f"Error processing {pola_url.url}: {str(e)}")
        
        # Process URLs in smaller batches to better manage resources
        batch_size = 5
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1} of {(len(urls) + batch_size - 1)//batch_size}")
            await asyncio.gather(*[process_url(url) for url in batch])
            # Add a small delay between batches
            await asyncio.sleep(1)
            
    finally:
        print("Closing browser...")
        await crawler.close()
        print("Browser closed.")

async def main():
    # Get URLs from manual list
    urls = get_pola_urls()
    if not urls:
        print("No URLs found to crawl")
        return
    
    print(f"Found {len(urls)} URLs to crawl")
    try:
        await crawl_parallel(urls)
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
    finally:
        print("Crawling completed.")

if __name__ == "__main__":
    asyncio.run(main())