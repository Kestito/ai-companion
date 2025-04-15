# API Structure Recommendations

## Overview

This document outlines the recommended API structure for the AI Companion application, focusing on the web-ui interface. The architecture follows a clean separation between server-side API routes and client-side API services.

## Recommended API Structure

Our API structure follows a clean separation between:

1. **API Routes** in `/src/ai_companion/interfaces/web-ui/src/app/api/` 
   - These handle HTTP requests and interact with the database
   - Implement RESTful endpoints (GET, POST, PUT, DELETE)
   - Handle authentication and authorization
   - Perform data validation
   - Return standardized responses

2. **API Services** in `/src/ai_companion/interfaces/web-ui/src/lib/api/services/` 
   - These provide a clean interface for components to interact with the API
   - Abstract away HTTP request details
   - Handle data transformation between frontend and API
   - Provide type safety with TypeScript interfaces
   - Centralize error handling

## Benefits

This separation provides several benefits:

- **Better Security**: Database credentials and operations are isolated to server-side code
- **Improved Maintainability**: Clear separation of concerns makes the codebase easier to understand and modify
- **Enhanced Flexibility**: The underlying data source can be changed without affecting components
- **Consistent Error Handling**: Standardized approach to error handling across the application
- **Scalability**: Better support for caching, middleware, and other API features

## Implementation Example

### API Route (Server-side)

```typescript
// app/api/scheduled-checks/route.ts
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const patientId = searchParams.get('patientId');
    
    if (!patientId) {
      return NextResponse.json(
        { error: 'Patient ID is required' },
        { status: 400 }
      );
    }
    
    const supabase = createClient();
    
    const { data, error } = await supabase
      .from('scheduled_checks')
      .select('*')
      .eq('patient_id', patientId)
      .order('next_scheduled', { ascending: true });
    
    if (error) {
      console.error('Error fetching scheduled checks:', error);
      return NextResponse.json(
        { error: 'Failed to fetch scheduled checks' },
        { status: 500 }
      );
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in scheduled checks API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### API Service (Client-side)

```typescript
// lib/api/services/scheduledChecks.service.ts
export async function fetchScheduledChecks(patientId: string): Promise<ScheduledCheck[]> {
  try {
    const response = await fetch(API_ENDPOINTS.SCHEDULED_CHECKS.BY_PATIENT(patientId));
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to fetch scheduled checks');
    }
    
    const data = await response.json();
    
    return (data || []).map((check: any) => ({
      id: check.id,
      title: check.title,
      description: check.description || '',
      frequency: check.frequency,
      nextScheduled: check.next_scheduled,
      status: check.status,
      platform: check.platform,
      patientId: check.patient_id,
      createdAt: check.created_at,
      updatedAt: check.updated_at
    }));
  } catch (err) {
    console.error('Error fetching scheduled checks:', err);
    return [];
  }
}
```

### Component Usage

```typescript
import { scheduledChecksService } from '@/lib/api';

function ScheduledChecksTab({ patientId }: { patientId: string }) {
  const [scheduledChecks, setScheduledChecks] = useState<ScheduledCheck[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadScheduledChecks = async () => {
      setLoading(true);
      try {
        const data = await scheduledChecksService.fetchScheduledChecks(patientId);
        setScheduledChecks(data);
      } catch (err) {
        console.error('Error loading scheduled checks:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadScheduledChecks();
  }, [patientId]);
  
  // ... rest of component
}
```

## Best Practices

1. Always use the API service approach over direct database access
2. Keep API routes focused on a single resource or operation
3. Implement proper error handling at all levels
4. Use TypeScript interfaces for request and response types
5. Document API endpoints and their expected parameters
6. Follow RESTful conventions for API routes
7. Use consistent naming conventions across the codebase

## Further Reading

For more detailed information, see the [API Integration](../src/ai_companion/interfaces/web-ui/project-docs/api-integration.md) document in the web-ui project documentation. 