/**
 * A simple logger hook for components
 * @param context - Context information for the logger
 * @returns Logger object with methods for different log levels
 */
export const useLogger = (context: Record<string, any> = {}) => {
  const prefix = Object.entries(context)
    .map(([key, value]) => `[${key}:${value}]`)
    .join(' ');

  return {
    debug: (message: string, ...args: any[]) => {
      if (process.env.NODE_ENV === 'development') {
        console.debug(`${prefix} ${message}`, ...args);
      }
    },
    info: (message: string, ...args: any[]) => {
      console.info(`${prefix} ${message}`, ...args);
    },
    warn: (message: string, ...args: any[]) => {
      console.warn(`${prefix} ${message}`, ...args);
    },
    error: (message: string, ...args: any[]) => {
      console.error(`${prefix} ${message}`, ...args);
    },
    logMethodExecution: async <T>(methodName: string, method: () => Promise<T>): Promise<T> => {
      const startTime = performance.now();
      try {
        const result = await method();
        const endTime = performance.now();
        console.info(`${prefix} ${methodName} executed in ${Math.round(endTime - startTime)}ms`);
        return result;
      } catch (error) {
        const endTime = performance.now();
        console.error(`${prefix} ${methodName} failed after ${Math.round(endTime - startTime)}ms`, error);
        throw error;
      }
    }
  };
}; 