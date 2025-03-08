# Web UI Interface

This document provides information about the AI Companion's Next.js-based Web UI interface.

## Overview

The Web UI is a modern, responsive interface built with Next.js, TypeScript, and Material UI. It provides an enhanced user experience for interacting with the AI Companion system, offering features such as:

- User authentication via Supabase
- Multi-language support
- Dark/light mode theme switching
- Real-time chat with AI
- History management and search
- Document upload and management

## Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **UI Library**: Material UI with TailwindCSS
- **Authentication**: Supabase Auth
- **State Management**: React Context API
- **Internationalization**: i18next

## Running the Web UI

### As a Standalone Component

The Web UI can be run separately from the other interfaces:

```bash
# Navigate to the web-ui directory
cd src/ai_companion/interfaces/web-ui

# Install dependencies
npm install

# Run in development mode
npm run dev

# Or build and run in production mode
npm run build
npm run start
```

### Using Docker

```bash
# Build the web-ui image
docker build -t ai-companion-web-ui:latest -f src/ai_companion/interfaces/web-ui/Dockerfile src/ai_companion/interfaces/web-ui

# Run the container
docker run -p 3000:3000 ai-companion-web-ui:latest
```

### Environment Variables

The Web UI requires the following environment variables:

```
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000  # URL of the main FastAPI app
```

You can set these by creating a `.env.local` file in the web-ui directory.

## Integration with Backend Services

The Web UI communicates with the main FastAPI application running on port 8000. It does not directly start or interact with other interfaces like Chainlit, Telegram, or the monitoring interface.

When using the Web UI, make sure the main FastAPI application is running separately.

## Project Structure

```
web-ui/
├── src/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # Reusable UI components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility libraries and clients
│   ├── store/         # State management
│   └── utils/         # Helper functions
├── public/            # Static assets
├── types/             # TypeScript type definitions
├── next.config.js     # Next.js configuration
├── package.json       # Project dependencies
└── tailwind.config.js # TailwindCSS configuration
```

## Development

### Adding New Features

When adding new features to the Web UI:

1. Follow the existing directory structure
2. Ensure components are properly typed with TypeScript
3. Use Tailwind CSS for styling
4. Add necessary translations to the localization files

### Building for Production

For production deployment, the Web UI is built as a standalone Next.js application:

```bash
npm run build
```

This creates a `.next/standalone` directory with a `server.js` file that can be run with Node.js.

## Troubleshooting

If you encounter issues with the Web UI:

1. Check the browser console for JavaScript errors
2. Verify the environment variables are correctly set
3. Ensure the main FastAPI application is running and accessible
4. Check that Supabase authentication is properly configured

## Contributing

When contributing to the Web UI:

1. Follow the project's code style and formatting guidelines
2. Write comprehensive test cases for new components
3. Document any API changes or new environment variables
4. Ensure the application works in both dark and light modes
5. Verify that all features are accessible and responsive 