# Journey Logging System

The AI Companion includes a comprehensive logging system that helps track the flow of operations through the application. This "journey logging" approach makes it easier to understand how data flows through the system, diagnose issues, and ensure proper functionality.

## Key Features

- **Journey Tracking**: Log the complete flow of operations from start to finish
- **Numbered Steps**: Each key operation is numbered to show the sequence clearly
- **Context Awareness**: Log messages include relevant contextual data
- **Structured Formatting**: Consistent formatting makes logs easy to read
- **Fallback Visibility**: Clearly identifies when fallback mechanisms are invoked
- **Error Tracing**: Comprehensive error logging with full context

## Using the Journey Logger

The journey logger is implemented in `src/lib/utils/logger.ts` and can be used across the application:

```typescript
import { journeyLogger } from '@/lib/utils/logger';

async function createPatient() {
  // Create a new logger for this journey
  const logger = journeyLogger({ journeyName: 'PATIENT_CREATION' });
  
  // Start logging steps
  logger.step(1, 'Starting patient creation process');
  
  try {
    // Generate patient ID
    const patientId = generateId();
    logger.step(2, 'Generated patient ID', { id: patientId });
    
    // Get database client
    logger.step(3, 'Getting database client');
    const db = getClient();
    
    // Log successful operations
    logger.success('Database connection established');
    
    // Try database operations with fallback
    try {
      await db.createPatient(patientData);
      logger.success('Patient created in database');
    } catch (dbError) {
      logger.error('Database operation failed', dbError);
      logger.fallback('Using localStorage fallback');
      
      // Store in localStorage instead
      localStorage.setItem('patient', JSON.stringify(patientData));
    }
    
    // End the journey when complete
    logger.end();
    return patientId;
  } catch (error) {
    // Log critical errors
    logger.critical('Patient creation failed', error);
    logger.end('error');
    throw error;
  }
}
```

## Log Levels

The journey logger provides multiple log levels:

| Level | Function | Description |
|-------|----------|-------------|
| Step | `logger.step(number, message, data?)` | Log a numbered step in the journey |
| Info | `logger.info(message, data?)` | General information |
| Success | `logger.success(message, data?)` | Successful operations |
| Warning | `logger.warn(message, data?)` | Potential issues that don't stop execution |
| Error | `logger.error(message, error?)` | Errors that are handled |
| Critical | `logger.critical(message, error?)` | Severe errors that stop the journey |
| Fallback | `logger.fallback(message, data?)` | Fallback mechanisms being used |

## Implementation Locations

Journey logging has been implemented in the following locations:

1. **Patient Creation** (`app/login/page.tsx`): 
   - Tracks the complete process of creating a test patient
   - Shows schema validation, database operations, and fallback mechanisms

2. **Chat API** (`app/api/chat/route.ts`):
   - Logs the journey of a message from client to AI and back
   - Tracks schema validation, message storage, and API interactions

## Console Output Example

The journey logger produces structured output that makes it easy to follow the flow:

```
==================== PATIENT_CREATION JOURNEY ====================
[1] Starting patient creation process
[2] Generated patient ID: patient-1647812345-ab3d5f
[3] Getting Supabase client
[4] Generated random name: Test Patient
[5] Timestamp for registration: 2023-03-21T15:22:43.567Z
[6] Checking if patients table is valid...
[7] Querying patients table to verify schema
[8] Patients table validated successfully
[9] Sample patient data: {"id":"123","first_name":"Test","last_name":"User"...}
[10] Patients table is valid, preparing to create new patient record
[11] Patient data prepared: {"first_name":"Test","last_name":"Patient"...}
[12] Attempting to insert patient record into database...
[13] SUCCESS! Created patient with database ID: a7e8d2c5-f6b3-41e9-9a8c-1d2e3f4a5b6c
[15] Patient data saved to localStorage: {"id":"a7e8d2c5-f6b3-41e9-9a8c-1d2e3f4a5b6c"...}
[16] Set patient_test_mode cookie
[17] Preparing to redirect to patient chat...
[18] Redirecting to patient chat interface
==================== END PATIENT_CREATION JOURNEY ====================
```

## Benefits

1. **Debugging**: Quickly identify where issues occur in complex operations
2. **Monitoring**: Track system behavior in production environments
3. **Auditability**: Maintain a record of important operations for compliance
4. **Development**: Understand the flow of operations during development
5. **Testing**: Verify that operations proceed in the expected sequence

## Future Improvements

1. **Remote Logging**: Send logs to a centralized logging service
2. **Log Filtering**: Add the ability to filter logs by journey or level
3. **Performance Metrics**: Add timing information to track operation duration
4. **Visualization**: Create a visualization tool for journey logs
5. **Correlations**: Add correlation IDs to connect related journeys 