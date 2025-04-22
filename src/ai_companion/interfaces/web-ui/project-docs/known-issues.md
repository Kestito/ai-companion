# Known Issues and Solutions

This document tracks known issues encountered during development and their solutions. It serves as a reference for the team to avoid repeating the same troubleshooting steps.

## Dependencies and Compatibility Issues

### date-fns Version Compatibility with @mui/x-date-pickers

**Issue:** The application fails to compile with an error related to date-fns and @mui/x-date-pickers:

```
Module not found: Package path ./_lib/format/longFormatters is not exported from package date-fns
```

**Root Cause:** The @mui/x-date-pickers component is not compatible with date-fns version 4.x. It requires date-fns version 2.x.

**Solution:** Downgrade date-fns to version 2.30.0:

```bash
npm install date-fns@2.30.0 --save
```

**Date Resolved:** March 12, 2023

## API and TypeScript Issues

### Duplicate Export Names in API Files

**Issue:** TypeScript error during build due to duplicate export names:

```
Type error: Module './client' has already exported a member named 'ApiError'. Consider explicitly re-exporting to resolve the ambiguity.
```

**Root Cause:** Both `client.ts` and `types.ts` were exporting an entity named `ApiError`, causing a naming conflict.

**Solution:** Renamed the `ApiError` interface in `types.ts` to `ApiErrorDetails` to avoid the conflict with the `ApiError` class from `client.ts`.

**Date Resolved:** March 12, 2023

## UI and Component Issues

(No issues documented yet)

## Performance Issues

(No issues documented yet)

## Security Issues

(No issues documented yet)

## Browser Compatibility Issues

(No issues documented yet)

## Mobile Responsiveness Issues

(No issues documented yet)

## Build Issues

### Missing Type Definitions (FIXED)

**Issue:**  
When building the Docker image, the build would fail due to missing type definitions for Supabase database.

**Error:**  
```
Failed to compile.
Type error: Cannot find module '@/types/database.types' or its corresponding type declarations.

  2 | import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
  3 | import { cookies } from 'next/headers';
> 4 | import { Database } from '@/types/database.types';
```

**Resolution:**  
Created the file `src/types/database.types.ts` with the appropriate TypeScript interfaces for the database schema.

**Prevention:**  
When adding new database tables or modifying existing ones, make sure to update the type definitions in `database.types.ts` to match the schema.

### OpenAI API Key Missing (FIXED)

**Issue:**  
Build failed during page data collection due to missing OpenAI API key.

**Error:**  
```
[Error]: The OPENAI_API_KEY environment variable is missing or empty; either provide it, or instantiate the OpenAI client with an apiKey option, like new OpenAI({ apiKey: 'My API Key' }).
```

**Resolution:**  
Added a fallback mechanism in the risk assessment generator to use either:
1. The `OPENAI_API_KEY` environment variable
2. The `NEXT_PUBLIC_AZURE_OPENAI_API_KEY` environment variable
3. A mock response if no API keys are available

**Prevention:**  
Always use conditional initialization for external services like OpenAI, with proper error handling and fallbacks for development environments.

## How to Add New Issues

When adding a new issue to this document, please follow this template:

```markdown
### Brief Title of the Issue

**Issue:** Clear description of the issue and any error messages.

**Root Cause:** Explanation of what caused the issue.

**Solution:** Step-by-step solution or code changes that resolved the issue.

**Date Resolved:** Date when the issue was resolved.
``` 