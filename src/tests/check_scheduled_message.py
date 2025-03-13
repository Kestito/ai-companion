"""
Check the status of a scheduled message.
"""

import asyncio
import sys
from ai_companion.utils.supabase import get_supabase_client

async def check_scheduled_message(message_id):
    """Check the status of a scheduled message."""
    print(f"Checking scheduled message with ID: {message_id}")
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Get the scheduled message
    result = supabase.table("scheduled_messages").select("*").eq("id", message_id).execute()
    
    # Check if we got results
    if result.data and len(result.data) > 0:
        message = result.data[0]
        print(f"Message found! Details:")
        print(f"  ID: {message.get('id')}")
        print(f"  Status: {message.get('status')}")
        print(f"  Scheduled Time: {message.get('scheduled_time')}")
        print(f"  Platform: {message.get('platform')}")
        print(f"  Patient ID: {message.get('patient_id')}")
        print(f"  Recipient: {message.get('recipient_id')}")
        print(f"  Content: {message.get('message_content')}")
        
        return message
    else:
        print(f"No message found with ID: {message_id}")
        return None

if __name__ == "__main__":
    # Get message ID from command line or use the one from our test
    message_id = sys.argv[1] if len(sys.argv) > 1 else "cbd37724-e734-4fdb-aea7-7ed26ddfee9a"
    
    # Run the check
    asyncio.run(check_scheduled_message(message_id)) 