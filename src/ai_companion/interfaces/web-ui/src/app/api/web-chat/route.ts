import { NextRequest, NextResponse } from 'next/server';

/**
 * Handle POST requests to /api/web-chat
 * This route proxies requests from the frontend to the backend web-chat API
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Get backend URL from environment variables
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Forward the request to the backend
    const response = await fetch(`${apiUrl}/web-chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      // Add a longer timeout for the API call
      signal: AbortSignal.timeout(30000), // 30 second timeout
    });
    
    // Check for response status
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend API error (${response.status}):`, errorText);
      return NextResponse.json(
        {
          error: `Backend error: ${response.status} ${response.statusText}`,
          session_id: body.session_id || '',
          response: "I'm having trouble processing your request. Please try again in a moment.",
        },
        { status: response.status }
      );
    }
    
    // Get the response from the backend
    const data = await response.json();
    
    // Return the response to the frontend
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in web-chat API route:', error);
    
    // Return error response with more details
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    return NextResponse.json(
      {
        error: `Failed to communicate with the backend: ${errorMessage}`,
        session_id: '',
        response: 'Sorry, I encountered a technical issue while processing your request. Please try again or contact support if the problem persists.',
      },
      { status: 500 }
    );
  }
} 