/**
 * API URL utilities to ensure consistent API path handling
 */

/**
 * Get the base API URL with the correct path prefix
 */
export function getBaseApiUrl(): string {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://trainers-memory.onrender.com';
  const pathPrefix = process.env.NEXT_PUBLIC_API_PATH_PREFIX || '';
  
  // Remove trailing slash from backend URL if present
  const cleanBackendUrl = backendUrl.endsWith('/') 
    ? backendUrl.slice(0, -1) 
    : backendUrl;
    
  return `${cleanBackendUrl}${pathPrefix}`;
}

/**
 * Generate a complete API endpoint URL
 * 
 * @param endpoint - The API endpoint path (e.g., "/auth/user")
 * @returns Complete API URL
 */
export function getApiUrl(endpoint: string): string {
  const baseUrl = getBaseApiUrl();
  
  // Ensure endpoint starts with a slash
  const cleanEndpoint = endpoint.startsWith('/') 
    ? endpoint 
    : `/${endpoint}`;
    
  return `${baseUrl}${cleanEndpoint}`;
} 