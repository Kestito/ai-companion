import { Component, ErrorInfo, ReactNode } from 'react'
import { Alert, Box } from '@mui/material'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <Box p={4}>
          <Alert severity="error">
            {this.state.error?.message || 'Something went wrong'}
          </Alert>
        </Box>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary 