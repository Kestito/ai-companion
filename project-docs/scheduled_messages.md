# Scheduled Messages System

## Overview

The Scheduled Messages system allows the Telegram bot to send messages at specific times, either as one-time events or on recurring schedules. This feature enables automated reminders, notifications, daily updates, and more.

## Architecture

The scheduled message system consists of the following components:

1. **Database Table**: Uses the existing `scheduled_messages` table in Supabase to store message details and scheduling information.

2. **ScheduledMessageService**: Service class for managing CRUD operations on scheduled messages.

3. **SchedulerWorker**: Background process that checks for due messages and processes them.

4. **Telegram Bot Integration**: New commands and methods in the TelegramBot class for creating, listing, and cancelling scheduled messages.

## Scheduled Message Table Schema

The system uses the existing `scheduled_messages` table with the following structure:

- `id` (UUID): Primary key
- `patient_id` (UUID, nullable): Optional patient ID
- `scheduled_time` (timestamp with timezone): When the message should be sent
- `message_content` (text): The message to send
- `status` (text): Message status (pending, sent, failed, cancelled, rescheduled)
- `platform` (text): Platform identifier (e.g., "telegram")
- `created_at` (timestamp with timezone): When the scheduled message was created
- `attempts` (integer): Number of send attempts
- `last_attempt_time` (timestamp with timezone, nullable): When the last attempt was made
- `priority` (integer): Message priority (1-5, 1 is highest)
- `metadata` (jsonb, nullable): Additional message metadata including recurrence patterns
- `delivery_window_seconds` (integer, nullable): Allowed window for delivery after scheduled time

## Recurrence Patterns

The system supports the following recurrence patterns:

1. **Daily**: Messages sent at the same time every day
   ```json
   {
     "type": "daily",
     "interval": 1
   }
   ```

2. **Weekly**: Messages sent on specified days of the week
   ```json
   {
     "type": "weekly",
     "interval": 1,
     "days": [0, 2, 4]  // Monday, Wednesday, Friday (0-6, 0 is Monday)
   }
   ```

3. **Monthly**: Messages sent on a specific day each month
   ```json
   {
     "type": "monthly",
     "interval": 1,
     "day": 15  // 15th day of each month
   }
   ```

4. **Custom**: Messages sent at custom intervals in minutes
   ```json
   {
     "type": "custom",
     "minutes": 120  // Every 2 hours
   }
   ```

## Telegram Bot Commands

The Telegram bot provides the following commands for managing scheduled messages:

1. **`/schedule`**: Schedule a new message
   - One-time: `/schedule 2023-12-31T12:00:00 Happy New Year!`
   - Daily: `/schedule daily 09:00 Good morning!`
   - Weekly: `/schedule weekly mon,wed,fri 08:00 Weekly reminder`
   - Monthly: `/schedule monthly 1 10:00 Monthly report`
   - Custom: `/schedule every 30m Time for a break`

2. **`/scheduled`**: List all scheduled messages for the current chat

3. **`/cancel_schedule <message_id>`**: Cancel a scheduled message by ID

## Worker Process

The scheduler worker runs in the background as part of the Telegram bot process. It:

1. Periodically checks for due messages (every 30 seconds by default)
2. Processes messages in batches (10 messages per batch by default)
3. Calculates next execution time for recurring messages
4. Handles retries with exponential backoff for failed sends
5. Updates message status in the database

## Error Handling

The system includes robust error handling:

1. Exponential backoff for retries (5 minutes, 10 minutes, 20 minutes, etc.)
2. Maximum retry attempts (configurable, default 3)
3. Detailed error logging
4. Error information stored in message metadata

## Usage Examples

### Create a daily reminder
```
/schedule daily 08:00 Take your medication
```

### Create a weekly meeting reminder
```
/schedule weekly mon 09:45 Team meeting
```

### Create a monthly report reminder
```
/schedule monthly 1 10:00 Submit monthly report
```

### Create a reminder every 2 hours
```
/schedule every 2h Drink water
```

### View all scheduled messages
```
/scheduled
```

### Cancel a scheduled message
```
/cancel_schedule 123e4567-e89b-12d3-a456-426614174000
```

## Implementation Details

The scheduler is implemented using standard Python asyncio patterns:

1. Main scheduler loop runs as a background task
2. Messages are processed asynchronously to avoid blocking
3. The worker gracefully handles shutdown signals
4. Rate limiting considerations for Telegram API

## Future Enhancements

Potential future enhancements include:

1. More complex recurrence patterns (e.g., "every 2nd Tuesday")
2. Timezone support for scheduling based on user's timezone
3. Message templates and variables
4. Bulk operations for creating/cancelling multiple scheduled messages
5. Enhanced filtering and sorting for scheduled message listings 