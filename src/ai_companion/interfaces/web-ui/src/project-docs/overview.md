# AI Companion Scheduler Overview

## Background and Purpose
The AI Companion Scheduler is a component designed to enable scheduled messaging between the AI system and users via Telegram. It allows healthcare providers to schedule one-time or recurring messages to patients, providing reminders, follow-ups, or regular check-ins.

## Core Components
The scheduler system consists of several interconnected parts:

1. **Web UI Frontend**: Located at `/scheduled-messages` - Allows creating, viewing, and managing scheduled messages
2. **API Interface**: Located at `/api/scheduler` - Provides a REST API for managing scheduled messages
3. **Backend Service**: A Python service that processes the queue and sends messages at the scheduled times
4. **MCP Integration**: Management Control Panel integration for monitoring scheduler status

## Integration Points
- **Patient Management**: Pulls patient data including Telegram IDs from the patient database
- **Telegram Bot API**: Uses the configured Telegram bot to send messages to patients
- **Monitoring**: Provides health checking and status monitoring of the scheduler service
- **MCP**: Management Control Panel for enhanced monitoring and diagnostics

## Technical Notes
- Scheduled messages are stored in the database with status tracking (pending, sent, failed, cancelled)
- The backend scheduler runs on a periodic interval (typically every minute) to check for messages that need to be sent
- Recurring messages support daily, weekly, and monthly patterns
- Multiple fallback mechanisms for checking scheduler health:
  1. Direct health endpoint check
  2. MCP status API
  3. Database activity monitoring

## Troubleshooting
If the scheduler appears to be down or messages fail to load:

1. Check the scheduler service status via the health endpoint
2. Use the MCP to verify database connectivity
3. Ensure patients have valid Telegram IDs configured
4. Check for any network connectivity issues between services

## Current Status
The scheduler is operational but requires proper configuration of Telegram IDs in the patient database to function correctly. Messages can be scheduled, canceled, or sent immediately as needed. 