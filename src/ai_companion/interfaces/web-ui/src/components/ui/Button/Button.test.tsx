import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from './Button';
import { ButtonVariant, ButtonSize } from '@/types/ui';

describe('Button Component', () => {
  it('renders correctly with default props', () => {
    render(<Button>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('btn-primary');
    expect(button).toHaveClass('btn-medium');
    expect(button).not.toBeDisabled();
  });

  it('applies the correct variant class', () => {
    render(
      <Button variant={ButtonVariant.SECONDARY}>Secondary Button</Button>
    );
    
    const button = screen.getByRole('button', { name: /secondary button/i });
    expect(button).toHaveClass('btn-secondary');
  });

  it('applies the correct size class', () => {
    render(
      <Button size={ButtonSize.LARGE}>Large Button</Button>
    );
    
    const button = screen.getByRole('button', { name: /large button/i });
    expect(button).toHaveClass('btn-large');
  });

  it('handles disabled state correctly', () => {
    render(<Button disabled>Disabled Button</Button>);
    
    const button = screen.getByRole('button', { name: /disabled button/i });
    expect(button).toBeDisabled();
  });

  it('shows loading state correctly', () => {
    render(<Button loading>Loading Button</Button>);
    
    const button = screen.getByRole('button', { name: /loading button/i });
    expect(button).toHaveAttribute('aria-busy', 'true');
    
    // Check if spinner is rendered
    const spinner = screen.getByTestId('button-spinner');
    expect(spinner).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled', () => {
    const handleClick = jest.fn();
    
    render(<Button onClick={handleClick} disabled>Disabled button</Button>);
    
    const button = screen.getByRole('button', { name: /disabled button/i });
    fireEvent.click(button);
    
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies custom className correctly', () => {
    render(<Button className="custom-class">Custom Button</Button>);
    
    const button = screen.getByRole('button', { name: /custom button/i });
    expect(button).toHaveClass('custom-class');
  });
}); 