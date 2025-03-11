# Scheduled Messaging Module

## Overview
The Scheduled Messaging module enables AI Companion to send messages to patients via Telegram and WhatsApp at specified times. This functionality is essential for medication reminders, appointment notifications, and periodic check-ins.

## Features

- **Message Scheduling**: Schedule one-time or recurring messages for delivery at specified times
- **Platform Support**: Compatible with both Telegram and WhatsApp
- **Recurrence Patterns**: Configure daily, weekly, or monthly recurring messages
- **Message Templates**: Use predefined templates for common messages with customizable parameters
- **Background Processing**: Autonomous message delivery through a dedicated processor
- **Database Integration**: Storage of scheduled messages in Supabase for durability and reporting

## Architecture

### Components

1. **Scheduler**: Core module for scheduling and managing messages
2. **Message Templates**: Predefined message templates with placeholder support
3. **Triggers**: Time and event-based trigger logic for scheduling
4. **Handlers**: Platform-specific handlers for message delivery (Telegram, WhatsApp)
5. **Background Processor**: Process that manages delivery of due messages
6. **Graph Integration**: Integration with the AI Companion conversation graph

### Database Schema

The module uses a `scheduled_messages` table in Supabase with the following structure:

```sql
CREATE TABLE public.scheduled_messages (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES public.patients(id),
    recipient_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('telegram', 'whatsapp')),
    message_content TEXT NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    template_key TEXT,
    parameters JSONB,
    recurrence_pattern JSONB,
    status TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## Usage

### Scheduling Commands

#### Telegram Commands

```
/schedule tomorrow 15:00 Take your medicine
/schedule monday 10:00 Doctor appointment
/schedule daily at 9:00 Morning checkup
```

#### WhatsApp Commands

```
schedule tomorrow 15:00 Take your medicine  
schedule monday 10:00 Doctor appointment
schedule daily at 9:00 Morning checkup
```

### Supported Time Formats

1. **Single Occurrences**:
   - `today 10:00` - Today at a specific time
   - `tomorrow 15:30` - Tomorrow at a specific time
   - `monday 09:00` - Next Monday at a specific time
   - `in 2 hours` - Relative time (hours)
   - `in 30 minutes` - Relative time (minutes)
   - `2023-04-15 14:00` - Specific date and time

2. **Recurring Patterns**:
   - `daily at 10:00` - Every day at a specific time
   - `weekly on monday at 09:00` - Every week on a specific day
   - `monthly on 15 at 14:00` - Every month on a specific day

### Message Templates

For common messaging needs, the module includes predefined templates:

- `medication_reminder`: Reminder to take medication
- `appointment_reminder`: Reminder for upcoming appointments
- `check_in`: General wellness check-in
- `follow_up`: Follow-up after a visit or treatment

Templates support parameters for personalization, like `{name}`, `{medication}`, etc.

## Background Processor

A dedicated background process handles the sending of scheduled messages:

- Runs as a separate process to ensure reliable delivery
- Checks for due messages every minute
- Handles message sending and status updates
- Supports error handling and retry logic
- Creates next occurrences for recurring messages

## Implementation Notes

- The module integrates with the AI Companion graph via the `schedule_message_node`
- Messages are tied to registered patients to maintain continuity of care
- Platform-specific handlers ensure messages are formatted correctly for each platform
- The system respects rate limits for external APIs

## Security Considerations

- Row-level security ensures patients can only view their own scheduled messages
- The API tokens for messaging platforms are stored securely in environment variables
- Only authenticated users can create and manage scheduled messages

## Deployment and Monitoring

- The background processor can be run as a separate service or within the main application
- Logging of all message processing activities helps with troubleshooting
- Scheduled message status tracking enables monitoring and reporting
- Database indexes support efficient querying of scheduled messages

## Future Enhancements

- Support for more messaging platforms (e.g., SMS, email)
- Advanced recurrence patterns (e.g., every 2 days, specific weekdays)
- More sophisticated template system with conditional logic
- User interface for healthcare providers to manage scheduled messages
- Analytics to track patient engagement with scheduled messages 