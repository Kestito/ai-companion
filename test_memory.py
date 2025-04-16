import asyncio
from src.ai_companion.modules.memory.short_term.short_memory import ShortTermMemoryManager

async def test_memory():
    print("Creating memory manager...")
    manager = ShortTermMemoryManager()
    
    print("Storing test memory...")
    memory = await manager.store_memory(
        content='Test memory content', 
        ttl_minutes=60, 
        metadata={
            'user_id': 'test-user', 
            'session_id': 'test-session',
            'chat_id': 'test-chat',
            'platform': 'test'
        }
    )
    
    print(f'Memory stored: {memory.id}')
    
    print("Retrieving active memories...")
    active = await manager.get_active_memories()
    print(f'Active memories: {len(active)}')
    
    for mem in active:
        print(f'- {mem.id}: {mem.content}')
    
    return memory.id

if __name__ == "__main__":
    memory_id = asyncio.run(test_memory())
    print(f"Test completed, created memory: {memory_id}") 