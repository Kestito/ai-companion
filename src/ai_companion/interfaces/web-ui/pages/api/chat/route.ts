import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const authHeader = request.headers.get('Authorization')
  if (authHeader !== `Bearer ${process.env.SUPABASE_SERVICE_KEY}`) {
    return new NextResponse('Unauthorized', { status: 401 })
  }
  
  // Process request
} 