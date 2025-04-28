import { NextRequest, NextResponse } from 'next/server';
import { FORCE_REAL_DATA } from '@/lib/config';
import fs from 'fs';
import path from 'path';

/**
 * GET handler for system info
 * This helps with debugging deployment environment issues
 */
export async function GET(request: NextRequest) {
  console.log('API called: GET /api/systeminfo');
  
  try {
    const nodeEnv = process.env.NODE_ENV || 'unknown';
    const hasSupabaseUrl = !!process.env.NEXT_PUBLIC_SUPABASE_URL;
    const hasSupabaseKey = !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    const forceRealData = FORCE_REAL_DATA;
    const vercelEnv = process.env.VERCEL_ENV || 'not-vercel';
    
    // Try to read version from file
    let version = process.env.APP_VERSION || 'unknown';
    try {
      // Try to find .version file in various locations
      const possiblePaths = [
        './.version',
        '../.version',
        '../../.version',
        '../../../.version',
        '../../../../.version'
      ];
      
      for (const versionPath of possiblePaths) {
        try {
          if (fs.existsSync(versionPath)) {
            const versionContent = fs.readFileSync(versionPath, 'utf8').trim();
            if (versionContent) {
              version = versionContent;
              break;
            }
          }
        } catch (e) {
          // Continue to next path
        }
      }
    } catch (versionErr) {
      console.error('Error reading version file:', versionErr);
    }
    
    return NextResponse.json({
      environment: nodeEnv,
      deployment: vercelEnv,
      database: {
        hasSupabaseUrl,
        hasSupabaseKey
      },
      config: {
        forceRealData
      },
      version,
      timestamp: new Date().toISOString(),
      serverTime: new Date().toString()
    });
  } catch (error) {
    console.error('Error getting system info:', error);
    return NextResponse.json({
      error: 'Error getting system info: ' + (error instanceof Error ? error.message : String(error)),
      version: '1.0.128' // Fallback version
    }, { status: 500 });
  }
} 