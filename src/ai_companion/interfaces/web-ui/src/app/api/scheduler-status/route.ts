import { NextRequest, NextResponse } from 'next/server';
import { FORCE_REAL_DATA } from '@/lib/config';

/**
 * GET handler for scheduler status check
 */
export async function GET(request: NextRequest) {
  console.log('API called: GET /api/scheduler-status');
  
  try {
    // In production with forced real data, always return running state
    if (FORCE_REAL_DATA) {
      console.log('Force real data enabled - returning scheduler as running');
      return NextResponse.json({
        status: 'running',
        lastChecked: new Date().toISOString(),
        forced: true
      });
    }
    
    // In development, try to check actual scheduler status
    // This would typically connect to your backend or database to check
    
    // For now, we're assuming it's running (replace with actual check in future)
    const isRunning = true; 
    
    if (isRunning) {
      return NextResponse.json({
        status: 'running',
        lastChecked: new Date().toISOString()
      });
    } else {
      return NextResponse.json({
        status: 'stopped',
        lastChecked: new Date().toISOString()
      });
    }
  } catch (error) {
    console.error('Error checking scheduler status:', error);
    
    // In production with forced real data, return as running even on error
    if (FORCE_REAL_DATA) {
      return NextResponse.json({
        status: 'running',
        lastChecked: new Date().toISOString(),
        forced: true
      });
    }
    
    return NextResponse.json({
      status: 'unknown',
      error: 'Error checking scheduler status: ' + (error instanceof Error ? error.message : String(error)),
      lastChecked: new Date().toISOString()
    }, { status: 500 });
  }
} 