# Component Standards

## Component Structure

All components should follow this structure:

```tsx
// Import statements
import { useState, useEffect } from 'react';
import { cn } from '@/src/utils/cn';

// Type definitions
interface ExampleComponentProps {
  /** Description of the prop */
  prop1: string;
  /** Description of the prop */
  prop2?: number;
  /** Description of the prop */
  onAction?: (arg: string) => void;
}

/**
 * ExampleComponent - Brief description of what this component does
 * 
 * @example
 * <ExampleComponent 
 *   prop1="value"
 *   prop2={123}
 *   onAction={(value) => console.log(value)}
 * />
 */
export const ExampleComponent = ({
  prop1,
  prop2,
  onAction,
}: ExampleComponentProps) => {
  // State definitions
  const [state, setState] = useState<string>('');

  // Effects
  useEffect(() => {
    // Logic here
  }, []);

  // Event handlers
  const handleClick = () => {
    if (onAction) {
      onAction(state);
    }
  };

  // Render
  return (
    <div className={cn('base-styles', 'conditional-styles')}>
      <button 
        onClick={handleClick}
        aria-label="Descriptive action name"
        className="button-styles"
      >
        {prop1}
      </button>
    </div>
  );
};
```

## Naming Conventions

1. **Components**: PascalCase (e.g., `ButtonPrimary.tsx`)
2. **Files**: PascalCase for components, camelCase for utilities
3. **Functions**: camelCase with descriptive names
4. **Event Handlers**: Start with `handle` prefix (e.g., `handleClick`)
5. **Props**: camelCase with descriptive names
6. **Interfaces**: PascalCase with suffix describing purpose (e.g., `ButtonProps`)

## Styling Guidelines

1. Use TailwindCSS utility classes with the `cn` helper for conditional classes
2. Keep styling close to the component using the className attribute
3. Use MUI components with custom styling using the sx prop or styled API
4. Maintain a consistent color palette defined in the theme

## Accessibility Guidelines

1. All interactive elements must be keyboard accessible
2. Include proper ARIA attributes (`aria-label`, `aria-expanded`, etc.)
3. Maintain proper contrast ratios for text
4. Ensure proper tab order with tabIndex
5. Add focus styles for keyboard users

## Component Documentation

All components should include:

1. Interface with JSDoc comments for each prop
2. Component JSDoc comment with description
3. Usage example in the component JSDoc
4. Edge cases and limitations documented

## Testing Guidelines

1. Test component rendering with basic props
2. Test user interactions (clicks, inputs, etc.)
3. Test accessibility features
4. Test edge cases and error states 