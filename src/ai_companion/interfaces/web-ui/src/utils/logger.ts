/**
 * Logger utility for application-wide logging
 * Features:
 * - Multiple log levels (debug, info, warn, error)
 * - Environment-based logging control
 * - Support for console and remote logging
 * - Context and metadata support
 */

// Log levels in order of severity
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

// Configuration interface for the logger
interface LoggerConfig {
  minLevel: LogLevel;
  enableConsole: boolean;
  enableRemote: boolean;
  remoteLogEndpoint?: string;
  includeTimestamps: boolean;
  applicationName: string;
}

// Default configuration
const DEFAULT_CONFIG: LoggerConfig = {
  minLevel: process.env.NODE_ENV === 'production' ? LogLevel.INFO : LogLevel.DEBUG,
  enableConsole: true,
  enableRemote: process.env.NODE_ENV === 'production',
  remoteLogEndpoint: process.env.NEXT_PUBLIC_LOG_ENDPOINT,
  includeTimestamps: true,
  applicationName: 'evelina-ai',
};

// Current configuration (can be updated at runtime)
let currentConfig: LoggerConfig = { ...DEFAULT_CONFIG };

// Color codes for console logs
const COLORS = {
  [LogLevel.DEBUG]: '\x1b[36m', // Cyan
  [LogLevel.INFO]: '\x1b[32m',  // Green
  [LogLevel.WARN]: '\x1b[33m',  // Yellow
  [LogLevel.ERROR]: '\x1b[31m', // Red
  reset: '\x1b[0m',             // Reset
};

// Stringified level names
const LEVEL_NAMES = {
  [LogLevel.DEBUG]: 'DEBUG',
  [LogLevel.INFO]: 'INFO',
  [LogLevel.WARN]: 'WARN',
  [LogLevel.ERROR]: 'ERROR',
};

/**
 * Updates the logger configuration
 * @param config Configuration options to update
 */
export function configureLogger(config: Partial<LoggerConfig>): void {
  currentConfig = { ...currentConfig, ...config };
}

/**
 * Checks if logging is enabled for a given level
 * @param level The log level to check
 * @returns Boolean indicating if this level should be logged
 */
function isLevelEnabled(level: LogLevel): boolean {
  return level >= currentConfig.minLevel;
}

/**
 * Formats a log message
 * @param level Log level
 * @param message Main log message
 * @param context Additional contextual information
 * @returns Formatted log message
 */
function formatLogMessage(level: LogLevel, message: string, context?: Record<string, any>): string {
  const parts = [];
  
  // Add timestamp if enabled
  if (currentConfig.includeTimestamps) {
    parts.push(`[${new Date().toISOString()}]`);
  }
  
  // Add app name
  parts.push(`[${currentConfig.applicationName}]`);
  
  // Add log level
  parts.push(`[${LEVEL_NAMES[level]}]`);
  
  // Add message
  parts.push(message);
  
  // Add context if provided
  if (context && Object.keys(context).length > 0) {
    try {
      parts.push('Context:', JSON.stringify(context, null, 2));
    } catch (error) {
      parts.push('Context: [Unstringifiable Object]');
    }
  }
  
  return parts.join(' ');
}

/**
 * Logs to the console with color
 * @param level Log level
 * @param message Log message
 * @param formattedMessage Formatted log message
 */
function logToConsole(level: LogLevel, message: string, formattedMessage: string): void {
  if (!currentConfig.enableConsole) return;
  
  const color = COLORS[level];
  const resetColor = COLORS.reset;
  
  switch (level) {
    case LogLevel.DEBUG:
      console.debug(`${color}${formattedMessage}${resetColor}`);
      break;
    case LogLevel.INFO:
      console.info(`${color}${formattedMessage}${resetColor}`);
      break;
    case LogLevel.WARN:
      console.warn(`${color}${formattedMessage}${resetColor}`);
      break;
    case LogLevel.ERROR:
      console.error(`${color}${formattedMessage}${resetColor}`);
      break;
  }
}

/**
 * Sends logs to a remote logging service
 * @param level Log level
 * @param message Log message
 * @param context Additional contextual information
 */
async function logToRemote(level: LogLevel, message: string, context?: Record<string, any>): Promise<void> {
  if (!currentConfig.enableRemote || !currentConfig.remoteLogEndpoint) return;
  
  try {
    const payload = {
      level: LEVEL_NAMES[level],
      message,
      context,
      timestamp: new Date().toISOString(),
      application: currentConfig.applicationName,
      environment: process.env.NODE_ENV || 'development',
      // Add user information if available (from auth context)
      user: typeof window !== 'undefined' && window.localStorage?.getItem('user')
        ? JSON.parse(window.localStorage.getItem('user') || '{}')?.id
        : 'unknown',
    };
    
    // Fire and forget - don't await the response
    fetch(currentConfig.remoteLogEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      // Use keepalive to ensure logs are sent even if page is unloading
      keepalive: true,
    }).catch(() => {
      // Silently fail on remote logging errors
      // We don't want remote logging to break the application
    });
  } catch (error) {
    // If remote logging fails, fallback to console if possible
    if (currentConfig.enableConsole) {
      console.error('Failed to send log to remote endpoint:', error);
    }
  }
}

/**
 * Log a debug message
 * @param message Log message
 * @param context Additional contextual information
 */
export function debug(message: string, context?: Record<string, any>): void {
  if (!isLevelEnabled(LogLevel.DEBUG)) return;
  
  const formattedMessage = formatLogMessage(LogLevel.DEBUG, message, context);
  logToConsole(LogLevel.DEBUG, message, formattedMessage);
  logToRemote(LogLevel.DEBUG, message, context);
}

/**
 * Log an info message
 * @param message Log message
 * @param context Additional contextual information
 */
export function info(message: string, context?: Record<string, any>): void {
  if (!isLevelEnabled(LogLevel.INFO)) return;
  
  const formattedMessage = formatLogMessage(LogLevel.INFO, message, context);
  logToConsole(LogLevel.INFO, message, formattedMessage);
  logToRemote(LogLevel.INFO, message, context);
}

/**
 * Log a warning message
 * @param message Log message
 * @param context Additional contextual information
 */
export function warn(message: string, context?: Record<string, any>): void {
  if (!isLevelEnabled(LogLevel.WARN)) return;
  
  const formattedMessage = formatLogMessage(LogLevel.WARN, message, context);
  logToConsole(LogLevel.WARN, message, formattedMessage);
  logToRemote(LogLevel.WARN, message, context);
}

/**
 * Log an error message
 * @param message Log message
 * @param error Error object
 * @param context Additional contextual information
 */
export function error(message: string, error?: Error | unknown, context?: Record<string, any>): void {
  if (!isLevelEnabled(LogLevel.ERROR)) return;
  
  // Extract error information
  const errorContext = error ? {
    ...context,
    error: {
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      name: error instanceof Error ? error.name : 'Unknown Error',
    },
  } : context;
  
  const formattedMessage = formatLogMessage(LogLevel.ERROR, message, errorContext);
  logToConsole(LogLevel.ERROR, message, formattedMessage);
  logToRemote(LogLevel.ERROR, message, errorContext);
}

/**
 * Log method execution with timing information
 * @param methodName Name of the method being logged
 * @param callback Method to execute and log
 * @returns The result of the callback
 */
export async function logMethodExecution<T>(methodName: string, callback: () => Promise<T> | T): Promise<T> {
  const startTime = performance.now();
  try {
    const result = await callback();
    const endTime = performance.now();
    debug(`Method ${methodName} executed in ${(endTime - startTime).toFixed(2)}ms`);
    return result;
  } catch (err) {
    const endTime = performance.now();
    error(`Method ${methodName} failed after ${(endTime - startTime).toFixed(2)}ms`, err);
    throw err;
  }
}

// Create a default logger object with all methods
const logger = {
  debug,
  info,
  warn,
  error,
  logMethodExecution,
  configureLogger,
};

export default logger; 