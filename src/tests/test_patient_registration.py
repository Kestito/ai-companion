"""Test script for patient registration functionality.

This script simulates a WhatsApp/Telegram message requesting patient registration,
and tests the router_node and patient_registration_node functionality.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from langchain_core.messages import HumanMessage

from ai_companion.graph.nodes import router_node, patient_registration_node
from ai_companion.graph.state import AICompanionState
from ai_companion.settings import settings
from ai_companion.utils.supabase import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_patient_registration")

print("Starting patient registration test script...")
logger.debug("Debug logging is enabled")

async def test_router_detection():
    """Test that router_node correctly detects patient registration requests."""
    logger.debug("Starting router detection test")
    test_cases = [
        "I want to register a new patient",
        "Please create a new patient for me",
        "add patient name: John Doe phone: +1234567890",
        "naujas pacientas vardas: Jonas Jonaitis",
    ]
    
    results = []
    for message in test_cases:
        logger.debug(f"Testing message: {message}")
        # Create a state with the test message
        state = AICompanionState(
            messages=[
                HumanMessage(
                    content=message,
                    metadata={"platform": "whatsapp", "user_id": "test_user_123"}
                )
            ]
        )
        
        # Process with router_node
        logger.debug("Calling router_node")
        result = await router_node(state)
        logger.debug(f"Router result: {result}")
        results.append((message, result.get("workflow", "unknown")))
    
    # Print results
    logger.info("Router detection test results:")
    for message, workflow in results:
        status = "✅" if workflow == "patient_registration_node" else "❌"
        logger.info(f"{status} Message: '{message[:30]}...' => Workflow: {workflow}")
    
    # Check if all cases were correctly detected
    success = all(workflow == "patient_registration_node" for _, workflow in results)
    if success:
        logger.info("Router detection test: All cases PASSED")
    else:
        logger.warning("Router detection test: Some cases FAILED")
    
    return success


async def test_patient_registration():
    """Test the patient_registration_node functionality."""
    logger.debug("Starting patient registration test")
    # Create a test message with patient information
    test_message = "Please register a new patient name: Test Patient phone: +1-555-123-4567"
    
    # Create a state with the test message
    state = AICompanionState(
        messages=[
            HumanMessage(
                content=test_message,
                metadata={"platform": "telegram", "user_id": "telegram_user_456"}
            )
        ]
    )
    
    # Process with patient_registration_node
    logger.debug("Calling patient_registration_node")
    try:
        result = await patient_registration_node(state, {})
        logger.debug(f"Patient registration result: {result}")
        
        # Log the result
        logger.info(f"Patient registration result: {result.get('registration_result', 'unknown')}")
        
        if result.get('registration_result') == 'success':
            patient_id = result.get('patient_id')
            patient_name = result.get('patient_name')
            logger.info(f"Successfully registered patient: {patient_name} with ID: {patient_id}")
            
            # Verify in database
            try:
                logger.debug("Getting Supabase client")
                supabase = get_supabase_client()
                logger.debug(f"Checking for patient with ID: {patient_id}")
                
                # Non-async version
                response = supabase.table("patients").select("*").eq("id", patient_id).execute()
                data = response.data
                
                if data and len(data) > 0:
                    logger.info(f"Patient verified in database: {data[0]}")
                    return True
                else:
                    logger.error(f"Patient not found in database: {patient_id}")
                    return False
            except Exception as e:
                logger.error(f"Error verifying patient in database: {e}", exc_info=True)
                return False
        else:
            logger.error(f"Patient registration failed: {result.get('error', 'unknown error')}")
            return False
    except Exception as e:
        logger.error(f"Error in patient_registration_node: {e}", exc_info=True)
        return False


async def test_telegram_patient_registration():
    """Test the patient_registration_node functionality with Telegram and no phone number."""
    logger.debug("Starting Telegram patient registration test")
    # Create a test message with patient information but no phone number
    test_message = "Please register a new patient name: Telegram User"
    
    # Create a state with the test message, including Telegram metadata
    telegram_user_id = "telegram_user_789"
    state = AICompanionState(
        messages=[
            HumanMessage(
                content=test_message,
                metadata={"platform": "telegram", "user_id": telegram_user_id}
            )
        ]
    )
    
    # Process with patient_registration_node
    logger.debug("Calling patient_registration_node for Telegram user")
    try:
        result = await patient_registration_node(state, {})
        logger.debug(f"Telegram patient registration result: {result}")
        
        # Log the result
        logger.info(f"Telegram patient registration result: {result.get('registration_result', 'unknown')}")
        
        if result.get('registration_result') == 'success':
            patient_id = result.get('patient_id')
            patient_name = result.get('patient_name')
            platform = result.get('platform')
            platform_user_id = result.get('platform_user_id')
            
            logger.info(f"Successfully registered Telegram patient: {patient_name} with ID: {patient_id}")
            logger.info(f"Platform: {platform}, Platform User ID: {platform_user_id}")
            
            # Verify in database
            try:
                logger.debug("Getting Supabase client")
                supabase = get_supabase_client()
                logger.debug(f"Checking for Telegram patient with ID: {patient_id}")
                
                # Non-async version
                response = supabase.table("patients").select("*").eq("id", patient_id).execute()
                data = response.data
                
                if data and len(data) > 0:
                    logger.info(f"Telegram patient verified in database: {data[0]}")
                    
                    # Verify Telegram ID was used as phone
                    patient_data = data[0]
                    phone = patient_data.get('phone')
                    
                    if phone and phone.startswith('telegram:'):
                        logger.info(f"✅ Telegram ID correctly stored as phone: {phone}")
                        return True
                    else:
                        logger.error(f"❌ Telegram ID not stored correctly in phone field: {phone}")
                        return False
                else:
                    logger.error(f"Telegram patient not found in database: {patient_id}")
                    return False
            except Exception as e:
                logger.error(f"Error verifying Telegram patient in database: {e}", exc_info=True)
                return False
        else:
            logger.error(f"Telegram patient registration failed: {result.get('error', 'unknown error')}")
            return False
    except Exception as e:
        logger.error(f"Error in Telegram patient_registration_node: {e}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    print("Starting patient registration tests...")
    logger.info("Starting patient registration tests...")
    
    try:
        # Test router detection
        logger.info("Starting router detection test...")
        router_success = await test_router_detection()
        
        # Test regular patient registration
        logger.info("Starting regular patient registration test...")
        registration_success = await test_patient_registration()
        
        # Test Telegram patient registration
        logger.info("Starting Telegram patient registration test...")
        telegram_registration_success = await test_telegram_patient_registration()
        
        # Print overall results
        if router_success and registration_success and telegram_registration_success:
            logger.info("All tests PASSED!")
        else:
            if not router_success:
                logger.error("Router detection test FAILED")
            if not registration_success:
                logger.error("Patient registration test FAILED")
            if not telegram_registration_success:
                logger.error("Telegram patient registration test FAILED")
            logger.error("Some tests FAILED!")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)


if __name__ == "__main__":
    print("Running main function...")
    asyncio.run(main())
    print("Test script complete.") 