# Telegram Interface Test Guide

## Overview

This guide covers the various tests created for the Telegram interface in the AI Companion application. These tests simulate the interaction between a Telegram user and the system without requiring an actual connection to the Telegram API, allowing for isolated and reproducible testing of each component.

## Available Tests

The following standalone test scripts are available:

1. **New Patient Registration Test** - `test_patient_creation.py`
2. **Existing Patient Handling Test** - `test_existing_patient.py`
3. **Schedule Message Test** - `test_schedule_message.py`
4. **Complete User Flow Test** - `test_full_user_flow.py`

## Test Locations

All test files are located in:
```
src/ai_companion/interfaces/telegram/
```

## How to Run Tests

Each test can be run individually using Python:

```bash
# Navigate to the telegram interface directory
cd src/ai_companion/interfaces/telegram/

# Run individual tests
python test_patient_creation.py
python test_existing_patient.py
python test_schedule_message.py
python test_full_user_flow.py
```

## Test Descriptions

### 1. New Patient Registration Test (`test_patient_creation.py`)

**Purpose:** Validates that the system correctly handles a first-time user's message by creating a new patient record.

**What it tests:**
- Extraction of user metadata from Telegram message
- Creation of a patient record with proper name construction
- Storage of Telegram metadata in the patient record
- Generation of an appropriate welcome response

**Expected Output:**
- Logs showing the new patient creation process
- JSON output with the patient ID and response message

### 2. Existing Patient Handling Test (`test_existing_patient.py`)

**Purpose:** Validates that the system correctly identifies returning users and retrieves their patient record.

**What it tests:**
- Extraction of user metadata from Telegram message
- Lookup of existing patient record by Telegram user ID
- Update of "last_contact" time
- Routing to the conversation workflow
- Generation of a contextual response

**Expected Output:**
- Logs showing the patient lookup process
- JSON output with the patient ID and response message

### 3. Schedule Message Test (`test_schedule_message.py`)

**Purpose:** Validates that the system correctly parses and processes scheduling commands.

**What it tests:**
- Detection of the "/schedule" command prefix
- Parsing of time expressions in natural language
- Extraction of the message content
- Creation of a scheduled message record
- Generation of a confirmation response with formatted date/time

**Expected Output:**
- Logs showing the scheduling command parsing
- JSON output with the schedule ID and confirmation message

### 4. Complete User Flow Test (`test_full_user_flow.py`)

**Purpose:** Validates the entire user journey from first contact to scheduling in a single test.

**What it tests:**
- First message → New patient registration
- Second message → Normal conversation as existing patient
- Third message → Command parsing and scheduling
- End-to-end flow through different system components

**Expected Output:**
- Detailed logs for each step of the process
- JSON output with comprehensive interaction history

## Test Data

All tests use similar test data to simulate a consistent user:

- **User ID:** 42424242
- **Username:** mariagarcia
- **Name:** Maria Garcia
- **Language:** English

## Test Mocking

These tests use simulated data and function calls rather than actual API interactions:

- **Database Operations:** Simulated with print statements and dummy IDs
- **Telegram API:** Replaced with constructed message objects
- **Scheduling Logic:** Uses simplified time parsing for demonstration

## Adding New Tests

When adding new tests to the Telegram interface, follow these guidelines:

1. Create a standalone Python file in the `src/ai_companion/interfaces/telegram/` directory
2. Follow the naming convention `test_[feature].py`
3. Use the `asyncio` library for asynchronous testing
4. Implement detailed logging for each step of the process
5. Return a structured result dictionary for easy validation

## Troubleshooting

If tests are failing, check the following:

1. **Import Errors:** Ensure all required modules are installed
2. **Syntax Errors:** Verify the code is valid Python 3.9+
3. **Log Output:** Review the detailed logs for specific failure points
4. **Data Structure:** Confirm that the simulated message structure matches what the system expects

## Integration with CI/CD

Future improvement: These tests should be incorporated into the CI/CD pipeline to ensure that changes to the Telegram interface don't break existing functionality. 