/**
 * API Types
 * Contains types for API request and response payloads
 */

/**
 * Base API Response structure
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
}

/**
 * Pagination parameters for API requests
 */
export interface PaginationParams {
  page: number;
  limit: number;
}

/**
 * Pagination metadata in API responses
 */
export interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

/**
 * Paginated API response
 */
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  meta?: PaginationMeta;
} 