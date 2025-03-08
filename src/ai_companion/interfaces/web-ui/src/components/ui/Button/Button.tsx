import React from 'react';
import { ButtonProps, ButtonSize, ButtonVariant } from '@/types/ui';
import { clsx } from 'clsx';

/**
 * Button Component
 * 
 * A customizable button component with different variants and sizes.
 * 
 * @param props - Button component props
 * @returns The Button component
 * 
 * @example
 * ```tsx
 * <Button variant="primary" size="medium" onClick={() => console.log('clicked')}>
 *   Click Me
 * </Button>
 * ```
 */
export const Button: React.FC<ButtonProps> = ({
  children,
  variant = ButtonVariant.PRIMARY,
  size = ButtonSize.MEDIUM,
  disabled = false,
  loading = false,
  type = 'button',
  className = '',
  onClick,
  ...rest
}) => {
  // Determine button classes based on props
  const buttonClasses = clsx(
    'btn',
    `btn-${variant.toLowerCase()}`,
    `btn-${size.toLowerCase()}`,
    {
      'opacity-70 cursor-not-allowed': disabled,
      'relative': loading,
    },
    className
  );

  // Handle button click
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) return;
    onClick?.(e);
  };

  return (
    <button
      type={type}
      className={buttonClasses}
      onClick={handleClick}
      disabled={disabled || loading}
      aria-busy={loading ? 'true' : 'false'}
      {...rest}
    >
      {loading && (
        <span 
          className="inline-block mr-2 animate-spin" 
          data-testid="button-spinner"
        >
          ⟳
        </span>
      )}
      {children}
    </button>
  );
}; 