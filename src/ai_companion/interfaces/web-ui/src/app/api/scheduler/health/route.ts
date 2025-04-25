import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Helper function to get the API URL
const getApiUrl = () => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return apiUrl.endsWith('/') ? apiUrl : `${apiUrl}/`;
};

// Custom fetch with timeout
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeout = 5000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

// Check scheduler health through direct API endpoint
async function checkDirectHealth() {
  try {
    const apiUrl = getApiUrl();
    const response = await fetchWithTimeout(`${apiUrl}monitor/health/telegram-scheduler-status`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      return {
        isRunning: false,
        source: 'direct',
        error: `Failed with status ${response.status}`,
        lastChecked: new Date().toISOString()
      };
    }
    
    const data = await response.json();
    return {
      isRunning: data.status === 'running',
      source: 'direct',
      message: data.message || '',
      lastRun: data.last_run,
      pendingMessages: data.pending_messages,
      lastChecked: new Date().toISOString()
    };
  } catch (error) {
    return {
      isRunning: false,
      source: 'direct',
      error: error instanceof Error ? error.message : String(error),
      lastChecked: new Date().toISOString()
    };
  }
}

// Check scheduler health through MCP
async function checkMcpHealth() {
  try {
    const response = await fetchWithTimeout('/api/mcp/scheduler-status', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      return {
        isRunning: false,
        source: 'mcp',
        error: `Failed with status ${response.status}`,
        lastChecked: new Date().toISOString()
      };
    }
    
    const data = await response.json();
    return {
      isRunning: data.isRunning,
      source: 'mcp',
      message: data.message || '',
      lastRun: data.lastRun,
      pendingMessages: data.pendingMessages,
      lastChecked: new Date().toISOString()
    };
  } catch (error) {
    return {
      isRunning: false,
      source: 'mcp',
      error: error instanceof Error ? error.message : String(error),
      lastChecked: new Date().toISOString()
    };
  }
}

// Check scheduler health through database activity
async function checkDatabaseHealth() {
  try {
    const apiUrl = getApiUrl();
    const response = await fetchWithTimeout(`${apiUrl}monitor/database/scheduler-status`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      return {
        isRunning: false,
        source: 'database',
        error: `Failed with status ${response.status}`,
        lastChecked: new Date().toISOString()
      };
    }
    
    const data = await response.json();
    return {
      isRunning: data.activeInLast10Minutes,
      source: 'database',
      message: data.activeInLast10Minutes ? 'Scheduler appears active based on database activity' : 'No recent scheduler activity in database',
      lastRun: data.lastRun,
      pendingMessages: data.pendingCount,
      lastChecked: new Date().toISOString()
    };
  } catch (error) {
    return {
      isRunning: false,
      source: 'database',
      error: error instanceof Error ? error.message : String(error),
      lastChecked: new Date().toISOString()
    };
  }
}

// Create a direct client here to avoid "use server" directive issues
const createSupabaseClient = async () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Missing Supabase credentials');
  }
  
  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false
    }
  });
};

// GET /api/scheduler/health
export async function GET(request: NextRequest) {
  try {
    const supabase = await createSupabaseClient();
    
    // Check if we can connect to the database by running a simple query
    const { data, error } = await supabase
      .from('scheduled_messages')
      .select('count(*)', { count: 'exact', head: true });
    
    if (error) {
      console.error('Error checking database connection:', error);
      return NextResponse.json({
        isRunning: false,
        message: `Database connection error: ${error.message}`,
        source: 'database',
        detail: error
      }, { status: 500 });
    }
    
    // Get latest message to use as lastRun timestamp
    const { data: latestMessage, error: latestError } = await supabase
      .from('scheduled_messages')
      .select('scheduled_time, status')
      .eq('status', 'sent')
      .order('scheduled_time', { ascending: false })
      .limit(1)
      .single();
    
    // Get pending messages count
    const { count, error: countError } = await supabase
      .from('scheduled_messages')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'pending');
    
    return NextResponse.json({
      isRunning: true,
      message: 'Database connection successful',
      lastRun: latestMessage?.scheduled_time || null,
      pendingMessages: count || 0,
      source: 'direct-db',
      detail: null
    });
  } catch (error: any) {
    console.error('Failed to check scheduler health:', error);
    return NextResponse.json({
      isRunning: false,
      message: `Failed to check health: ${error.message}`,
      source: 'error',
      detail: error.stack
    }, { status: 500 });
  }
} 