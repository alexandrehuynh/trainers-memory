/**
 * API URL utilities to ensure consistent API path handling
 */

/**
 * Validate required environment variables and log warnings
 */
function validateEnvironmentVariables() {
  // Check backend URL
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  if (!backendUrl) {
    console.error('NEXT_PUBLIC_BACKEND_URL is not set in environment variables!');
    console.warn('Using fallback URL: https://trainers-memory.onrender.com');
  }
  
  // Check API key
  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  if (!apiKey) {
    console.error('NEXT_PUBLIC_API_KEY is not set in environment variables!');
    if (process.env.NODE_ENV === 'production') {
      console.error('This will cause authentication failures in production!');
    } else {
      console.warn('Using fallback test key in development. This will not work in production.');
    }
  }
}

// Call validation on module load
validateEnvironmentVariables();

/**
 * Get the base API URL with the correct path prefix
 */
export function getBaseApiUrl(): string {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://trainers-memory.onrender.com';
  // API path prefix should be empty as we're now using the full path with version in individual API calls
  const pathPrefix = process.env.NEXT_PUBLIC_API_PATH_PREFIX || '';
  
  // Remove trailing slash from backend URL if present
  const cleanBackendUrl = backendUrl.endsWith('/') 
    ? backendUrl.slice(0, -1) 
    : backendUrl;
  
  const baseApiUrl = `${cleanBackendUrl}${pathPrefix}`;
  
  // Log for debugging - only in development
  if (process.env.NODE_ENV !== 'production') {
    console.log(`API Base URL: ${baseApiUrl}`);
  }
    
  return baseApiUrl;
}

/**
 * Generate a complete API endpoint URL
 * 
 * @param endpoint - The API endpoint path (e.g., "/api/v1/auth/user")
 * @returns Complete API URL
 */
export function getApiUrl(endpoint: string): string {
  const baseUrl = getBaseApiUrl();
  
  // Ensure endpoint starts with a slash
  const cleanEndpoint = endpoint.startsWith('/') 
    ? endpoint 
    : `/${endpoint}`;
  
  const fullUrl = `${baseUrl}${cleanEndpoint}`;
  
  // Validate URL format
  try {
    new URL(fullUrl);
  } catch (error) {
    console.error(`Invalid API URL generated: ${fullUrl}`, error);
  }
    
  return fullUrl;
} 