# Scheduled Messaging System

## Overview
The Scheduled Messaging System is a robust platform for scheduling, managing, and delivering messages across various communication channels, beginning with Telegram and WhatsApp. This functionality is essential for medication reminders, appointment notifications, and periodic check-ins with patients.

The system is designed to handle both one-time and recurring messages, with advanced features for error handling, status tracking, and performance monitoring. The architecture leverages asynchronous processing, parallel execution via worker pools, and intelligent error categorization to ensure reliable message delivery even in challenging network conditions.

## Project Scope

The Scheduled Messaging System encompasses:

1. **Message Scheduling**: Ability to schedule messages for future delivery, either one-time or recurring
2. **Platform Support**: Initially Telegram, with architecture supporting expansion to WhatsApp and SMS
3. **Delivery Tracking**: Comprehensive tracking of message delivery attempts and outcomes
4. **Error Handling**: Robust error handling with retry mechanisms and circuit breakers
5. **Performance Monitoring**: Metrics collection and alerting for system health and performance

## Requirements

### Functional Requirements

#### Message Scheduling
- The system MUST support scheduling messages for future delivery
- The system MUST support one-time scheduled messages
- The system MUST support recurring messages (daily, weekly, monthly)
- The system MUST allow specifying the delivery time with minute precision
- The system MUST support custom recurrence patterns (e.g., specific days of week)

#### Message Content
- The system MUST support plain text messages
- The system MUST support HTML-formatted messages for Telegram
- The system SHOULD support message templates with variable substitution
- The system SHOULD support internationalization for messages
- The system MUST enforce platform-specific message size limits

#### Platform Support
- The system MUST support Telegram as a delivery platform
- The system MUST be designed for future expansion to WhatsApp
- The system MUST be designed for future expansion to SMS
- The system MUST handle platform-specific formatting requirements

#### Status Tracking
- The system MUST track delivery status of all messages
- The system MUST record delivery attempts and failures
- The system MUST provide status history for messages
- The system SHOULD allow manual retry of failed messages
- The system MUST support cancellation of scheduled messages

#### Error Handling
- The system MUST implement retry logic for transient failures
- The system MUST categorize errors properly (permanent vs. temporary)
- The system MUST provide detailed error information for failures
- The system MUST handle rate limiting from external APIs
- The system SHOULD gracefully degrade during partial outages

### Non-Functional Requirements

#### Performance
- The system MUST support sending at least 1000 messages per day
- The system MUST handle bursts of up to 100 messages in 15 minutes
- The system MUST deliver messages within 60 seconds of scheduled time
- Message processing SHOULD take less than 500ms per message
- Database queries SHOULD complete in under 100ms

#### Scalability
- The system MUST be horizontally scalable to handle increased load
- The system MUST use appropriate database indexes for efficient queries
- The system MUST implement connection pooling for database access
- The system SHOULD support parallel message processing
- The system MUST handle backpressure during high load

#### Reliability
- The system MUST have a 99.5% message delivery success rate
- The system MUST implement circuit breaker patterns for external services
- The system MUST handle infrastructure restarts gracefully
- The system MUST recover from crashes without message loss
- The system MUST log all critical errors for debugging

#### Security
- The system MUST secure all API credentials
- The system MUST validate message content before delivery
- The system MUST implement row-level security for the database
- The system MUST sanitize user input to prevent injection attacks
- The system SHOULD encrypt sensitive message content

#### Monitoring
- The system MUST provide metrics on message volume and delivery rates
- The system MUST alert on elevated failure rates
- The system MUST log all message delivery attempts
- The system SHOULD provide a dashboard for system health
- The system SHOULD track latency metrics for message delivery

## Technical Architecture

### Core Components

1. **Message Scheduler**: Handles creation and management of scheduled messages
2. **Message Processor**: Retrieves due messages and routes to appropriate handlers
3. **Platform Handlers**: Platform-specific components for message delivery
4. **Status Tracker**: Manages message statuses and delivery attempts
5. **Monitoring System**: Collects and reports on system metrics and health

### System Architecture Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│                 │     │                  │     │                    │
│ API Interface   │────▶│ Message Scheduler│────▶│ Database           │
│                 │     │                  │     │ (scheduled_messages)│
└─────────────────┘     └──────────────────┘     └────────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│                 │     │                  │     │                    │
│ Status Tracker  │◀────│ Message Processor│◀────│ Worker Pool        │
│                 │     │                  │     │                    │
└─────────────────┘     └──────────────────┘     └────────────────────┘
                                │                          │
                                ▼                          ▼
                        ┌──────────────────┐     ┌────────────────────┐
                        │                  │     │                    │
                        │ Platform Handlers│────▶│ External Platforms │
                        │                  │     │ (Telegram, etc.)   │
                        └──────────────────┘     └────────────────────┘
```

### Database Schema

The system uses a `scheduled_messages` table in Supabase with the following structure:

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

### Recommended Schema Updates
- **attempts**: INTEGER - Add field to track number of delivery attempts
- **last_attempt_time**: TIMESTAMPTZ - Timestamp of the last attempt
- **priority**: INTEGER - For prioritizing messages (optional)
- **metadata**: JSONB - For additional platform-specific data
- **delivery_window_seconds**: INTEGER - Flexibility window for delivery timing

### Technology Stack

- **Language**: Python 3.9+
- **Frameworks**: FastAPI, asyncio, SQLAlchemy
- **Database**: PostgreSQL with Supabase
- **External APIs**: Telegram Bot API
- **Deployment**: Docker, Kubernetes
- **Monitoring**: Prometheus, Grafana

## Implementation Details

### Telegram Bot Integration

#### File Structure
- Location: `src/ai_companion/interfaces/telegram/telegram_bot.py`
- Associated handler in `src/ai_companion/modules/scheduled_messaging/handlers/telegram_handler.py`

#### Key Components
- **TelegramBot class**: Main class that handles all Telegram interactions
- **Polling mechanism**: Asynchronous long-polling loop to receive updates
- **Message processing**: Extracts content and routes to appropriate handlers
- **Response handling**: Formats and sends responses, handles media types
- **Connection management**: Handles connection setup, health checks, and graceful shutdown

#### Message Sending Methods
| Method | Parameters | Return Type | Description | Notes |
|--------|------------|-------------|-------------|-------|
| `_send_message` | `chat_id: int, text: str` | `Dict` | Sends text message with chunking for long messages | Handles messages > 4000 chars by splitting |
| `_send_photo` | `chat_id: int, photo: bytes, caption: str = None` | `Dict` | Sends photo message | Handles long captions by sending separately |
| `_send_voice` | `chat_id: int, voice: bytes, caption: str = None` | `Dict` | Sends voice message | Sends caption as separate message |
| `_make_request` | `method: str, params: Dict = None, files: Dict = None, data: Dict = None, retries: int = 5` | `Dict` | Makes API requests with retry logic | Implements exponential backoff |

#### Authentication Pattern
- Uses bot token from settings: `settings.TELEGRAM_BOT_TOKEN`
- Token is included in API URL: `self.base_url = f"{self.api_base}/bot{self.token}"`
- No additional auth headers required for Telegram Bot API
- Settings loaded from environment variables

#### Error Handling
- **Comprehensive error handling** throughout the codebase
- **Retry mechanism** with exponential backoff for transient errors:
  ```python
  backoff_time = min(2 ** attempt + (0.1 * attempt), 30)
  ```
- **Error categorization**:
  - Client errors (400-499): Not retried, propagated up
  - Server errors (500+): Retried with backoff
  - Timeouts: Retried with backoff
- **Conflict handling** (409): Special case for webhook conflicts
- **Exception logging**: Detailed error messages with exception info

#### Threading Model
- **Fully asynchronous** using Python's `asyncio`
- **Single event loop** running the bot
- **Long-polling** in a while loop with `await` for non-blocking operation
- **Signal handlers** for graceful shutdown
- **Task management** with proper exception handling

### Handler Implementation

The existing codebase already includes a `TelegramHandler` class specifically designed for scheduled messages:

#### Key Methods
- `send_scheduled_message(schedule_data: Dict[str, Any]) -> Dict[str, Any]`: Main method for sending scheduled messages
- `send_message(chat_id: str, message: str, parse_mode: str = "HTML") -> Dict[str, Any]`: Sends a basic message
- `_make_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]`: Makes API requests

#### Integration Points
- Uses same API token as main bot
- Returns structured response with success/error information
- Handles all aspects of message delivery

### Processor Implementation

The system includes a dedicated message processor:

#### Key Components
- **Process runner**: Periodic task that checks for due messages
- **Message dispatcher**: Routes messages to appropriate platform handlers
- **Status updater**: Updates message status after delivery attempts
- **Recurrence handler**: Creates next occurrences for recurring messages

#### Processing Flow
1. Query for pending messages that are due
2. Process each message through appropriate handler
3. Update message status based on result
4. Create next occurrence if message is recurring

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

## Implementation Plan

The implementation is structured into three phases:

### Phase 1: Foundation & Core Infrastructure (Weeks 1-3)
- Database schema migration
- Worker pool implementation
- Message query optimization
- Basic error handling and platform integration

### Phase 2: Enhanced Capabilities (Weeks 4-6)
- Advanced retry logic
- Circuit breaker implementation
- Status tracking enhancements
- Platform extensions and API improvements

### Phase 3: Monitoring, Optimization & Deployment (Weeks 7-8)
- Metrics collection implementation
- Alerting system setup
- Performance tuning
- Production deployment

## Acceptance Criteria

### Message Scheduling
- Schedule a message for delivery at a future time
- Verify the message is delivered within 60 seconds of the scheduled time
- Schedule a recurring message and verify multiple deliveries
- Cancel a scheduled message and verify it is not delivered

### Platform Support
- Successfully deliver a plain text message via Telegram
- Successfully deliver an HTML-formatted message via Telegram
- Verify platform-specific formatting is applied correctly
- Verify long messages are handled appropriately

### Error Handling
- Simulate a temporary API failure and verify retry behavior
- Simulate a permanent failure and verify appropriate error recording
- Verify rate limiting handling by scheduling multiple messages
- Test recovery after service restart

### Monitoring
- Verify all message attempts are logged properly
- Confirm metrics collection for message volume and success rates
- Test alerting for elevated error rates
- Verify performance meets specified requirements

## Future Enhancements

### Platform Expansion
- WhatsApp integration using WhatsApp Business API
- SMS integration with multiple provider support
- Email as an alternative delivery channel
- Support for interactive message types (buttons, forms)

### Advanced Features
- Content personalization based on user profile
- AI-assisted message generation
- Advanced scheduling with timezone support
- Message delivery confirmation and read receipts
- A/B testing for message variations
- Advanced recurrence patterns (e.g., every 2 days, specific weekdays)
- More sophisticated template system with conditional logic
- User interface for healthcare providers to manage scheduled messages
- Analytics to track patient engagement with scheduled messages

## Confidence Assessment

Based on the completed analysis and design work:
- **95% confidence in solution architecture** - The design aligns well with existing systems
- **90% confidence in implementation timeline** - Clear scope with well-defined components
- **100% confidence in coding pattern consistency** - All designs follow existing patterns 