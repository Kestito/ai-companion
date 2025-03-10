import React, { useEffect } from 'react';
import { useLogger } from '@/hooks/useLogger';

interface WithLoggingOptions {
  logProps?: boolean;
  logLifecycle?: boolean;
  logRenders?: boolean;
}

/**
 * Higher-order component that adds logging capabilities to any component
 * @param WrappedComponent The component to wrap with logging
 * @param options Logging configuration options
 * @returns The wrapped component with logging
 */
export function withLogging<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: WithLoggingOptions = {
    logProps: true,
    logLifecycle: true,
    logRenders: true,
  }
) {
  // Get the display name for the component
  const componentName = WrappedComponent.displayName || WrappedComponent.name || 'Component';
  
  // Create the wrapped component
  const WithLoggingComponent = (props: P) => {
    const logger = useLogger({ component: componentName });
    
    // Log component mounting
    useEffect(() => {
      if (options.logLifecycle) {
        logger.debug('Component mounted', options.logProps ? { props } : undefined);
      }
      
      return () => {
        if (options.logLifecycle) {
          logger.debug('Component will unmount');
        }
      };
    }, []);
    
    // Log prop changes
    useEffect(() => {
      if (options.logProps) {
        logger.debug('Props updated', { props });
      }
    }, [props]);
    
    // Log render
    if (options.logRenders) {
      logger.debug('Component rendering');
    }
    
    // Wrap the component with error boundary logging
    try {
      return <WrappedComponent {...props} />;
    } catch (error) {
      logger.error('Error in component', error as Error);
      throw error;
    }
  };
  
  // Set display name for debugging
  WithLoggingComponent.displayName = `withLogging(${componentName})`;
  
  return WithLoggingComponent;
}

// Example usage:
// const MyComponentWithLogging = withLogging(MyComponent, {
//   logProps: true,
//   logLifecycle: true,
//   logRenders: true,
// }); 