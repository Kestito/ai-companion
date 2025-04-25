# Scheduled Messages Feature

## Overview
The Scheduled Messages feature enables users to create and manage scheduled communications with patients across multiple platforms (Telegram, Email, SMS). It provides a flexible scheduling system with support for one-time and recurring messages.

## Database Schema
The `scheduled_messages` table contains:
- `id`: UUID (primary key)
- `patient_id`: UUID (foreign key to patients)
- `scheduled_time`: Timestamp for message delivery
- `message_content`: Text content of the message
- `status`: Current message status (pending, sent, failed, cancelled)
- `platform`: Delivery platform (telegram, email, sms)
- `created_at`: Creation timestamp
- `attempts`: Number of delivery attempts
- `last_attempt_time`: Last delivery attempt timestamp
- `priority`: Message priority level
- `metadata`: Additional JSON data
- `delivery_window_seconds`: Allowed delivery window

## Current Features
- Schedule one-time messages
- Set up recurring messages (daily, weekly, monthly)
- View message status
- Send scheduled messages immediately
- Cancel pending messages
- Retry failed messages

## Planned Enhancements

### UI Improvements
1. **Enhanced Filtering**
   - Filter by platform (Telegram, Email, SMS)
   - Filter by date range
   - Full-text search for message content
   - Multiple status filters

2. **Improved Form**
   - Step-by-step scheduling wizard
   - Platform selection based on patient contact info
   - Priority selection
   - Message templates
   - Character count and validation
   - Delivery window configuration

3. **Message Management**
   - Detailed message view with history
   - Batch operations (cancel multiple, reschedule)
   - Message duplication functionality
   - Export schedules to CSV

4. **Visual Enhancements**
   - Status indicators with colors
   - Calendar view for scheduled messages
   - Mobile-responsive design
   - Dark mode support

## Implementation Timeline
- Phase 1: Basic UI improvements and filtering
- Phase 2: Enhanced form with multi-platform support
- Phase 3: Advanced management features
- Phase 4: Visual enhancements and calendar view

## Technical Implementation Notes
- Use React hooks for state management
- MaterialUI components for consistency
- Responsive design with flex layouts
- Optimistic UI updates for better UX
- Form validation with error handling 