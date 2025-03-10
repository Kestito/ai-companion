import React from 'react';
import { Alert, Button, Container, Typography } from '@mui/material';
import { useLogger } from '@/hooks/useLogger';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary component that catches and logs errors in the component tree
 */
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private logger = useLogger({ component: 'ErrorBoundary' });

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log the error
    this.logger.error('Uncaught error in component tree', error, {
      componentStack: errorInfo.componentStack,
    });
  }

  handleReset = (): void => {
    this.logger.info('Resetting error boundary state');
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render(): React.ReactNode {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        this.props.fallback || (
          <Container maxWidth="sm" sx={{ py: 4 }}>
            <Alert
              severity="error"
              action={
                <Button color="inherit" size="small" onClick={this.handleReset}>
                  Try Again
                </Button>
              }
            >
              <Typography variant="h6" gutterBottom>
                Something went wrong
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {this.state.error?.message || 'An unexpected error occurred'}
              </Typography>
              {process.env.NODE_ENV !== 'production' && (
                <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {this.state.error?.stack}
                </Typography>
              )}
            </Alert>
          </Container>
        )
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 