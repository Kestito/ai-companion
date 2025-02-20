import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def delete_duplicate_records():
    try:
        # First, get the document IDs we want to delete
        response = supabase.table('documents') \
            .select('id') \
            .eq('title', 'Svetainės slapukų naudojimo taisyklės') \
            .execute()
        
        if not response.data:
            print("No matching records found")
            return None
            
        # Delete the records from documents table (this will cascade to document_chunks)
        result = supabase.table('documents') \
            .delete() \
            .eq('title', 'Svetainės slapukų naudojimo taisyklės') \
            .execute()
        
        print(f"Successfully deleted {len(result.data)} records")
        return result.data
        
    except Exception as e:
        print(f"Error deleting records: {e}")
        return None

if __name__ == "__main__":
    delete_duplicate_records() 