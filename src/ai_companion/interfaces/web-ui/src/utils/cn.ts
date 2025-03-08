import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines multiple class names using clsx and optimizes them with tailwind-merge
 * to handle class conflicts properly
 * 
 * @example
 * // Basic usage
 * cn('text-red-500', 'bg-blue-500')
 * 
 * @example
 * // With conditional classes
 * cn('text-lg', isLarge && 'font-bold', { 'opacity-50': isDisabled })
 * 
 * @param inputs - Class names or conditional class expressions
 * @returns Merged and optimized className string
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
} 