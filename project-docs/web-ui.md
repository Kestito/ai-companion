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
- Patient information display for Telegram and WhatsApp messages
- Fully responsive design for mobile, tablet, and desktop devices

## Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **UI Library**: Material UI with TailwindCSS
- **Authentication**: Supabase Auth
- **State Management**: React Context API
- **Internationalization**: i18next
- **Responsive Design**: Mobile-first approach with responsive breakpoints

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
│   │   ├── chat/      # Chat-related components including PatientInfo
│   │   ├── patients/  # Patient management components
│   │   └── ...        # Other component categories
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

### Chat Interface Features

The chat interface includes the following features:

1. **Message Display**: Shows messages from both the user and the AI assistant with appropriate styling
2. **Patient Information**: When messages come from Telegram or WhatsApp, patient information is displayed at the top of the chat
3. **Message Source Indication**: Messages show their source (Telegram, WhatsApp, or Web)
4. **Real-time Updates**: New messages are automatically scrolled into view
5. **Message Input**: Users can type and send messages with keyboard shortcuts

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

## Best Practices

### Defensive Programming

When working with the Web UI, it's important to follow defensive programming practices to ensure the application is robust and can handle unexpected data:

1. **Always add null checks for data from external sources**:
   ```tsx
   // Good practice
   {patient?.id && patient.id.substring(0, 8)}
   
   // Avoid
   {patient.id.substring(0, 8)}
   ```

2. **Use optional chaining for nested properties**:
   ```tsx
   // Good practice
   {user?.profile?.name}
   
   // Avoid
   {user.profile.name}
   ```

3. **Provide fallback values for all displayed properties**:
   ```tsx
   // Good practice
   {patient?.email || 'No email available'}
   
   // Avoid
   {patient.email}
   ```

4. **Validate data before setting state**:
   ```tsx
   // Good practice
   if (data && data.name) {
     setPatient(data);
   }
   
   // Avoid
   setPatient(data);
   ```

5. **Use TypeScript properly**:
   - Define interfaces for all data structures
   - Use strict null checking
   - Avoid using `any` type when possible

Following these practices will help prevent common runtime errors like "Cannot read properties of undefined" that can break the user experience.

## Supabase Dashboard Integration

The dashboard in the Web UI displays real-time data from Supabase, providing up-to-date information for users. This integration follows a robust pattern to ensure data is always available, even in case of connectivity issues or missing tables.

### Data Sources

The dashboard fetches three main types of data from Supabase:

1. **Patient Statistics**: Basic metrics about patients, including:
   - Total patients count
   - Active patients count
   - New patients (registered in the last 24 hours)
   - Critical patients count
   - Pending appointments
   - Response rate

2. **Activity Logs**: Recent system activity showing what actions have been performed, who performed them, and when.

3. **Notifications**: Important system alerts and notifications for the user.

### Resilient Data Fetching Pattern

The dashboard implements a resilient data fetching pattern with these key features:

1. **Primary and Alternative Table Sources**:
   - The system first tries to fetch from the primary tables (`patients`, `activity_logs`, `notifications`)
   - If a primary table doesn't exist, it tries alternative tables (`system_logs`, `system_notifications`, `alerts`)
   - Only falls back to mock data when no valid tables can be found

2. **Graceful Error Handling**:
   - "Table not found" errors (code '42P01') are handled separately from other errors
   - Critical errors are displayed to the user with retry options
   - Non-critical errors are logged but don't block the UI

3. **User Refreshing**:
   - The dashboard includes a refresh button to manually update data
   - Last updated timestamp is displayed to show data freshness
   - Error messages include a retry button for easy recovery

### Implementation Details

The integration is implemented in these key files:

- `src/lib/supabase/patientService.ts`: Handles patient statistics and related data
- `src/lib/supabase/activityService.ts`: Manages activity logs 
- `src/lib/supabase/notificationService.ts`: Handles notifications and alerts
- `src/app/dashboard/page.tsx`: Dashboard UI that consumes the data

Each service implements a consistent pattern:
1. Try to fetch from primary data source
2. If not available, try alternative data sources
3. Provide fallback data only when real data cannot be retrieved
4. Log appropriate diagnostic information

### Fallback Data

Fallback data is only used in these scenarios:
- When tables don't exist in the database yet
- When a critical error occurs during data fetching
- When returned data is empty

This ensures that the dashboard always displays something useful to the user, even in degraded states.

### Schema Evolution Support

The services support schema evolution by trying multiple table access patterns:
- Direct table name access in the public schema
- Schema-prefixed table names
- Legacy schema support for backward compatibility

This makes the dashboard resilient to schema changes and migrations.

## Authentication and User Management

The web UI provides several authentication methods:

1. Email/Password Authentication
2. Google OAuth (planned)
3. Microsoft OAuth (planned)
4. Demo Mode - For testing without real credentials
5. Patient Test Mode - For simulating a patient experience

For development and demonstration purposes, you can use the Demo account:
- Email: demo@evelina.ai
- Password: demo123

### Demo Mode

The Demo Mode allows users to explore the dashboard without requiring real authentication. When a user selects "Use Demo Account" on the login page, a cookie is set to identify them as a demo user, and they are redirected to the dashboard with simulated data.

### Patient Test Mode

The "Try as a Patient" feature allows users to experience the platform from a patient's perspective. This feature creates an actual patient record in the database and leverages the same conversation graph used by other interfaces like Telegram.

Key aspects of the Patient Test Mode:

1. **Patient Creation**: When a user clicks "Try as a Patient", the system:
   - Generates a unique patient identifier
   - Creates a real patient record in the database
   - Sets a cookie to identify this as a test patient session
   - Stores patient information in localStorage for client-side access

2. **Conversation Storage**: All conversations in the test mode are stored in the database and can be reviewed by administrators. This helps in:
   - Training and improving the AI assistant
   - Identifying common patient questions
   - Testing the robustness of the conversation graph

3. **Graph Integration**: The patient chat uses the same graph-based conversation logic as other interfaces, ensuring consistency across platforms.

4. **API Integration**: The patient chat communicates with the backend through the `/api/chat` endpoint, which:
   - Creates and manages conversation records
   - Stores message history
   - Interacts with the AI conversation graph

To access this feature, click the "Try as a Patient" button on the login page. You'll be redirected to a chat interface where you can interact with the AI assistant as if you were a patient.

**Note**: While this creates a real patient record, it's marked as a test record in the database to distinguish it from actual patients.

## Mobile Responsiveness

The Web UI is built with a mobile-first approach, ensuring excellent usability across all device sizes:

### Key Mobile Features

1. **Adaptive Layout**: The interface automatically adjusts based on screen size:
   - Collapsible sidebar on desktop
   - Slide-out drawer with backdrop on mobile
   - Optimized header with reduced elements on small screens

2. **Touch-Friendly Elements**:
   - Larger touch targets for mobile users
   - Swipeable navigation drawer
   - Optimized button and input sizes

3. **Responsive Typography**:
   - Font sizes automatically adjust for readability on small screens
   - Proper text wrapping and truncation to prevent overflow

4. **Optimized Components**:
   - Cards and dialogs resize appropriately for mobile screens
   - Mobile-friendly menus and dropdowns
   - Stacked layouts for forms and data displays on small screens

### Implementation Details

The responsive design is implemented through:

1. **Media Queries**: Both in Tailwind CSS and MUI theme configuration
2. **Responsive MUI Components**: Using breakpoint-aware props like `sx={{ display: { xs: 'none', md: 'flex' } }}`
3. **Dynamic Layout Changes**: Different components/layouts loaded based on screen size
4. **Responsive State Management**: Navigation context automatically adapts to screen size changes

### Testing Mobile Responsiveness

When making changes to the Web UI, ensure to test across multiple device sizes:
- Mobile phone (320px-480px width)
- Tablet (481px-768px width)
- Small laptop (769px-1024px width)
- Desktop (1025px+ width)

Browser developer tools can simulate these different device sizes for testing. 