# Testing Strategy

## Overview

This document outlines our testing approach for the web-ui frontend. We use a combination of unit, integration, and end-to-end tests to ensure the quality and reliability of the application.

## Testing Stack

- **Jest**: Testing framework for running tests
- **React Testing Library**: For testing React components
- **MSW (Mock Service Worker)**: For API mocking
- **Cypress**: For end-to-end testing

## Directory Structure

```
src/
├── __tests__/                          # Tests using the same directory structure as the source
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.test.tsx      # Unit tests for LoginForm
│   │   ├── ui/
│   │   │   ├── Button.test.tsx         # Unit tests for Button component
│   ├── hooks/
│   │   ├── useAuth.test.ts             # Tests for authentication hooks
│   ├── pages/
│   │   ├── login.test.tsx              # Integration tests for login page
│   ├── utils/
│   │   ├── format.test.ts              # Tests for utility functions
├── __mocks__/                          # Mock data and services
│   ├── auth.ts                         # Auth service mocks
│   ├── data.ts                         # Mock data
├── cypress/                            # End-to-end tests
│   ├── e2e/
│   │   ├── login.cy.ts                 # E2E test for login flow
```

## Unit Testing

Unit tests focus on testing individual components or functions in isolation:

```tsx
// __tests__/components/ui/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/src/components/ui/Button';

describe('Button Component', () => {
  it('renders correctly with default props', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-primary-main');
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('can be disabled', () => {
    render(<Button disabled>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeDisabled();
  });

  it('renders with different variants', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    let button = screen.getByRole('button', { name: /primary/i });
    expect(button).toHaveClass('bg-primary-main');
    
    rerender(<Button variant="secondary">Secondary</Button>);
    button = screen.getByRole('button', { name: /secondary/i });
    expect(button).toHaveClass('bg-secondary-main');
    
    rerender(<Button variant="outlined">Outlined</Button>);
    button = screen.getByRole('button', { name: /outlined/i });
    expect(button).toHaveClass('border-2');
  });
});
```

## Integration Testing

Integration tests verify that multiple components work together correctly:

```tsx
// __tests__/pages/login.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import LoginPage from '@/src/app/login/page';
import { AppProviders } from '@/src/components/providers/AppProviders';

// Mock the Supabase client
jest.mock('@/src/lib/supabase/client', () => ({
  getSupabaseClient: () => ({
    auth: {
      signInWithPassword: jest.fn().mockImplementation(async ({ email, password }) => {
        if (email === 'user@example.com' && password === 'password') {
          return { data: { user: { id: '123' } }, error: null };
        }
        return { data: null, error: { message: 'Invalid credentials' } };
      }),
    },
  }),
}));

describe('Login Page', () => {
  it('renders login form', () => {
    render(
      <AppProviders>
        <LoginPage />
      </AppProviders>
    );
    
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows error message for invalid credentials', async () => {
    render(
      <AppProviders>
        <LoginPage />
      </AppProviders>
    );
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'wrong@example.com' },
    });
    
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrongpassword' },
    });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('redirects after successful login', async () => {
    const mockRouter = { push: jest.fn() };
    jest.mock('next/navigation', () => ({
      useRouter: () => mockRouter,
    }));
    
    render(
      <AppProviders>
        <LoginPage />
      </AppProviders>
    );
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'user@example.com' },
    });
    
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password' },
    });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith('/dashboard');
    });
  });
});
```

## API Mocking

We use MSW to mock API calls during testing:

```typescript
// __mocks__/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/user', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: '123',
        name: 'Test User',
        email: 'user@example.com',
      })
    );
  }),
  
  rest.post('/api/auth/login', (req, res, ctx) => {
    const { email, password } = req.body as { email: string; password: string };
    
    if (email === 'user@example.com' && password === 'password') {
      return res(
        ctx.status(200),
        ctx.json({
          token: 'fake-token-123',
          user: {
            id: '123',
            name: 'Test User',
            email: 'user@example.com',
          },
        })
      );
    }
    
    return res(
      ctx.status(401),
      ctx.json({
        message: 'Invalid credentials',
      })
    );
  }),
];
```

## End-to-End Testing

Cypress tests for full end-to-end flows:

```typescript
// cypress/e2e/login.cy.ts
describe('Login Page', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('displays login form', () => {
    cy.get('h1').should('contain', 'Sign In');
    cy.get('input[name="email"]').should('exist');
    cy.get('input[name="password"]').should('exist');
    cy.get('button').contains('Sign In').should('exist');
  });

  it('shows error for invalid credentials', () => {
    cy.get('input[name="email"]').type('wrong@example.com');
    cy.get('input[name="password"]').type('wrongpassword');
    cy.get('button').contains('Sign In').click();
    
    cy.get('[data-testid="error-message"]').should('be.visible');
    cy.get('[data-testid="error-message"]').should('contain', 'Invalid credentials');
  });

  it('redirects after successful login', () => {
    // Intercept the login API call
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        token: 'fake-token-123',
        user: {
          id: '123',
          name: 'Test User',
          email: 'user@example.com',
        },
      },
    }).as('loginRequest');
    
    cy.get('input[name="email"]').type('user@example.com');
    cy.get('input[name="password"]').type('password');
    cy.get('button').contains('Sign In').click();
    
    cy.wait('@loginRequest');
    cy.url().should('include', '/dashboard');
  });
});
```

## Testing Custom Hooks

Testing hooks with React Testing Library:

```typescript
// __tests__/hooks/useAuth.test.ts
import { renderHook, act } from '@testing-library/react-hooks';
import { AuthProvider } from '@/src/store/auth/AuthContext';
import { useAuth } from '@/src/store/hooks';

// Mock the Supabase client
jest.mock('@/src/lib/supabase/client', () => ({
  getSupabaseClient: () => ({
    auth: {
      getSession: jest.fn().mockResolvedValue({
        data: { session: null },
        error: null,
      }),
      onAuthStateChange: jest.fn().mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } },
      }),
    },
  }),
}));

describe('useAuth hook', () => {
  it('provides the current auth state', async () => {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
    
    // Initial state
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    
    await waitForNextUpdate();
    
    // After initialization
    expect(result.current.isLoading).toBe(false);
  });

  it('updates auth state when user is set', async () => {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
    
    await waitForNextUpdate();
    
    act(() => {
      result.current.setUser({
        id: '123',
        email: 'user@example.com',
      });
    });
    
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({
      id: '123',
      email: 'user@example.com',
    });
    
    act(() => {
      result.current.logout();
    });
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
  });
});
```

## Test Coverage Requirements

- **Unit Tests**: 
  - All components should have unit tests
  - All utility functions should have unit tests
  - Coverage goal: 80%+

- **Integration Tests**:
  - All pages should have integration tests
  - All major user flows should be covered
  - Coverage goal: 70%+

- **End-to-End Tests**:
  - All critical user journeys should be covered
  - Focus on happy paths and common error cases

## Running Tests

```bash
# Run unit and integration tests
npm test

# Run with coverage
npm test -- --coverage

# Run a specific test file
npm test -- components/Button.test.tsx

# Run end-to-end tests
npm run cypress

# Run end-to-end tests in headless mode
npm run cypress:headless
```

## CI/CD Integration

Tests are automatically run in our CI/CD pipeline:

1. **Pull Request**: All tests must pass before merging
2. **Coverage Report**: Coverage reports are generated and reviewed
3. **Deploy Preview**: E2E tests run against deploy previews
4. **Production**: Final verification E2E tests run against production 