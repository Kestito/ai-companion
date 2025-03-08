# Migration Plan: Directory Structure Consolidation

## Overview

This document outlines the plan for consolidating duplicate directories in the AI Companion Web UI project. The goal is to move all code from root-level directories (`/components`, `/lib`) into the `/src` directory to follow Next.js best practices.

## Prerequisites

Before beginning the migration:

- Ensure all tests are passing
- Create a backup or work in a dedicated branch
- Inform team members of the planned changes

## Migration Steps

### 1. Components Migration

#### Step 1: Move files from `/components` to `/src/components`

1. Create corresponding directory structure in `/src/components` if it doesn't exist
2. For each component:
   - Copy the component to the new location
   - Add proper JSDoc documentation
   - Update imports to use `@/` path alias
   - Create an `index.ts` file to re-export the component

#### Step 2: Update imports

Run a search for all imports from `/components` and update them to use the new location:

```typescript
// Before
import { Component } from '@/components/path/Component';
// or 
import { Component } from 'components/path/Component';

// After
import { Component } from '@/components/path/Component';
```

### 2. Library Migration

#### Step 1: Move files from `/lib` to `/src/lib`

1. Create corresponding directory structure in `/src/lib` if it doesn't exist
2. For each utility:
   - Copy the utility to the new location
   - Add proper JSDoc documentation
   - Update imports to use `@/` path alias

#### Step 2: Update imports

Run a search for all imports from `/lib` and update them to use the new location:

```typescript
// Before
import { utility } from '@/lib/path/utility';
// or
import { utility } from 'lib/path/utility';

// After
import { utility } from '@/lib/path/utility';
```

### 3. Testing

After migration:

1. Run all tests to ensure they pass
2. Verify the application builds successfully
3. Manually test key functionality to ensure nothing was broken

### 4. Cleanup

Once everything is working:

1. Remove the original directories (`/components`, `/lib`)
2. Update documentation to reflect the new structure

## Rollback Plan

If issues are encountered:

1. Revert to the previous commit/branch
2. Document the specific issues encountered
3. Create a more targeted migration plan

## Timeline

- **Phase 1**: Move components and update imports (1-2 days)
- **Phase 2**: Move utilities and update imports (1 day)
- **Phase 3**: Testing and validation (1 day)
- **Phase 4**: Cleanup and documentation (0.5 day)

## Team Communication

- Announce the migration start date to all team members
- Share documentation on the new structure
- Schedule a brief demo of the updated structure after completion 