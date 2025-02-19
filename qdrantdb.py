from qdrant_client import QdrantClient, models
from qdrant_client.http import models as rest
from qdrant_client.http.models import Distance, VectorParams, OptimizersConfigDiff

# Connect to Qdrant
client = QdrantClient(
    url="https://b88198bc-6212-4390-bbac-b1930f543812.europe-west3-0.gcp.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzQ3MDY5MzcyfQ.plLwDbnIi7ggn_d98e-OsxpF60lcNq9nzZ0EzwFAnQw"
)

# Check if collection exists
if client.collection_exists("Information"):
    # Delete if exists
    client.delete_collection("Information")

# Create new collection with optimized configuration
client.create_collection(
    collection_name="Information",
    vectors_config=models.VectorParams(
        size=1536,  # OpenAI embedding size
        distance=models.Distance.COSINE,
        on_disk=True  # Store vectors on disk for larger datasets
    ),
    optimizers_config=models.OptimizersConfigDiff(
        indexing_threshold=20000,  # Optimize for larger dataset
        memmap_threshold=50000
    ),
    hnsw_config=models.HnswConfigDiff(  # Add HNSW index configuration
        m=16,  # Number of connections per element
        ef_construct=100,  # Size of the dynamic candidate list
        full_scan_threshold=10000  # Threshold for full scan vs index
    )
)

# Create payload indexes for efficient filtering
client.create_payload_index(
    collection_name="Information",
    field_name="source_type",
    field_schema=models.PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="Information",
    field_name="language",
    field_schema=models.PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="Information",
    field_name="url",
    field_schema=models.PayloadSchemaType.TEXT
)

# Verify collection info
collection_info = client.get_collection("Information")
print(f"Collection 'Information' created successfully!")
print(f"Vector size: {collection_info.config.params.vectors.size}")
print(f"Distance: {collection_info.config.params.vectors.distance}")
print(f"Indexed points: {collection_info.points_count}")