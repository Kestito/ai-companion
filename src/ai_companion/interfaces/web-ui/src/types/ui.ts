/**
 * UI Types
 * Contains types for UI components
 */

import { ReactNode } from 'react';

/**
 * Base props for all components
 */
export interface BaseComponentProps {
  className?: string;
  id?: string;
  testId?: string;
}

/**
 * Props for components that can have children
 */
export interface WithChildrenProps {
  children: ReactNode;
}

/**
 * Button variants
 */
export enum ButtonVariant {
  PRIMARY = 'primary',
  SECONDARY = 'secondary',
  GHOST = 'ghost',
  OUTLINE = 'outline',
  LINK = 'link',
  DANGER = 'danger',
}

/**
 * Button sizes
 */
export enum ButtonSize {
  SMALL = 'small',
  MEDIUM = 'medium',
  LARGE = 'large',
}

/**
 * Common button props
 */
export interface ButtonProps extends BaseComponentProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit' | 'reset';
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  children: ReactNode;
}

/**
 * Input types
 */
export interface InputProps extends BaseComponentProps {
  label?: string;
  placeholder?: string;
  type?: string;
  value?: string;
  name?: string;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
}

/**
 * Card components
 */
export interface CardProps extends BaseComponentProps, WithChildrenProps {
  title?: string;
  elevation?: number;
  bordered?: boolean;
} 