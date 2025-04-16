import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.ai_companion.utils.supabase import get_supabase_client
from src.ai_companion.modules.memory.short_term.short_memory import ShortTermMemoryManager

async def test_telegram_memory():
    print("=== Testing Telegram Memory Operations ===")
    
    # Create session ID
    session_id = f"test-{uuid.uuid4()}"
    print(f"Using session ID: {session_id}")
    
    # Setup checkpoint dir
    checkpoint_dir = os.path.join(os.getcwd(), "data", "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Create checkpointer
    checkpoint_file = os.path.join(checkpoint_dir, f"{session_id}.json")
    checkpointer = AsyncSqliteSaver(checkpoint_file)
    
    # Create test data
    user_id = "test-user"
    chat_id = "test-chat-123"
    platform = "telegram"
    memory_metadata = {
        "user_id": user_id,
        "chat_id": chat_id,
        "session_id": session_id,
        "message_type": "text"
    }
    
    # Test storing memory through ShortTermMemoryManager
    print("\n1. Testing ShortTermMemoryManager")
    memory_manager = ShortTermMemoryManager()
    memory = await memory_manager.store_memory(
        content="Test message from user", 
        ttl_minutes=60,
        metadata=memory_metadata
    )
    print(f"Memory stored: {memory.id}")
    
    # Get active memories
    active_memories = await memory_manager.get_active_memories()
    print(f"Active memories: {len(active_memories)}")
    for mem in active_memories:
        print(f"- {mem.id}: {mem.content}")
    
    # Test direct Supabase table operations
    print("\n2. Testing direct Supabase operations")
    supabase = get_supabase_client()
    
    if supabase:
        # Test checking schema
        try:
            print("\nChecking table schema...")
            schema_query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'short_term_memory' ORDER BY ordinal_position;"
            result = supabase.rpc("execute_sql", {"query": schema_query}).execute()
            if hasattr(result, 'data'):
                print(f"Schema result: {result.data}")
            else:
                print("No schema information available")
        except Exception as e:
            print(f"Schema check failed: {e}")
        
        # Test inserting a record with state
        try:
            print("\nTesting insert with correct schema...")
            conversation_data = {
                "user_message": "Test user message",
                "bot_response": "Test bot response",
                "timestamp": datetime.now().isoformat()
            }
            
            # Create a test state to store
            test_state = {
                "conversation_history": ["Test message 1", "Test message 2"],
                "context": {"test_key": "test_value"}
            }
            
            # Combine conversation data and state into context
            context_data = {
                "conversation": conversation_data,
                "state": test_state,
                "metadata": memory_metadata
            }
            
            # Insert record with correct schema
            memory_data = {
                "id": str(uuid.uuid4()),
                # Note: patient_id is required but has foreign key constraint
                # So we skip it for this test
                "context": context_data,
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
            }
            
            try:
                # Try insert with minimal fields
                result = supabase.table("short_term_memory").insert(memory_data).execute()
                if hasattr(result, 'data'):
                    print(f"Insert successful: {result.data}")
                else:
                    print("No data returned from insert operation")
            except Exception as e:
                print(f"Insert failed: {e}")
                
                # Try with null patient_id
                try:
                    memory_data["patient_id"] = None
                    result = supabase.table("short_term_memory").insert(memory_data).execute()
                    print(f"Insert with null patient_id: {result.data if hasattr(result, 'data') else 'No data'}")
                except Exception as e2:
                    print(f"Insert with null patient_id failed: {e2}")
        except Exception as e:
            print(f"Test insert operation failed: {e}")
    else:
        print("Supabase client not available")
    
    print("\n=== Test completed ===")
    
if __name__ == "__main__":
    asyncio.run(test_telegram_memory()) 