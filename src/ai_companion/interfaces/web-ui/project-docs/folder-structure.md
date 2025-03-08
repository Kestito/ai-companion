# Folder Structure

## Overview

This document outlines the folder structure for the AI Companion Web UI. We follow Next.js best practices by organizing all application code within the `/src` directory.

## Directory Structure

```
src/
├── app/                    # Next.js app router pages and layouts
│   ├── dashboard/          # Dashboard page routes
│   ├── login/              # Authentication routes
│   ├── users/              # User management routes
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Home page
│
├── components/             # React components
│   ├── auth/               # Authentication components
│   ├── chat/               # Chat components
│   ├── dashboard/          # Dashboard components
│   ├── icons/              # Icon components
│   ├── layout/             # Layout components
│   ├── providers/          # Context providers
│   ├── ui/                 # UI components (buttons, inputs, etc.)
│   └── users/              # User-related components
│
├── hooks/                  # Custom React hooks
│   ├── api/                # API-related hooks
│   ├── auth/               # Authentication hooks
│   └── ui/                 # UI-related hooks
│
├── lib/                    # Utility functions and services
│   ├── api/                # API services and types
│   ├── supabase/           # Supabase client and types
│   ├── theme/              # Theme configuration
│   └── utils.ts            # General utility functions
│
├── store/                  # State management
│   ├── auth/               # Authentication state
│   └── settings/           # App settings state
│
└── types/                  # TypeScript type definitions
    ├── api.ts              # API types
    ├── auth.ts             # Authentication types
    ├── models.ts           # Domain model types
    └── ui.ts               # UI component types
```

## Key Conventions

1. **Component Organization**
   - Each component should be in its own directory with related files
   - Example structure for a component:
     ```
     Button/
     ├── Button.tsx         # Component implementation
     ├── Button.test.tsx    # Component tests
     └── index.ts           # Re-export the component
     ```

2. **Path Aliases**
   - Use `@/` to import from the src directory
   - Example: `import { Button } from '@/components/ui/Button'`

3. **Type Organization**
   - Domain-specific types in separate files under `/types`
   - Component props defined in the component file or imported from `/types/ui.ts`

4. **State Management**
   - Context providers in `/components/providers`
   - State logic in `/store`

5. **Utilities**
   - All utility functions in `/lib`
   - Group related functions in their own files

## Import Guidelines

- Prefer absolute imports with the `@/` alias
- Example: `import { cn } from '@/lib/utils'` rather than relative paths
- Group imports in the following order:
  1. React and Next.js
  2. External libraries
  3. Internal components and hooks
  4. Types and utilities
  5. Assets (styles, images)

## Migration Notes

The codebase previously had duplicate directories at the root level (`/components`, `/lib`). All code has been consolidated into the `/src` directory according to Next.js best practices. 