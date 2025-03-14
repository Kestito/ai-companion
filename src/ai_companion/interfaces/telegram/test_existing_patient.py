import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_existing_telegram_user():
    """
    Test handling a returning Telegram user that already has a patient record.
    This is a standalone simulation with no external dependencies.
    """
    logger.info("=== RETURNING TELEGRAM USER TEST ===")
    logger.info("This test simulates how the system handles a returning Telegram user")
    
    logger.info("\n1. SIMULATING TELEGRAM MESSAGE RECEPTION")
    # Create a simulated Telegram message object
    telegram_message = {
        "message_id": 87654399,
        "from": {
            "id": 42424242,  # Same Telegram user ID as previous test
            "is_bot": False,
            "first_name": "Maria",
            "last_name": "Garcia",
            "username": "mariagarcia",
            "language_code": "en"
        },
        "chat": {
            "id": 42424242,
            "first_name": "Maria",
            "last_name": "Garcia",
            "username": "mariagarcia",
            "type": "private"
        },
        "date": int(datetime.now().timestamp()),
        "text": "How are you doing today? I have a question about my appointment."
    }
    
    chat_id = telegram_message["chat"]["id"]
    session_id = str(chat_id)
    content = telegram_message["text"]
    
    logger.info(f"Received message from chat ID: {chat_id}")
    logger.info(f"Message content: '{content}'")
    
    logger.info("\n2. EXTRACTING USER METADATA")
    # Extract user metadata from Telegram message
    user_metadata = {
        "platform": "telegram",
        "user_id": str(telegram_message["from"]["id"]),
        "chat_id": str(chat_id)
    }
    
    # Add more user details
    user = telegram_message["from"]
    user_metadata["telegram_user"] = user
    if "username" in user:
        user_metadata["username"] = user["username"]
    if "first_name" in user:
        user_metadata["first_name"] = user["first_name"]
    if "last_name" in user:
        user_metadata["last_name"] = user["last_name"]
    
    logger.info(f"Generated user metadata: {json.dumps(user_metadata, indent=2)}")
    
    logger.info("\n3. CREATING HUMAN MESSAGE WITH METADATA")
    # Simulate LangChain HumanMessage creation
    human_message = {
        "type": "human",
        "content": content,
        "metadata": user_metadata
    }
    logger.info("HumanMessage created with metadata attached")
    
    logger.info("\n4. ROUTER NODE: CHECKING FOR EXISTING PATIENT")
    # Simulate database check - this time finding an existing patient
    logger.info("Checking Supabase for existing patient with user ID: " + user_metadata["user_id"])
    
    # In real system, would search Supabase like:
    # metadata_search = f'%"user_id": "{user_metadata["user_id"]}"%'
    # result = supabase.table("patients").select("id").like("email", metadata_search).execute()
    
    # Simulate finding an existing patient
    existing_patient_id = "existing-patient-uuid-54321"
    logger.info(f"Found existing patient with ID: {existing_patient_id}")
    
    logger.info("\n5. RETRIEVING PATIENT INFORMATION")
    # Simulate fetching patient details from the database
    patient_record = {
        "id": existing_patient_id,
        "name": "Maria Garcia",
        "phone": "telegram:42424242",
        "status": "Active",
        "risk_level": "Low",
        "last_contact": "2025-03-12T14:23:12.321456",
        "created_at": "2025-03-10T09:45:22.654321",
        "source": "telegram",
        "email": json.dumps({
            "platform": "telegram",
            "user_id": "42424242",
            "username": "mariagarcia"
        })
    }
    
    logger.info(f"Retrieved patient record: {json.dumps(patient_record, indent=2)}")
    
    logger.info("\n6. UPDATING LAST CONTACT TIME")
    # Update last contact timestamp
    now = datetime.now().isoformat()
    patient_record["last_contact"] = now
    logger.info(f"Updated last_contact to: {now}")
    
    logger.info("\n7. PROCESSING MESSAGE THROUGH CONVERSATION WORKFLOW")
    # Since this is a returning user, the message gets routed to the conversation workflow
    logger.info("Routing message to conversation_node for normal processing")
    
    # Simulate conversation response
    conversation_response = "Hello Maria! I'm doing well, thank you for asking. Regarding your appointment, I'd be happy to help. Could you please specify which appointment you're inquiring about?"
    
    logger.info("\n8. GENERATING RESPONSE")
    # Generate response message
    logger.info(f"Response message: '{conversation_response}'")
    
    logger.info("\n9. RETURNING RESULT")
    # Build result object
    result = {
        "messages": [{
            "type": "ai",
            "content": conversation_response
        }],
        "patient_id": existing_patient_id
    }
    
    logger.info("=== TEST COMPLETE ===")
    return result

# Run the test
if __name__ == "__main__":
    print("\n")
    result = asyncio.run(test_existing_telegram_user())
    print("\nFinal result:", json.dumps(result, indent=2))
    print("\n") 