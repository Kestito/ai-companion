# Scheduled Messaging System: Schema Update Recommendations

## Current Schema Analysis

The existing `scheduled_messages` table has a well-designed structure that covers most of our needs:

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
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## Recommended Schema Updates

Based on our requirements analysis, we recommend the following additions to enhance delivery tracking, error handling, and performance:

```sql
-- Add new columns to scheduled_messages table
ALTER TABLE public.scheduled_messages
ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0,
ADD COLUMN last_attempt_time TIMESTAMP WITH TIME ZONE,
ADD COLUMN priority INTEGER NOT NULL DEFAULT 5,
ADD COLUMN metadata JSONB,
ADD COLUMN delivery_window_seconds INTEGER DEFAULT 60;

-- Add index for delivery attempts to help with retry logic
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_attempts ON public.scheduled_messages(attempts);

-- Add index for priority to support prioritized message delivery
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_priority ON public.scheduled_messages(priority, scheduled_time);

-- Add partial index for processing pending messages more efficiently
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_pending ON public.scheduled_messages(scheduled_time) 
WHERE status = 'pending';
```

## New Schema Fields Explained

### 1. `attempts` (INTEGER)
- **Purpose**: Track the number of delivery attempts made for each message
- **Default**: 0 (no attempts made yet)
- **Usage**: Used by retry logic to implement exponential backoff and maximum retry limits
- **Example**: After 3 failed attempts, apply longer delay before next retry

### 2. `last_attempt_time` (TIMESTAMPTZ)
- **Purpose**: Record when the last delivery attempt was made
- **Default**: NULL (no attempts made yet)
- **Usage**: Calculate appropriate backoff periods and detect stalled deliveries
- **Example**: If last attempt was 1 hour ago for a message that should retry every 5 minutes, it indicates a processing issue

### 3. `priority` (INTEGER)
- **Purpose**: Set message delivery priority (lower number = higher priority)
- **Default**: 5 (normal priority)
- **Usage**: Allow certain messages to be processed before others despite scheduled time
- **Example**: Urgent notifications might use priority 1, while marketing messages use priority 9

### 4. `metadata` (JSONB)
- **Purpose**: Store platform-specific configuration and tracking data
- **Default**: NULL (no metadata)
- **Usage**: Include additional data needed for specific platforms or message types
- **Example**: Store Telegram-specific formatting options or delivery settings

### 5. `delivery_window_seconds` (INTEGER)
- **Purpose**: Define how long after the scheduled time the message is still valid to send
- **Default**: 60 (one minute window)
- **Usage**: Prevent sending of time-sensitive messages that are too late
- **Example**: A reminder to take medication might be useless if delivered 2 hours late

## Additional Indexes Explained

### 1. `idx_scheduled_messages_attempts`
- **Purpose**: Optimize queries that filter by number of attempts
- **Usage**: Used when finding messages for retry or identifying problematic messages
- **Example**: Query to find all messages with > 3 failed attempts

### 2. `idx_scheduled_messages_priority`
- **Purpose**: Support priority-based querying of messages
- **Usage**: Used when fetching messages for processing in priority order
- **Example**: Query to get highest priority messages first

### 3. `idx_scheduled_messages_pending`
- **Purpose**: Partial index to optimize retrieval of only pending messages
- **Usage**: Used in the main message processor query that runs frequently
- **Example**: Significantly speeds up: `SELECT * FROM scheduled_messages WHERE status = 'pending' AND scheduled_time <= now()`

## Implementation Approach

We recommend implementing these schema changes as follows:

1. **Create migration script** that makes these changes with safe defaults
2. **Apply changes during off-peak hours** to minimize impact
3. **Update code to use new fields** in the processor and handler implementations
4. **Add backfill logic** for existing records if needed
5. **Monitor query performance** after changes to ensure indexes are effective

## Database Impact Analysis

- **Storage Impact**: Minimal (~20-30 bytes per row)
- **Query Performance**: Expected to improve due to specialized indexes
- **Write Performance**: No significant impact expected
- **Maintenance**: No special maintenance requirements

## Dependencies

- These schema changes must be coordinated with corresponding code changes
- The message processor must be updated to use the new fields
- Monitoring systems should be updated to track the new fields 