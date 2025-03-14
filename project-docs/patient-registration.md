# Patient Registration Module

## Overview
The Patient Registration module enables the AI Companion to create new patient records in the Supabase database from Telegram or WhatsApp messages. This feature allows healthcare providers to quickly register new patients through simple text commands.

## Implementation Details

### Components

1. **Router Detection**
   - The `router_node` component now detects phrases indicating patient registration requests in both English and Lithuanian
   - When detected, the workflow is routed to the patient registration node

2. **Patient Registration Node**
   - A dedicated node (`patient_registration_node`) processes registration requests
   - Extracts patient information from messages using regex pattern matching
   - Creates a new patient record in the Supabase database
   - Generates a unique patient ID
   - Stores registration metadata in conversation memory

3. **Supabase Integration**
   - Uses the Supabase client utility for database operations
   - Patient records are stored in the `patients` table
   - Table schema includes: id, name, phone, email, status, platform, and timestamps

4. **Important Implementation Notes**
   - The `patients` table uses UUID format for the primary key (`id` field)
   - Telegram/WhatsApp user IDs are numeric and cannot be directly used as UUIDs
   - User identifiers from messaging platforms are stored in the `email` field as JSON metadata
   - When looking up patients by platform user ID, always use a LIKE query on the email field:
     ```python
     # Correct way to find a patient by Telegram user ID
     metadata_search = f'%"user_id": "{user_id}"%'
     result = supabase.table("patients").select("id").like("email", metadata_search).execute()
     ```
   - Never attempt to query directly by messaging platform ID in the UUID field:
     ```python
     # INCORRECT - will cause "invalid input syntax for type uuid" error
     result = supabase.table("patients").select("id").eq("id", str(user_id)).execute()
     ```

5. **Graph Integration**
   - The node is properly integrated into the processing graph
   - Edge definitions ensure proper routing to the node
   - Conversation flow is maintained after registration

## Usage

### Registration Commands
Users can trigger patient registration with phrases like:
- "register new patient"
- "add patient"
- "create patient" 
- Lithuanian equivalents like "naujas pacientas"

### Data Format
For optimal information extraction, use the following format:
```
register new patient name: John Doe phone: +1234567890
```

The system extracts:
- **Name**: Text after "name:" until a new line or comma
- **Phone**: Digits and symbols after "phone:"

### Response
After successful registration, the system responds with:
```
Patient John Doe has been registered successfully with ID: pat_12345
```

## Testing
A test script (`test_patient_registration.py`) is provided to verify:
- Pattern detection in the router node
- Patient creation functionality
- Database integration

## Security Considerations
- Row-level security is implemented on the `patients` table
- Policies control who can read and write patient data
- No sensitive patient data (besides basic contact info) is stored

## Future Enhancements
- Enhance NLP for better information extraction
- Add more patient fields (medical history, insurance info)
- Implement verification and validation of patient data
- Add integration with appointment scheduling
- Support for other messaging platforms 