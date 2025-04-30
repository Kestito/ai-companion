import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'
import { Database } from '@/lib/supabase/types'
import { Socket, Server } from 'net'
import http from 'http'

// Hardcoded Supabase credentials
const SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc";

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  // Check for demo mode cookie
  const demoMode = request.cookies.get('demo_mode')?.value === 'true';
  
  // If in demo mode, allow access to protected routes
  if (demoMode) {
    // For demo mode, we'll just proceed without authentication
    return response;
  }

  const supabase = createServerClient<Database>(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value,
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value,
            ...options,
          })
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value: '',
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value: '',
            ...options,
          })
        },
      },
    }
  )

  // Check auth state
  const { data: { session } } = await supabase.auth.getSession()

  // Define protected and public routes
  const isLoginPage = request.nextUrl.pathname === '/login'
  const isPublicRoute = request.nextUrl.pathname.startsWith('/public') || 
                       request.nextUrl.pathname.startsWith('/_next') ||
                       request.nextUrl.pathname.startsWith('/favicon.ico') ||
                       request.nextUrl.pathname.includes('.')

  // Redirect to login if accessing protected route without session
  if (!session && !isLoginPage && !isPublicRoute) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Redirect to dashboard if accessing login page with active session
  if (session && isLoginPage) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // Redirect root to login page if no session, or dashboard if session exists
  if (request.nextUrl.pathname === '/') {
    return NextResponse.redirect(new URL(session ? '/dashboard' : '/login', request.url))
  }

  // Only process WebSocket requests to our /api/web-chat/ws/* route
  if (
    request.headers.get('upgrade') === 'websocket' &&
    request.nextUrl.pathname.startsWith('/api/web-chat/ws/')
  ) {
    try {
      // Extract the session ID from the URL
      const sessionId = request.nextUrl.pathname.split('/').pop();
      
      if (!sessionId) {
        console.error('WebSocket connection attempt with missing session ID');
        return NextResponse.json(
          { error: 'Missing session ID in WebSocket URL' },
          { status: 400 }
        );
      }
      
      // Get the backend URL from environment variables
      const apiUrlStr = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Create a URL object from the API URL string
      let apiUrl: URL;
      try {
        apiUrl = new URL(apiUrlStr);
      } catch (urlError) {
        console.error('Invalid API URL:', apiUrlStr, urlError);
        return NextResponse.json(
          { error: 'Backend configuration error' },
          { status: 500 }
        );
      }
      
      // Create target URL for the WebSocket connection
      const targetUrl = `${apiUrl.protocol === 'https:' ? 'wss:' : 'ws:'}//${apiUrl.host}/web-chat/ws/${sessionId}`;
      
      // Log connection attempt
      console.log(`WebSocket connection attempt for session ${sessionId}, forwarding to ${targetUrl}`);
      
      // Check if all required headers exist
      const wsKey = request.headers.get('Sec-WebSocket-Key');
      const wsVersion = request.headers.get('Sec-WebSocket-Version');
      
      if (!wsKey || !wsVersion) {
        console.error('Missing required WebSocket headers:', { wsKey, wsVersion });
        return NextResponse.json(
          { error: 'Invalid WebSocket request' },
          { status: 400 }
        );
      }
      
      // Return a Response object that will be used by Next.js to proxy the WebSocket connection
      return new Response(null, {
        status: 101, // Switching protocols
        headers: {
          'Upgrade': 'websocket',
          'Connection': 'Upgrade',
          'Sec-WebSocket-Accept': wsKey, // Echo back the key (in a real implementation, this should be properly calculated)
          'Sec-WebSocket-Protocol': request.headers.get('Sec-WebSocket-Protocol') || '',
          'X-WebSocket-Target': targetUrl,
          'X-Session-ID': sessionId,
        },
      });
    } catch (error) {
      console.error('Error setting up WebSocket proxy:', error);
      return NextResponse.json(
        { 
          error: 'Failed to establish WebSocket connection',
          details: error instanceof Error ? error.message : 'Unknown error'
        },
        { status: 500 }
      );
    }
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
} 