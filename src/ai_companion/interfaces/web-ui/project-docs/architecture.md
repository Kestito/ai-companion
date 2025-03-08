# Web-UI Architecture

## Overview
The web-ui interface serves as the frontend for the AI Companion system, providing an intuitive and responsive user interface for interacting with the AI system. It is built using Next.js 14, React 18, TypeScript, and Material UI with TailwindCSS for styling.

## Directory Structure

```
web-ui/
├── public/                  # Static assets and images
├── src/
│   ├── app/                 # Next.js App Router pages and layouts
│   ├── components/          # All React components
│   │   ├── auth/            # Authentication related components
│   │   ├── chat/            # Chat interface components
│   │   ├── dashboard/       # Dashboard related components
│   │   ├── icons/           # SVG icons and visual elements
│   │   ├── layout/          # Layout components (header, footer, etc.)
│   │   ├── providers/       # Context providers
│   │   ├── ui/              # Reusable UI components
│   │   └── users/           # User management components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utility libraries
│   │   ├── api/             # API integration layer
│   │   ├── supabase/        # Supabase client and utilities
│   │   └── theme/           # Theme configuration
│   ├── store/               # State management 
│   └── utils/               # Helper functions
├── project-docs/            # Project documentation
├── types/                   # TypeScript type definitions
└── tests/                   # Test files
```

## Key Technologies

- **Next.js 14**: React framework with App Router for routing
- **React 18**: UI library with hooks and functional components
- **TypeScript**: For type safety across the application
- **Material UI**: Component library for consistent UI elements
- **TailwindCSS**: Utility-first CSS framework for styling
- **Supabase**: Backend integration for authentication and data
- **i18next**: Internationalization support

## Architectural Patterns

1. **Component Structure**: Functional components with TypeScript interfaces
2. **API Integration**: Custom hooks and service layer for API calls
3. **State Management**: React Context API for global state
4. **Styling Approach**: Material UI with TailwindCSS for custom styling
5. **Routing**: Next.js App Router with layouts and nested routes
6. **Authentication**: Supabase Auth with protected routes
7. **Error Handling**: ErrorBoundary components and consistent error states

## Best Practices

1. **Accessibility**: All components follow WCAG guidelines
2. **Performance**: Code splitting, lazy loading, and optimized rendering
3. **Security**: CSP headers, input validation, and secure authentication
4. **Testing**: Unit tests for components and integration tests for key flows
5. **Documentation**: Component props documentation and usage examples 