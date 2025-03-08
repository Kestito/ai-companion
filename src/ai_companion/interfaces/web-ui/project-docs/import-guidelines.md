# Import Guidelines

This document provides guidelines for importing modules and components in the AI Companion Web UI codebase.

## Path Aliases

The project uses Next.js path aliases to make imports cleaner and more maintainable. The primary alias is:

- `@/` - Points to the `src` directory

## Import Examples

### Correct Usage

```typescript
// Importing components
import { Button } from '@/components/ui/Button';
import { RouteGuard } from '@/components/auth/RouteGuard';

// Importing hooks
import { useAuth } from '@/hooks/auth/useAuth';

// Importing utilities
import { cn } from '@/lib/utils';
import { getSupabaseClient } from '@/lib/supabase/client';

// Importing types
import { User } from '@/types/auth';
import { ApiResponse } from '@/types/api';
```

### Avoid These Patterns

```typescript
// ❌ Avoid relative paths that traverse multiple directories
import { Button } from '../../components/ui/Button';

// ❌ Avoid direct imports from the root components directory (use src instead)
import { Button } from 'components/ui/Button';
import { Button } from '@/components/ui/Button'; // When importing from non-src components

// ❌ Avoid direct imports from the root lib directory (use src instead)
import { cn } from 'lib/utils';
import { cn } from '@/lib/utils'; // When importing from non-src lib
```

## Import Order

Organize imports in the following order:

1. React and Next.js imports
   ```typescript
   import React, { useState, useEffect } from 'react';
   import { useRouter } from 'next/router';
   import Image from 'next/image';
   ```

2. External library imports
   ```typescript
   import { CircularProgress } from '@mui/material';
   import clsx from 'clsx';
   ```

3. Internal components and hooks
   ```typescript
   import { Button } from '@/components/ui/Button';
   import { useAuth } from '@/hooks/auth/useAuth';
   ```

4. Types and utilities
   ```typescript
   import { User } from '@/types/auth';
   import { cn } from '@/lib/utils';
   ```

5. Assets (styles, images)
   ```typescript
   import logo from '@/public/logo.svg';
   import '@/styles/component.css';
   ```

## Directory Structure Changes

Previously, the project had duplicate directories at the root level (`/components`, `/lib`). All code has been consolidated into the `/src` directory to follow Next.js best practices.

When working on existing code, be sure to update any imports that reference the old paths. 