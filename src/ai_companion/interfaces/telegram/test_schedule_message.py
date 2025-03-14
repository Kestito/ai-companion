import asyncio
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_telegram_message_scheduling():
    """
    Test scheduling a message for an existing Telegram user.
    This is a standalone simulation with no external dependencies.
    """
    logger.info("=== TELEGRAM MESSAGE SCHEDULING TEST ===")
    logger.info("This test simulates scheduling a message for an existing Telegram user")
    
    logger.info("\n1. SIMULATING TELEGRAM MESSAGE RECEPTION")
    # Create a simulated Telegram message with a scheduling command
    telegram_message = {
        "message_id": 87654421,
        "from": {
            "id": 42424242,  # Same Telegram user ID as previous tests
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
        "text": "/schedule tomorrow at 9am Reminder for your doctor appointment with Dr. Smith"
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
    
    logger.info("\n4. ROUTER NODE: DETECTING SCHEDULING COMMAND")
    # Check for schedule message request using regex pattern: r'(?i)^/schedule'
    if content.lower().startswith('/schedule'):
        logger.info("Detected schedule message request - routing to schedule_message_node")
        workflow = "schedule_message_node"
    else:
        logger.info("Not a scheduling command - would route to conversation_node")
        workflow = "conversation_node"
    
    logger.info(f"Determined workflow: {workflow}")
    
    # Since this is a scheduling command, continue with scheduling process
    if workflow == "schedule_message_node":
        logger.info("\n5. CHECKING FOR EXISTING PATIENT")
        # Simulate finding an existing patient (same as in test_existing_patient.py)
        existing_patient_id = "existing-patient-uuid-54321"
        logger.info(f"Found existing patient with ID: {existing_patient_id}")
        
        logger.info("\n6. PARSING SCHEDULING COMMAND")
        # Parse the scheduling command to extract time and message
        command_parts = content.split(" ", 4)  # Split into max 4 parts: ['/schedule', 'tomorrow', 'at', '9am', 'message']
        
        # Extract scheduling information
        when = " ".join(command_parts[1:4])  # 'tomorrow at 9am'
        message_content = command_parts[4]  # The actual message content
        
        # Calculate the scheduled time (in reality, this would use a more sophisticated parser)
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        scheduled_date = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        formatted_time = scheduled_date.isoformat()
        
        logger.info(f"Parsed schedule time: {when} → {formatted_time}")
        logger.info(f"Parsed message content: '{message_content}'")
        
        logger.info("\n7. CREATING SCHEDULED MESSAGE RECORD")
        # Create schedule record
        schedule_data = {
            "id": "schedule-uuid-67890",
            "patient_id": existing_patient_id,
            "recipient_id": user_metadata["user_id"],
            "platform": "telegram",
            "message_content": message_content,
            "scheduled_time": formatted_time,
            "status": "pending",
            "created_at": now.isoformat()
        }
        
        logger.info(f"Created scheduled message record: {json.dumps(schedule_data, indent=2)}")
        
        logger.info("\n8. GENERATING RESPONSE")
        # Generate confirmation response
        scheduled_time_display = scheduled_date.strftime("%A, %B %d at %I:%M %p")
        response_message = f"I've scheduled your message for {scheduled_time_display}."
        logger.info(f"Response message: '{response_message}'")
        
        # Build result object
        result = {
            "messages": [{
                "type": "ai",
                "content": response_message
            }],
            "patient_id": existing_patient_id,
            "schedule_id": schedule_data["id"]
        }
    else:
        # If not a scheduling command (shouldn't happen in this test)
        result = {
            "messages": [{
                "type": "ai",
                "content": "I'm not sure if you're trying to schedule a message. Please use the format '/schedule [time] [message]'."
            }]
        }
    
    logger.info("=== TEST COMPLETE ===")
    return result

# Run the test
if __name__ == "__main__":
    print("\n")
    result = asyncio.run(test_telegram_message_scheduling())
    print("\nFinal result:", json.dumps(result, indent=2))
    print("\n") 