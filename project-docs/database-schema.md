# AI Companion Database Schema

This document outlines the database schema used in the AI Companion application. The system uses Supabase as the primary database provider.

## Core Tables

### Patients

The `patients` table stores information about users who interact with the AI companion as patients.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| email | text | Email or platform metadata (JSON string) |
| phone | text | Phone number or platform identifier |
| first_name | text | Patient's first name |
| last_name | text | Patient's last name |
| created_at | timestamp | Account creation timestamp |
| last_active | timestamp | Last activity timestamp |
| preferred_language | text | Language preference code (e.g., 'en') |
| subility_eligible | bool | Eligibility flag |
| legal_consents | jsonb | Consent status for various legal agreements |
| support_status | text | Current support status |

### Conversations

The `conversations` table stores high-level information about conversation sessions.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| patient_id | uuid | Reference to patients.id |
| platform | text | Platform identifier (e.g., 'web-ui', 'whatsapp') |
| start_time | timestamp | Conversation start time |
| end_time | timestamp | Last message time |
| conversation_type | text | Type of conversation |
| status | text | Current status (active, completed, etc.) |

### Conversation Details

The `conversation_details` table stores detailed information about each conversation message and metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| conversation_id | uuid | Reference to conversations.id |
| message_content | text | Message text content |
| message_type | text | Type of message |
| sent_at | timestamp | Timestamp when message was sent |
| sender | text | Message sender (user, assistant, system) |
| metadata | jsonb | Additional metadata (JSON string) |

### Messages

The `messages` table stores general message data.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| patient_id | uuid | Reference to patients.id |
| content | text | Message content |
| message_type | text | Type of message |
| sent_at | timestamp | Timestamp when sent |
| read_at | timestamp | Timestamp when read |
| priority | text | Message priority |
| metadata | jsonb | Additional metadata |

### Short Term Memory

The `short_term_memory` table stores short-term memory for conversations.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| patient_id | uuid | Reference to patients.id |
| conversation_id | uuid | Reference to conversations.id |
| context | text | Memory context |
| expires_at | timestamp | Expiration timestamp |

### Long Term Memory

The `long_term_memory` table stores persistent memory across conversations.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| patient_id | uuid | Reference to patients.id |
| memory_type | text | Type of memory |
| content | text | Memory content |
| recorded_at | timestamp | When the memory was recorded |

### Scheduled Messages

The `scheduled_messages` table stores messages that are scheduled to be sent.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| patient_id | uuid | Reference to patients.id |
| scheduled_time | timestamp | When to send the message |
| message_content | text | Content to send |
| status | text | Scheduling status |
| platform | text | Delivery platform |
| created_at | timestamp | When scheduled |

### Risk Assessments

The `risk_assessments` table stores risk assessment information.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| patient_id | uuid | Reference to patients.id |
| risk_type | text | Type of risk |
| risk_level | text | Assessed risk level |
| detected_at | timestamp | Detection timestamp |
| trigger_criteria | text | What triggered the assessment |

### Reports

The `reports` table stores generated reports.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| generated_by | uuid | Who/what generated the report |
| report_type | text | Type of report |
| generated_at | timestamp | Generation timestamp |
| report_format | text | Format of the report |
| storage_path | text | Where the report is stored |
| parameters | jsonb | Report generation parameters |

## Relationships

- `patients` ← one-to-many → `conversations`: A patient can have many conversations
- `conversations` ← one-to-many → `conversation_details`: A conversation has many detail records
- `patients` ← one-to-many → `messages`: A patient can have many messages
- `conversations` ← one-to-many → `messages`: A conversation can include many messages
- `patients` ← one-to-many → `short_term_memory`: A patient can have multiple short-term memory records
- `patients` ← one-to-many → `long_term_memory`: A patient can have multiple long-term memory records
- `patients` ← one-to-many → `scheduled_messages`: A patient can have multiple scheduled messages
- `patients` ← one-to-many → `risk_assessments`: A patient can have multiple risk assessments

## Implementation Notes

- The system is designed to be resilient to schema variations
- Primary communication flow: `conversations` → `conversation_details` → `messages`
- For test/demo purposes, fallbacks to localStorage are implemented when database tables are unavailable
- `conversation_details` serves as the main table for conversation history tracking
- JSON metadata is used extensively to maintain flexibility

## Schema Information

- **Schema Name**: `evelinaai`
- **Database**: Supabase
- **Schema Version**: Current as of March 2024

## Key Features
1. User Management
   - Multi-role support (patient, doctor)
   - Activity tracking
   - Risk level monitoring

2. Medical Records
   - Risk assessments
   - Appointment scheduling
   - Report generation

3. AI Interaction
   - Conversation tracking
   - Memory management (short-term and long-term)
   - Detailed conversation analysis

## Security Considerations
- All tables include created_at timestamps for audit trails
- Foreign key constraints ensure data integrity
- JSONB fields allow flexible metadata storage while maintaining structure

## Performance Notes
- Indexes are recommended on:
  - users(email)
  - users(status)
  - conversations(user_id)
  - scheduled_appointments(scheduled_time)
  - risk_assessments(user_id, risk_level) 

## Schema Access Verification

To verify access to the schema, use the verification script:

```bash
node src/ai_companion/interfaces/web-ui/scripts/verify-evelinaai-schema.js
```

This script will test connectivity to all tables in the `evelinaai` schema and confirm schema existence. 