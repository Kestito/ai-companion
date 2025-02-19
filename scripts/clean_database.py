import os
import sys
import asyncio
from typing import List
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Load environment variables
load_dotenv()

def get_qdrant_client() -> QdrantClient:
    """Initialize and return Qdrant client."""
    return QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

def get_all_collections(client: QdrantClient) -> List[str]:
    """Get list of all collection names."""
    try:
        collections = client.get_collections()
        return [collection.name for collection in collections.collections]
    except Exception as e:
        print(f"Error getting collections: {e}")
        return []

def delete_collection(client: QdrantClient, collection_name: str) -> bool:
    """Delete a single collection."""
    try:
        client.delete_collection(collection_name=collection_name)
        print(f"Successfully deleted collection: {collection_name}")
        return True
    except Exception as e:
        print(f"Error deleting collection {collection_name}: {e}")
        return False

def main():
    """Main function to delete all collections."""
    client = get_qdrant_client()
    
    # Get all collections
    collections = get_all_collections(client)
    
    if not collections:
        print("No collections found in the database.")
        return
    
    print("\nFound the following collections:")
    for i, collection in enumerate(collections, 1):
        print(f"{i}. {collection}")
    
    # Ask for confirmation
    confirmation = input("\nAre you sure you want to delete ALL collections? This action cannot be undone! (yes/no): ")
    
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return
    
    # Delete each collection
    success_count = 0
    fail_count = 0
    
    print("\nDeleting collections...")
    for collection in collections:
        if delete_collection(client, collection):
            success_count += 1
        else:
            fail_count += 1
    
    # Print summary
    print("\nDeletion Summary:")
    print(f"Total collections processed: {len(collections)}")
    print(f"Successfully deleted: {success_count}")
    print(f"Failed to delete: {fail_count}")

if __name__ == "__main__":
    main() 