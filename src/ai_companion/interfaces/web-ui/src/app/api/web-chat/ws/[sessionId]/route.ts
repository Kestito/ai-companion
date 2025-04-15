import { NextResponse } from 'next/server';

// This route will be used for upgradable WebSocket connections
export async function GET(request: Request, { params }: { params: { sessionId: string } }) {
  // This function won't be used directly as WebSockets will be handled by Next.js's automatic WebSocket upgrading
  // But we need to provide a route to handle the initial HTTP request that will be upgraded to a WebSocket connection
  
  return new NextResponse(
    JSON.stringify({
      message: "This endpoint is for WebSocket connections only",
      status: 400
    }),
    {
      status: 400,
      headers: {
        'Content-Type': 'application/json',
      }
    }
  );
}

// In Next.js, the WebSocket handling happens at the server level
// Check middleware.ts file for WebSocket handling and proxying to backend 