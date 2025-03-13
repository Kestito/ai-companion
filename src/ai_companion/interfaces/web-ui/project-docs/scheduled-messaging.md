# Scheduled Messaging

## Overview

The scheduled messaging feature allows users to schedule messages to be sent at specific times through various platforms (WhatsApp, Telegram). This document outlines the implementation details, API endpoints, and usage examples.

## Architecture

The scheduled messaging system follows a decoupled architecture:

1. **Web UI**: Creates records in the Supabase `scheduled_messages` table
2. **Backend Processor**: Polls the table for pending messages and sends them at the scheduled time
3. **Platform Handlers**: Handle the actual message delivery to different platforms

This decoupled approach ensures that the UI doesn't need to know about the backend implementation details, and the backend can evolve independently.

## Database Schema

The `scheduled_messages` table has the following structure:

```sql
CREATE TABLE IF NOT EXISTS public.scheduled_messages (
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
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## API Endpoints

### Create Scheduled Message

```
POST /api/scheduled-messages
```

**Request Body:**
```json
{
  "recipientId": "+37061234567",
  "platform": "whatsapp",
  "message": "Reminder: Take your medication",
  "scheduledTime": "2023-08-15T09:00:00Z",
  "recurrence": "daily"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "recipient_id": "+37061234567",
  "platform": "whatsapp",
  "message_content": "Reminder: Take your medication",
  "scheduled_time": "2023-08-15T09:00:00Z",
  "recurrence_pattern": "daily",
  "status": "pending",
  "created_at": "2023-08-14T12:00:00Z"
}
```

### Get Scheduled Messages

```
GET /api/scheduled-messages
```

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "recipient_id": "+37061234567",
    "platform": "whatsapp",
    "message_content": "Reminder: Take your medication",
    "scheduled_time": "2023-08-15T09:00:00Z",
    "recurrence_pattern": "daily",
    "status": "pending",
    "created_at": "2023-08-14T12:00:00Z"
  }
]
```

### Cancel Scheduled Message

```
DELETE /api/scheduled-messages/{id}
```

**Response:**
```json
{
  "success": true
}
```

## UI Components

### ScheduleForm

A form component for creating new scheduled messages.

**Props:**
- `open`: boolean - Controls the visibility of the form
- `onClose`: () => void - Callback when the form is closed
- `onSubmit`: (data: ScheduleRequest) => void - Callback when the form is submitted

**Usage:**
```tsx
<ScheduleForm
  open={showForm}
  onClose={() => setShowForm(false)}
  onSubmit={handleSubmit}
/>
```

## Service Layer

The `scheduleService` provides methods for interacting with the scheduled messaging API:

```typescript
// Create a new scheduled message
const message = await scheduleService.createScheduledMessage({
  recipientId: '+37061234567',
  platform: 'whatsapp',
  message: 'Reminder: Take your medication',
  scheduledTime: new Date('2023-08-15T09:00:00Z'),
  recurrence: 'daily'
});

// Get all scheduled messages
const messages = await scheduleService.getScheduledMessages();

// Cancel a scheduled message
await scheduleService.cancelScheduledMessage('123e4567-e89b-12d3-a456-426614174000');
```

## Backend Processing

The backend processor runs as a separate service that:

1. Polls the `scheduled_messages` table for pending messages that are due
2. Sends the messages using the appropriate platform handler
3. Updates the message status to 'sent' or 'failed'
4. Creates the next occurrence for recurring messages

This process runs independently of the UI, allowing for reliable message delivery even if the UI is not active.

## Testing

To test the scheduled messaging feature:

1. Create a scheduled message for a time in the near future
2. Verify that the message appears in the scheduled messages list
3. Wait for the scheduled time to pass
4. Verify that the message status changes to 'sent'
5. Check that the message was received on the target platform

## Future Enhancements

- Support for more messaging platforms
- Message templates with variable substitution
- Bulk scheduling of messages
- Advanced recurrence patterns (e.g., "every Monday and Wednesday")
- Message delivery confirmation and read receipts

## Scheduled Health Checks

The system supports scheduling regular health checks for patients. These checks can be configured to run at different frequencies (daily, weekly, monthly) and can be delivered through different messaging platforms (WhatsApp, Telegram, SMS, Email).

### Scheduled Checks Data Model

Scheduled checks are stored in the `scheduled_checks` table in the Supabase database:

```sql
CREATE TABLE IF NOT EXISTS public.scheduled_checks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  description TEXT,
  frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly', 'once')),
  next_scheduled TIMESTAMP WITH TIME ZONE NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled', 'failed')),
  platform TEXT NOT NULL CHECK (platform IN ('whatsapp', 'telegram', 'sms', 'email')),
  patient_id UUID NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Scheduled Checks UI

The scheduled checks are displayed in the patient details page under the "Scheduled Checks" tab. The UI shows:

1. The title and description of the check
2. The frequency (daily, weekly, monthly)
3. The platform used for delivery (WhatsApp, Telegram, etc.)
4. The status of the check (pending, completed, cancelled, failed)
5. The next scheduled date for the check

### Adding New Scheduled Checks

New scheduled checks can be added through the "Add Check" button in the Scheduled Checks tab. This will open a form where the user can configure:

1. Title and description of the check
2. Frequency (daily, weekly, monthly, once)
3. Platform for delivery (WhatsApp, Telegram, SMS, Email)
4. Initial scheduled date and time

### Implementation Details

The scheduled checks feature is implemented using:

1. A Supabase database table for storing the scheduled checks
2. A React component for displaying the scheduled checks in the UI
3. API endpoints for creating, updating, and deleting scheduled checks
4. A background job that runs periodically to check for scheduled checks that need to be executed 