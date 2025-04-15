# Telegram Message Scheduler

## Overview

The Telegram Message Scheduler enables healthcare providers to schedule one-time or recurring messages to be sent to patients via Telegram. This feature provides a way to send automated reminders, check-ins, and educational content on a regular basis, improving patient engagement and adherence to care plans.

## Features

- Schedule one-time messages to be sent at a specific date and time
- Set up recurring messages with various patterns:
  - Daily at a specific time
  - Weekly on selected days of the week
  - Monthly on a specific day of the month
- View and manage all scheduled messages
- Cancel pending scheduled messages
- Track delivery status of messages

## Technical Implementation

### Database Schema

The feature leverages the existing `scheduled_messages` table with the following key fields:

- `id`: Unique identifier for the schedule
- `patient_id`: ID of the recipient patient
- `scheduled_time`: When the message should be sent
- `message_content`: The content of the message
- `status`: Current status (pending, sent, failed, cancelled)
- `platform`: Set to 'telegram' for Telegram messages
- `recurrence`: JSON object containing recurrence pattern (if applicable)
- `created_at`: When the schedule was created

### Components

1. **Web UI Components**
   - `/telegram-messages` page for viewing and managing scheduled messages
   - Form for creating new scheduled messages with recurrence options
   - Table view of all scheduled messages with status indicators

2. **API Endpoints**
   - `GET /api/telegram-scheduler`: List scheduled messages
   - `POST /api/telegram-scheduler`: Create a new scheduled message
   - `PATCH /api/telegram-scheduler`: Update an existing schedule
   - `DELETE /api/telegram-scheduler`: Cancel a scheduled message

3. **Backend Processing**
   - `recurring_processor.py`: Handles calculation of next occurrence dates
   - `recurring_hook.py`: Processes messages after sending to schedule next occurrence

### Message Flow

1. User creates a scheduled message via the web UI
2. The scheduler service checks for messages due to be sent
3. When a message is due, it's sent via the Telegram handler
4. For recurring messages, after sending, the recurring hook calculates the next occurrence
5. A new scheduled message is created for the next occurrence

## Integration with Other Systems

- Leverages the existing Telegram bot infrastructure
- Uses the same scheduled messaging framework that can be extended to other platforms
- Connects to the patient database for recipient information

## Future Enhancements

- Message templates for common communication needs
- Bulk scheduling for multiple patients
- Advanced recurrence patterns (e.g., every other week)
- Message performance analytics
- WhatsApp integration using the same framework

## Usage Guidelines

1. Navigate to the Telegram Messages page from the sidebar
2. Click "Create New Schedule" to set up a new message
3. Enter the message content and select the date and time
4. For recurring messages, toggle the switch and select the recurrence pattern
5. Review scheduled messages in the "Scheduled Messages" tab
6. Cancel any pending messages if needed 