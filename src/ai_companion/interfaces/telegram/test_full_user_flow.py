import asyncio
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_telegram_user_flow():
    """
    Test a complete flow for a Telegram user:
    1. First message → New patient registration
    2. Second message → Normal conversation as existing patient
    3. Third message → Scheduling a reminder
    
    This is a standalone simulation with no external dependencies.
    """
    logger.info("=== COMPLETE TELEGRAM USER FLOW TEST ===")
    logger.info("This test simulates the entire user journey from first message to scheduling")
    patient_id = None
    
    #-------------------- STEP 1: FIRST MESSAGE & REGISTRATION --------------------#
    logger.info("\n\n=================== FIRST MESSAGE (NEW USER) ===================")
    
    # Create a simulated first Telegram message
    telegram_message_1 = {
        "message_id": 87654321,
        "from": {
            "id": 42424242,
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
    
    # Process first message
    chat_id = telegram_message_1["chat"]["id"]
    content = telegram_message_1["text"]
    
    logger.info(f"Received first message from chat ID: {chat_id}")
    logger.info(f"Message content: '{content}'")
    
    # Extract user metadata
    user_metadata = {
        "platform": "telegram",
        "user_id": str(telegram_message_1["from"]["id"]),
        "chat_id": str(chat_id)
    }
    
    # Add detailed user info
    user = telegram_message_1["from"]
    user_metadata["telegram_user"] = user
    if "username" in user:
        user_metadata["username"] = user["username"]
    if "first_name" in user:
        user_metadata["first_name"] = user["first_name"]
    if "last_name" in user:
        user_metadata["last_name"] = user["last_name"]
    
    # Router node: Check for existing patient - won't find one
    logger.info("Router node: Checking for existing patient - none found")
    logger.info("Routing to patient_registration_node for new user registration")
    
    # Patient registration: Creating new patient
    user_name = None
    if "telegram_user" in user_metadata:
        telegram_user = user_metadata["telegram_user"]
        if "first_name" in telegram_user:
            first_name = telegram_user["first_name"]
            last_name = telegram_user.get("last_name", "")
            user_name = f"{first_name} {last_name}".strip()
    
    # Create patient record
    now = datetime.now().isoformat()
    patient_data = {
        "name": user_name,
        "phone": f"telegram:{user_metadata['user_id']}",
        "status": "Active",
        "risk_level": "Low",
        "last_contact": now,
        "created_at": now,
        "source": "telegram"
    }
    
    # Add platform metadata as JSON in email field
    platform_metadata = {
        "platform": "telegram",
        "user_id": user_metadata["user_id"],
        "username": user_metadata.get("username")
    }
    patient_data["email"] = json.dumps(platform_metadata)
    
    logger.info(f"Creating new patient record: {json.dumps(patient_data, indent=2)}")
    
    # Simulate database insert
    patient_id = "new-patient-uuid-12345"
    logger.info(f"New patient created with ID: {patient_id}")
    
    # Generate response for first message (registration confirmation)
    response_1 = "Thank you! I've registered you as a new patient in our system. You can now use our services through this Telegram chat."
    logger.info(f"Response to first message: '{response_1}'")
    
    #-------------------- STEP 2: SECOND MESSAGE (EXISTING USER) --------------------#
    logger.info("\n\n================ SECOND MESSAGE (RETURNING USER) ================")
    
    # Create a simulated second message from the same user
    telegram_message_2 = {
        "message_id": 87654322,
        "from": {
            "id": 42424242,  # Same user ID
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
        "text": "I have a chronic back pain. Can I schedule an appointment with a specialist?"
    }
    
    # Process second message
    content_2 = telegram_message_2["text"]
    logger.info(f"Received second message: '{content_2}'")
    
    # Router node: Check for existing patient - will find one this time
    logger.info("Router node: Checking for existing patient")
    logger.info(f"Found existing patient with ID: {patient_id}")
    
    # Update last contact time
    last_contact = datetime.now().isoformat()
    logger.info(f"Updating last_contact time to: {last_contact}")
    
    # Process through conversation node for normal response
    logger.info("Routing to conversation_node for normal processing")
    
    # Generate response for second message (normal conversation)
    response_2 = "I'm sorry to hear about your chronic back pain. Yes, we can definitely help you schedule an appointment with one of our specialists. We have several orthopedic specialists available. The earliest available appointments are next week. Would you like me to schedule one for you, or would you prefer to receive a reminder to schedule it yourself?"
    logger.info(f"Response to second message: '{response_2}'")
    
    #-------------------- STEP 3: THIRD MESSAGE (SCHEDULING) --------------------#
    logger.info("\n\n================= THIRD MESSAGE (SCHEDULING) =================")
    
    # Create a simulated third message with scheduling request
    telegram_message_3 = {
        "message_id": 87654323,
        "from": {
            "id": 42424242,  # Same user ID
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
        "text": "/schedule tomorrow at 10am Please schedule my appointment with the orthopedic specialist"
    }
    
    # Process third message
    content_3 = telegram_message_3["text"]
    logger.info(f"Received third message: '{content_3}'")
    
    # Router node: Check for schedule command
    logger.info("Router node: Detected scheduling command")
    logger.info("Routing to schedule_message_node")
    
    # Verify patient exists
    logger.info(f"Verified existing patient with ID: {patient_id}")
    
    # Parse scheduling command
    command_parts = content_3.split(" ", 4)
    
    # Extract scheduling information
    when = " ".join(command_parts[1:4])  # 'tomorrow at 10am'
    message_content = command_parts[4]  # The actual message
    
    # Calculate actual scheduled time
    tomorrow = datetime.now() + timedelta(days=1)
    scheduled_date = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    formatted_time = scheduled_date.isoformat()
    
    logger.info(f"Parsed schedule time: {when} → {formatted_time}")
    logger.info(f"Parsed message content: '{message_content}'")
    
    # Create scheduled message record
    schedule_data = {
        "id": "schedule-uuid-67890",
        "patient_id": patient_id,
        "recipient_id": user_metadata["user_id"],
        "platform": "telegram",
        "message_content": message_content,
        "scheduled_time": formatted_time,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    logger.info(f"Created scheduled message record: {json.dumps(schedule_data, indent=2)}")
    
    # Generate confirmation response
    scheduled_time_display = scheduled_date.strftime("%A, %B %d at %I:%M %p")
    response_3 = f"I've scheduled your message for {scheduled_time_display}. I'll remind you then about scheduling your appointment with our orthopedic specialist."
    logger.info(f"Response to third message: '{response_3}'")
    
    #-------------------- SUMMARY --------------------#
    logger.info("\n\n==================== COMPLETE FLOW SUMMARY ====================")
    logger.info(f"Patient ID: {patient_id}")
    logger.info(f"Patient Name: {user_name}")
    logger.info(f"Schedule ID: {schedule_data['id']}")
    logger.info("Message 1: First contact → Patient registration")
    logger.info("Message 2: Medical inquiry → Normal conversation")
    logger.info("Message 3: Scheduling command → Reminder scheduled")
    
    # Compose final result
    result = {
        "patient_id": patient_id,
        "patient_name": user_name,
        "schedule_id": schedule_data["id"],
        "interactions": [
            {
                "message": telegram_message_1["text"],
                "response": response_1,
                "action": "patient_registration"
            },
            {
                "message": telegram_message_2["text"],
                "response": response_2,
                "action": "conversation"
            },
            {
                "message": telegram_message_3["text"],
                "response": response_3,
                "action": "message_scheduling"
            }
        ]
    }
    
    logger.info("=== TEST COMPLETE ===")
    return result

# Run the test
if __name__ == "__main__":
    print("\n")
    result = asyncio.run(test_complete_telegram_user_flow())
    print("\nFinal result:", json.dumps(result, indent=2))
    print("\n") 