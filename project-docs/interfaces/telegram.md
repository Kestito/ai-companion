# Telegram Interface Documentation

## Overview

The Telegram interface provides a communication channel between patients and the AI Companion system through the Telegram messaging platform. This interface supports patient registration, general conversations, and scheduling of reminders or appointments.

## Features

### 1. Patient Registration

When a user sends their first message to the Telegram bot, the system automatically:
- Extracts user information from Telegram metadata (user ID, username, first/last name)
- Creates a new patient record in the database
- Constructs a natural name from the user's first and last name
- Stores Telegram metadata as JSON in the patient record for platform-specific identification
- Responds to the user with a confirmation of registration

### 2. Existing Patient Handling

For returning users, the system:
- Identifies the user based on their Telegram user ID
- Retrieves their existing patient record from the database
- Updates their "last_contact" timestamp to track engagement
- Routes their message through the appropriate conversation workflow
- Provides personalized responses based on their inquiry

### 3. Message Scheduling

The system supports scheduling messages through a command-based interface:
- Users can send messages with the format: `/schedule [time] [message]`
- The system parses the scheduling command to extract time information and message content
- Creates a scheduled message record linked to the patient
- Confirms the scheduling with a formatted date/time display
- Delivers the message at the scheduled time

## Technical Implementation

### Message Handling Flow

1. **Message Reception**: Incoming Telegram messages are received through the Telegram API
2. **User Identification**: The system extracts user metadata from the message
3. **Patient Lookup**: The system checks if a patient record exists for the Telegram user ID
4. **Routing Logic**:
   - If no patient exists → Create new patient record (Patient Registration)
   - If patient exists and message is a command → Process command (e.g., Scheduling)
   - If patient exists and message is regular text → Process through conversation workflow

### Data Storage

- **Patient Record**: Contains both human-readable name and platform-specific details
- **Platform Metadata**: Stored as JSON in the email field, includes:
  - Platform identifier ("telegram")
  - Telegram user ID (for reliable identification)
  - Username (optional, for reference)
- **Phone Field**: Contains platform-prefixed identifier in format "telegram:{user_id}"

### Scheduled Messages

- **Format**: Structured data including patient ID, recipient ID, platform, content, and time
- **Status Tracking**: Messages marked as "pending" until delivered
- **Delivery**: Background process checks for and delivers pending scheduled messages

## Testing

Testing for the Telegram interface has been implemented as standalone simulation scripts that don't require connection to the actual Telegram API:

### Individual Test Files

1. **New Patient Test** (`test_patient_creation.py`): Tests the process of receiving a first message and creating a new patient record

2. **Existing Patient Test** (`test_existing_patient.py`): Tests handling of returning users and proper patient lookup

3. **Schedule Message Test** (`test_schedule_message.py`): Tests parsing of scheduling commands and creation of scheduled message records

### Complete Flow Test

The `test_full_user_flow.py` file provides an end-to-end test of the complete user journey:

1. **First Message**: User's initial contact triggering patient registration
2. **Second Message**: Normal conversation as a returning patient
3. **Third Message**: Scheduling command to set up a reminder

## Examples

### Example: New Patient Registration

```python
# Incoming first message from Telegram
telegram_message = {
    "message_id": 12345,
    "from": {
        "id": 42424242,
        "first_name": "Maria",
        "last_name": "Garcia",
        "username": "mariagarcia"
    },
    "text": "Hello, I'd like to get some information."
}

# Results in patient record
patient_data = {
    "name": "Maria Garcia",
    "phone": "telegram:42424242",
    "email": "{\"platform\": \"telegram\", \"user_id\": \"42424242\", \"username\": \"mariagarcia\"}",
    "status": "Active",
    "source": "telegram"
}
```

### Example: Scheduling Message

```python
# Incoming scheduling command
telegram_message = {
    "message_id": 12346,
    "from": {
        "id": 42424242
    },
    "text": "/schedule tomorrow at 10am Please schedule my appointment"
}

# Results in scheduled message record
schedule_data = {
    "patient_id": "patient-uuid-12345",
    "recipient_id": "42424242",
    "platform": "telegram",
    "message_content": "Please schedule my appointment",
    "scheduled_time": "2023-03-14T10:00:00",
    "status": "pending"
}
```

## Future Enhancements

1. **Interactive Buttons**: Implement Telegram's inline keyboard for easier interaction
2. **Multi-language Support**: Add language detection and translation capabilities
3. **Media Handling**: Support for processing images and documents sent by patients
4. **Integration with Appointment System**: Direct scheduling of appointments
5. **Secure Patient Verification**: Additional verification methods for sensitive operations 