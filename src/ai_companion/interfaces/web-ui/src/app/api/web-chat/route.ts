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
    });
    
    // Get the response from the backend
    const data = await response.json();
    
    // Return the response to the frontend
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in web-chat API route:', error);
    
    // Return error response
    return NextResponse.json(
      {
        error: 'Failed to communicate with the backend',
        session_id: '',
        response: 'Sorry, I encountered an error processing your request.',
      },
      { status: 500 }
    );
  }
} 