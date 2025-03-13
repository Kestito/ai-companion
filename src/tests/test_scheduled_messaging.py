#!/usr/bin/env python
"""
Test script for scheduled messaging functionality.

This script tests the scheduled messaging functionality end-to-end, including
command parsing, database storage, and message delivery.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
import uuid
from typing import Dict, Any, List
import re

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_scheduled_messaging")

# Add the src directory to the Python path if needed
if os.path.abspath(os.path.dirname(__file__)) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from langchain_core.messages import HumanMessage
from ai_companion.graph.state import AICompanionState
from ai_companion.graph.nodes import router_node, schedule_message_node
from ai_companion.modules.scheduled_messaging.scheduler import ScheduleManager
from ai_companion.modules.scheduled_messaging.handlers.telegram_handler import TelegramHandler
from ai_companion.modules.scheduled_messaging.handlers.whatsapp_handler import WhatsAppHandler
from ai_companion.modules.scheduled_messaging.storage import (
    create_scheduled_messages_table,
    get_pending_messages,
    get_patient_scheduled_messages,
    get_scheduled_message,
    update_message_status
)
from ai_companion.utils.supabase import get_supabase_client

# Test patient ID - replace with an actual ID from your database
TEST_PATIENT_ID = "bf0b9e03-2177-4f05-9979-124419bd39a2"  # Replace with an actual patient ID

async def test_router_detection():
    """Test router detection of schedule commands."""
    logger.info("Testing router detection of schedule commands")
    
    test_cases = [
        "/schedule tomorrow 15:00 Take your medicine",
        "/schedule monday 10:00 Doctor appointment",
        "/schedule daily at 9:00 Morning checkup",
        "schedule tomorrow 15:00 Take your medicine",
        "schedule weekly on monday at 9:00 Weekly checkup"
    ]
    
    results = []
    for message in test_cases:
        logger.debug(f"Testing message: {message}")
        state = AICompanionState(
            messages=[
                HumanMessage(
                    content=message,
                    metadata={"platform": "telegram" if message.startswith('/') else "whatsapp", "user_id": "test_user_123"}
                )
            ]
        )
        
        result = await router_node(state)
        results.append((message, result.get("workflow", "unknown")))
    
    # Print results
    logger.info("Router detection test results:")
    for message, workflow in results:
        status = "✅" if workflow == "schedule_message_node" else "❌"
        logger.info(f"{status} Message: '{message[:30]}...' => Workflow: {workflow}")
    
    # Check if all cases were correctly detected
    success = all(workflow == "schedule_message_node" for _, workflow in results)
    if success:
        logger.info("Router detection test: All cases PASSED")
    else:
        logger.warning("Router detection test: Some cases FAILED")
    
    return success

async def test_command_parsing():
    """Test parsing of schedule commands."""
    logger.info("Testing command parsing")
    
    # Test Telegram command parsing
    telegram_handler = TelegramHandler()
    telegram_commands = [
        ("/schedule tomorrow 15:00 Take your medicine", "single"),
        ("/schedule monday 10:00 Doctor appointment", "single"),
        ("/schedule daily at 9:00 Morning checkup", "recurring"),
        ("/schedule weekly on monday at 9:00 Weekly checkup", "recurring"),
        ("/schedule monthly on 15 at 14:00 Monthly checkup", "recurring"),
        ("/schedule in 2 hours Quick reminder", "single"),
        ("/schedule invalid format", None)  # Should fail
    ]
    
    telegram_results = []
    for command, expected_type in telegram_commands:
        logger.info(f"Testing Telegram command: {command}")
        result = await telegram_handler.parse_command(command)
        logger.info(f"Result: {result}")
        success = result and result.get("success", False) and (result.get("type") == expected_type if expected_type else True)
        telegram_results.append((command, success))
        
        # Add detailed debugging for recurring commands
        if "recurring" in str(expected_type):
            logger.info(f"Debugging recurring command: {command}")
            content = command[9:].strip()  # Remove "/schedule "
            recurring_pattern = r'^(daily|weekly on \w+|monthly on \d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(.+)$'
            recurring_match = re.match(recurring_pattern, content, re.IGNORECASE)
            logger.info(f"Recurring pattern match: {recurring_match is not None}")
            
            if recurring_match:
                recurrence_spec = recurring_match.group(1)
                time_spec = recurring_match.group(2)
                message = recurring_match.group(3).strip()
                logger.info(f"Extracted - Recurrence: '{recurrence_spec}', Time: '{time_spec}', Message: '{message}'")
                
                from ai_companion.modules.scheduled_messaging.triggers import parse_recurrence
                recurrence_str = f"{recurrence_spec} at {time_spec}"
                logger.info(f"Testing parse_recurrence with: '{recurrence_str}'")
                recurrence = parse_recurrence(recurrence_str)
                logger.info(f"Parse recurrence result: {recurrence}")
    
    # Test WhatsApp command parsing
    whatsapp_handler = WhatsAppHandler()
    whatsapp_commands = [
        ("schedule tomorrow 15:00 Take your medicine", "single"),
        ("schedule monday 10:00 Doctor appointment", "single"),
        ("schedule daily at 9:00 Morning checkup", "recurring"),
        ("schedule weekly on monday at 9:00 Weekly checkup", "recurring"),
        ("schedule monthly on 15 at 14:00 Monthly checkup", "recurring"),
        ("schedule in 2 hours Quick reminder", "single"),
        ("schedule invalid format", None)  # Should fail
    ]
    
    # Test each recurring pattern separately
    logger.info("Testing recurring patterns specifically:")
    
    # Define patterns from both handler files
    telegram_recurring_pattern = r'^(daily|weekly on \w+|monthly on \d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(.+)$'
    triggers_daily_pattern = r'^daily\s+at\s+(\d{1,2}):(\d{2})$'
    triggers_weekly_pattern = r'^weekly\s+on\s+(\w+)\s+at\s+(\d{1,2}):(\d{2})$'
    triggers_monthly_pattern = r'^monthly\s+on\s+(\d{1,2})\s+at\s+(\d{1,2}):(\d{2})$'
    
    # Log each pattern for clarity
    logger.info(f"Handler recurring pattern: {telegram_recurring_pattern}")
    logger.info(f"Triggers daily pattern: {triggers_daily_pattern}")
    logger.info(f"Triggers weekly pattern: {triggers_weekly_pattern}")
    logger.info(f"Triggers monthly pattern: {triggers_monthly_pattern}")
    
    # Test daily pattern
    daily_cmd = "schedule daily at 9:00 Morning checkup"
    daily_cmd_no_prefix = "daily at 9:00"
    logger.info(f"Testing daily pattern: '{daily_cmd}'")
    
    # Test with handler pattern
    handler_match = re.match(telegram_recurring_pattern, daily_cmd[9:], re.IGNORECASE)  # Remove 'schedule ' prefix
    logger.info(f"Handler pattern match for daily: {handler_match is not None}")
    if handler_match:
        recurrence_spec = handler_match.group(1)
        time_spec = handler_match.group(2)
        logger.info(f"Daily - Handler extracted - Recurrence spec: '{recurrence_spec}', Time spec: '{time_spec}'")
        
        # Test direct recurrence pattern match
        recurrence_str = f"{recurrence_spec} at {time_spec}"
        logger.info(f"Daily - Testing parse_recurrence with: '{recurrence_str}'")
        from ai_companion.modules.scheduled_messaging.triggers import parse_recurrence
        recurrence = parse_recurrence(recurrence_str)
        logger.info(f"Daily - Direct parse_recurrence result: {recurrence}")
        
        # Test matches with exact pattern
        direct_match = re.match(triggers_daily_pattern, recurrence_str, re.IGNORECASE)
        logger.info(f"Daily - Direct triggers pattern match: {direct_match is not None}")
        if direct_match:
            logger.info(f"Daily - Matched groups: {direct_match.groups()}")
    
    # Test weekly pattern
    weekly_cmd = "schedule weekly on monday at 9:00 Weekly checkup"
    weekly_cmd_no_prefix = "weekly on monday at 9:00"
    logger.info(f"Testing weekly pattern: '{weekly_cmd}'")
    
    # Test with handler pattern
    handler_match = re.match(telegram_recurring_pattern, weekly_cmd[9:], re.IGNORECASE)  # Remove 'schedule ' prefix
    logger.info(f"Handler pattern match for weekly: {handler_match is not None}")
    if handler_match:
        recurrence_spec = handler_match.group(1)
        time_spec = handler_match.group(2)
        logger.info(f"Weekly - Handler extracted - Recurrence spec: '{recurrence_spec}', Time spec: '{time_spec}'")
        
        # Test direct recurrence pattern match
        recurrence_str = f"{recurrence_spec} at {time_spec}"
        logger.info(f"Weekly - Testing parse_recurrence with: '{recurrence_str}'")
        recurrence = parse_recurrence(recurrence_str)
        logger.info(f"Weekly - Direct parse_recurrence result: {recurrence}")
        
        # Test matches with exact pattern
        direct_match = re.match(triggers_weekly_pattern, recurrence_str, re.IGNORECASE)
        logger.info(f"Weekly - Direct triggers pattern match: {direct_match is not None}")
        if direct_match:
            logger.info(f"Weekly - Matched groups: {direct_match.groups()}")
    
    # Test monthly pattern
    monthly_cmd = "schedule monthly on 15 at 14:00 Monthly checkup"
    monthly_cmd_no_prefix = "monthly on 15 at 14:00"
    logger.info(f"Testing monthly pattern: '{monthly_cmd}'")
    
    # Test with handler pattern
    handler_match = re.match(telegram_recurring_pattern, monthly_cmd[9:], re.IGNORECASE)  # Remove 'schedule ' prefix
    logger.info(f"Handler pattern match for monthly: {handler_match is not None}")
    if handler_match:
        recurrence_spec = handler_match.group(1)
        time_spec = handler_match.group(2)
        logger.info(f"Monthly - Handler extracted - Recurrence spec: '{recurrence_spec}', Time spec: '{time_spec}'")
        
        # Test direct recurrence pattern match
        recurrence_str = f"{recurrence_spec} at {time_spec}"
        logger.info(f"Monthly - Testing parse_recurrence with: '{recurrence_str}'")
        recurrence = parse_recurrence(recurrence_str)
        logger.info(f"Monthly - Direct parse_recurrence result: {recurrence}")
        
        # Test matches with exact pattern
        direct_match = re.match(triggers_monthly_pattern, recurrence_str, re.IGNORECASE)
        logger.info(f"Monthly - Direct triggers pattern match: {direct_match is not None}")
        if direct_match:
            logger.info(f"Monthly - Matched groups: {direct_match.groups()}")
    
    # Direct test of parse_recurrence function with exact recurrence strings
    logger.info("Direct testing of parse_recurrence function:")
    test_recurrence_strings = [
        "daily at 9:00",
        "weekly on monday at 9:00",
        "monthly on 15 at 14:00"
    ]
    
    for recurrence_str in test_recurrence_strings:
        logger.info(f"Testing parse_recurrence with exact string: '{recurrence_str}'")
        result = parse_recurrence(recurrence_str)
        logger.info(f"Result: {result}")
        
        # Test with direct regex matching
        daily_pattern = r'^daily\s+at\s+(\d{1,2}):(\d{2})$'
        weekly_pattern = r'^weekly\s+on\s+(\w+)\s+at\s+(\d{1,2}):(\d{2})$'
        monthly_pattern = r'^monthly\s+on\s+(\d{1,2})\s+at\s+(\d{1,2}):(\d{2})$'
        
        daily_match = re.match(daily_pattern, recurrence_str)
        weekly_match = re.match(weekly_pattern, recurrence_str)
        monthly_match = re.match(monthly_pattern, recurrence_str)
        
        logger.info(f"Direct regex match results for '{recurrence_str}':")
        logger.info(f"  Daily match: {daily_match is not None}")
        logger.info(f"  Weekly match: {weekly_match is not None}")
        logger.info(f"  Monthly match: {monthly_match is not None}")
    
    whatsapp_results = []
    for command, expected_type in whatsapp_commands:
        logger.debug(f"Testing WhatsApp command: {command}")
        result = await whatsapp_handler.parse_command(command)
        success = result and result.get("success", False) and (result.get("type") == expected_type if expected_type else True)
        whatsapp_results.append((command, success))
        # Add detailed logging for failures
        if not success:
            logger.error(f"WhatsApp command failed: '{command}'")
            logger.error(f"Result: {result}")
            if result and "error" in result:
                logger.error(f"Error message: {result['error']}")
            # Check if it's a recurring command
            if "recurring" in command:
                match = re.match(r'^schedule\s+(daily|weekly\s+on\s+\w+|monthly\s+on\s+\d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(.+)$', command, re.IGNORECASE)
                if match:
                    recurrence_spec = match.group(1)
                    time_spec = match.group(2)
                    logger.error(f"Recurrence spec: '{recurrence_spec}', Time spec: '{time_spec}'")
                    from ai_companion.modules.scheduled_messaging.triggers import parse_recurrence
                    recurrence = parse_recurrence(f"{recurrence_spec} at {time_spec}")
                    logger.error(f"Direct parse_recurrence result: {recurrence}")
    
    # Print results
    logger.info("Telegram command parsing results:")
    for command, success in telegram_results:
        status = "✅" if success else "❌"
        logger.info(f"{status} Command: '{command}'")
        # Add detailed logging for failures
        if not success:
            logger.error(f"Telegram command failed: '{command}'")
            if command.startswith("/schedule"):
                result = await telegram_handler.parse_command(command)
                logger.error(f"Result: {result}")
                if result and "error" in result:
                    logger.error(f"Error message: {result['error']}")
                # Check if it's a recurring command
                if "recurring" in command or any(pattern in command for pattern in ["daily", "weekly", "monthly"]):
                    match = re.match(r'^/schedule\s+(daily|weekly\s+on\s+\w+|monthly\s+on\s+\d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(.+)$', command, re.IGNORECASE)
                    if match:
                        recurrence_spec = match.group(1)
                        time_spec = match.group(2)
                        logger.error(f"Recurrence spec: '{recurrence_spec}', Time spec: '{time_spec}'")
                        from ai_companion.modules.scheduled_messaging.triggers import parse_recurrence
                        recurrence = parse_recurrence(f"{recurrence_spec} at {time_spec}")
                        logger.error(f"Direct parse_recurrence result: {recurrence}")
    
    logger.info("WhatsApp command parsing results:")
    for command, success in whatsapp_results:
        status = "✅" if success else "❌"
        logger.info(f"{status} Command: '{command}'")
    
    # Check overall success
    telegram_success = all(success for _, success in telegram_results[:-1])  # Excluding the last one which is expected to fail
    whatsapp_success = all(success for _, success in whatsapp_results[:-1])  # Excluding the last one which is expected to fail
    
    if telegram_success and whatsapp_success:
        logger.info("Command parsing test: All valid cases PASSED")
        return True
    else:
        logger.warning("Command parsing test: Some valid cases FAILED")
        return False

async def test_schedule_creation():
    """Test creating a schedule through the scheduler."""
    logger.info("Testing schedule creation")
    
    # Ensure the scheduled_messages table exists
    await create_scheduled_messages_table()
    
    # Test scheduling a message
    scheduler = ScheduleManager()
    scheduled_time = (datetime.now() + timedelta(minutes=30)).isoformat()
    
    try:
        # Try to create a schedule
        result = await scheduler.schedule_message(
            patient_id=TEST_PATIENT_ID,
            recipient_id="test_user_456",
            platform="telegram",
            message_content="This is a test scheduled message",
            scheduled_time=scheduled_time
        )
        
        logger.info(f"Schedule creation result: {result}")
        
        if result.get("status") == "scheduled":
            logger.info("Schedule creation test: PASSED")
            
            # Verify in database
            schedule_id = result.get("schedule_id")
            schedule_data = await get_scheduled_message(schedule_id)
            
            if schedule_data:
                logger.info(f"Verified schedule in database: {schedule_data}")
                return True, schedule_id
            else:
                logger.error("Failed to verify schedule in database")
                return False, None
        else:
            logger.error(f"Failed to create schedule: {result}")
            return False, None
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        return False, None

async def test_message_node():
    """Test the schedule_message_node for handling schedule requests."""
    logger.info("Testing schedule_message_node")
    
    # Create a mock conversation state
    state = AICompanionState(
        messages=[
            HumanMessage(
                content="/schedule tomorrow 15:00 Take your medicine",
                metadata={"platform": "telegram", "user_id": "test_user_789"}
            )
        ],
        conversation_memory={
            "metadata": {
                "patient_id": TEST_PATIENT_ID
            }
        }
    )
    
    try:
        # Process with schedule_message_node
        result = await schedule_message_node(state, {})
        logger.info(f"Schedule message node result: {result}")
        
        if result.get("schedule_result") == "success":
            logger.info(f"Successfully scheduled message with ID: {result.get('schedule_id')}")
            logger.info("Schedule message node test: PASSED")
            return True
        else:
            logger.error(f"Failed to schedule message: {result.get('error')}")
            logger.info("Schedule message node test: FAILED")
            return False
    except Exception as e:
        logger.error(f"Error in schedule_message_node: {e}")
        logger.info("Schedule message node test: FAILED")
        return False

async def test_pending_messages():
    """Test fetching pending messages."""
    logger.info("Testing pending messages retrieval")
    
    # Create a test message scheduled for now
    scheduler = ScheduleManager()
    scheduled_time = datetime.now().isoformat()
    
    try:
        # Create a test message scheduled for now
        result = await scheduler.schedule_message(
            patient_id=TEST_PATIENT_ID,
            recipient_id="test_user_pending",
            platform="telegram",
            message_content="This is a test pending message",
            scheduled_time=scheduled_time
        )
        
        if result.get("status") != "scheduled":
            logger.error("Failed to create test pending message")
            return False
        
        schedule_id = result.get("schedule_id")
        logger.info(f"Created test pending message with ID: {schedule_id}")
        
        # Fetch pending messages
        pending_messages = await get_pending_messages()
        logger.info(f"Found {len(pending_messages)} pending messages")
        
        # Check if our test message is in the pending messages
        test_message_found = any(message.get("id") == schedule_id for message in pending_messages)
        
        if test_message_found:
            logger.info("Found test message in pending messages: PASSED")
            
            # Update message status to sent
            update_success = await update_message_status(schedule_id, "sent")
            
            if update_success:
                logger.info("Successfully updated message status to sent")
                return True
            else:
                logger.error("Failed to update message status")
                return False
        else:
            logger.error("Test message not found in pending messages")
            return False
    except Exception as e:
        logger.error(f"Error testing pending messages: {e}")
        return False

async def test_patient_messages():
    """Test retrieving messages for a specific patient."""
    logger.info("Testing patient messages retrieval")
    
    try:
        # Get all scheduled messages for the test patient
        patient_messages = await get_patient_scheduled_messages(TEST_PATIENT_ID)
        
        logger.info(f"Found {len(patient_messages)} messages for patient {TEST_PATIENT_ID}")
        
        if len(patient_messages) > 0:
            logger.info("Sample patient message:")
            logger.info(patient_messages[0])
            logger.info("Patient messages retrieval test: PASSED")
            return True
        else:
            logger.warning("No messages found for test patient")
            return False
    except Exception as e:
        logger.error(f"Error retrieving patient messages: {e}")
        return False

async def main():
    """Run all the tests."""
    print("Starting scheduled messaging tests...")
    
    try:
        # Test router detection
        router_success = await test_router_detection()
        
        # Test command parsing
        parsing_success = await test_command_parsing()
        
        # Test schedule creation
        schedule_success, schedule_id = await test_schedule_creation()
        
        # Test message node
        node_success = await test_message_node()
        
        # Test pending messages retrieval
        pending_success = await test_pending_messages()
        
        # Test patient messages retrieval
        patient_success = await test_patient_messages()
        
        # Print overall results
        print("\n=== TEST RESULTS ===")
        print(f"Router Detection:    {'✅ PASSED' if router_success else '❌ FAILED'}")
        print(f"Command Parsing:     {'✅ PASSED' if parsing_success else '❌ FAILED'}")
        print(f"Schedule Creation:   {'✅ PASSED' if schedule_success else '❌ FAILED'}")
        print(f"Schedule Message Node: {'✅ PASSED' if node_success else '❌ FAILED'}")
        print(f"Pending Messages:    {'✅ PASSED' if pending_success else '❌ FAILED'}")
        print(f"Patient Messages:    {'✅ PASSED' if patient_success else '❌ FAILED'}")
        
        overall = all([router_success, parsing_success, schedule_success, node_success, pending_success, patient_success])
        print(f"\nOVERALL:            {'✅ PASSED' if overall else '❌ FAILED'}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"\nTests FAILED with error: {e}")
        return 1
    
    return 0 if overall else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 