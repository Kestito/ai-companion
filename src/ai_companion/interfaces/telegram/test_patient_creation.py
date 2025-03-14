import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_telegram_user_creation():
    """
    Test creating a new patient record from a Telegram user's first message.
    This is a standalone simulation with no external dependencies.
    """
    logger.info("=== TELEGRAM USER CREATION TEST ===")
    logger.info("This test simulates the entire process of creating a patient record from Telegram data")
    
    logger.info("\n1. SIMULATING TELEGRAM MESSAGE RECEPTION")
    # Create a simulated Telegram message object
    telegram_message = {
        "message_id": 87654321,
        "from": {
            "id": 42424242,  # Telegram user ID
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
        "text": "Hello, I'd like to get some information about your services."
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
    # Simulate database check
    logger.info("Checking Supabase for existing patient with user ID: " + user_metadata["user_id"])
    logger.info("No existing patient found - routing to patient_registration_node")
    
    logger.info("\n5. PATIENT REGISTRATION NODE: CREATING NEW PATIENT")
    # Extract name components
    user_name = None
    if "telegram_user" in user_metadata:
        telegram_user = user_metadata["telegram_user"]
        if "first_name" in telegram_user:
            first_name = telegram_user["first_name"]
            last_name = telegram_user.get("last_name", "")
            user_name = f"{first_name} {last_name}".strip()
    
    # Fallback if no name available
    if not user_name:
        user_name = f"Telegram User {user_metadata['user_id']}"
    
    logger.info(f"Using name from Telegram: {user_name}")
    
    # Create timestamp for registration
    now = datetime.now().isoformat()
    
    # Create patient record data
    patient_data = {
        "name": user_name,
        "phone": f"telegram:{user_metadata['user_id']}",
        "status": "Active",
        "risk_level": "Low",
        "last_contact": now,
        "created_at": now,
        "source": "telegram"
    }
    
    # Add platform metadata - stored in email field as JSON
    platform_metadata = {
        "platform": "telegram",
        "user_id": user_metadata["user_id"],
        "username": user_metadata.get("username")
    }
    patient_data["email"] = json.dumps(platform_metadata)
    
    logger.info(f"Patient data prepared: {json.dumps(patient_data, indent=2)}")
    
    logger.info("\n6. INSERTING PATIENT RECORD INTO DATABASE")
    # Simulate database insert
    new_patient_id = "new-patient-uuid-12345"
    logger.info(f"New patient created with ID: {new_patient_id}")
    
    logger.info("\n7. GENERATING RESPONSE MESSAGE")
    # Generate response
    response_message = "Thank you! I've registered you as a new patient in our system. You can now use our services through this Telegram chat."
    logger.info(f"Response message: '{response_message}'")
    
    logger.info("\n8. RETURNING RESULT")
    # Build result object
    result = {
        "messages": [{
            "type": "ai",
            "content": response_message
        }],
        "patient_id": new_patient_id
    }
    
    logger.info("=== TEST COMPLETE ===")
    return result

# Run the test
if __name__ == "__main__":
    print("\n")
    result = asyncio.run(test_telegram_user_creation())
    print("\nFinal result:", json.dumps(result, indent=2))
    print("\n") 