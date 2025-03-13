import { NextResponse } from 'next/server';

/**
 * Debug API route - minimal version
 */
export async function GET() {
  try {
    const envVars = {
      NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL ? 'Set' : 'Not set',
      NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Not set',
      SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY ? 'Set' : 'Not set',
    };
    
    return NextResponse.json({
      status: 'success',
      message: 'Debug API endpoint is working',
      envVars
    });
  } catch (error: any) {
    return NextResponse.json({
      status: 'error',
      message: 'An unexpected error occurred',
      error: error.message
    }, { status: 500 });
  }
} 