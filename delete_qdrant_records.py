from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, PointIdsList, FieldCondition
from typing import Optional, List, Union
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def delete_qdrant_records(collection_name: str, filter_conditions: Optional[Union[Filter, dict]] = None) -> None:
    """
    Delete records from a Qdrant collection based on filter conditions
    Args:
        collection_name: Name of the collection to delete from
        filter_conditions: Optional filter conditions to specify which records to delete
    """
    try:
        # Initialize Qdrant client using environment variables
        client = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY')
        )
        
        # Get initial count
        initial_count = client.get_collection(collection_name).points_count
        print(f"Initial points in {collection_name}: {initial_count}")
        
        if initial_count == 0:
            print(f"No points to delete in {collection_name}")
            return
        
        if filter_conditions:
            # Get points matching the filter
            search_result = client.scroll(
                collection_name=collection_name,
                filter=filter_conditions,
                limit=initial_count
            )
            points_to_delete = [point.id for point in search_result[0]]
            
            if not points_to_delete:
                print("No points match the filter conditions")
                return
                
            # Delete specific points
            client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(
                    points=points_to_delete
                )
            )
        else:
            # Get all point IDs
            search_result = client.scroll(
                collection_name=collection_name,
                limit=initial_count
            )
            points_to_delete = [point.id for point in search_result[0]]
            
            # Delete all points
            client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(
                    points=points_to_delete
                )
            )
        
        # Get final count
        final_count = client.get_collection(collection_name).points_count
        deleted_count = initial_count - final_count
        
        print(f"Successfully deleted {deleted_count} points from {collection_name}")
        print(f"Remaining points: {final_count}")
        
    except Exception as e:
        print(f"Error deleting records from {collection_name}: {e}")

if __name__ == "__main__":
    # Example usage:
    # Delete all records from a collection
    delete_qdrant_records("Information")
    
    # Example of deleting with a filter
    # filter_conditions = Filter(
    #     must=[
    #         FieldCondition(
    #             key="source_type",
    #             match={"value": "specific_type"}
    #         )
    #     ]
    # )
    # delete_qdrant_records("Information", filter_conditions) 