import { getJwtToken } from './tokenHelper';

const API_BASE_URL = 'http://localhost:8000/api/v1';

type RequestOptions = {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
  cache?: boolean;
  retries?: number;
  retryDelay?: number;
  skipCache?: boolean;
};

// Standard API response format
interface ApiResponse<T> {
  status: 'success' | 'error';
  message: string;
  data: T;
  timestamp: string;
  api_version: string;
}

// Simple in-memory cache
const cache: Record<string, { data: any; timestamp: number }> = {};
const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes in milliseconds

// Function to generate a cache key
const getCacheKey = (url: string, options: RequestOptions): string => {
  const method = options.method || 'GET';
  const body = options.body ? JSON.stringify(options.body) : '';
  return `${method}:${url}:${body}`;
};

// Function to check if a cache entry is valid
const isCacheValid = (cacheTimestamp: number): boolean => {
  return Date.now() - cacheTimestamp < CACHE_EXPIRY;
};

/**
 * Make an API request with caching and retry support
 */
async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getJwtToken();
  const cacheEnabled = options.cache !== false; // Cache enabled by default
  const maxRetries = options.retries || 2; // Default to 2 retries
  const retryDelay = options.retryDelay || 1000; // Default to 1 second delay between retries
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-API-Key': 'test_key_12345', // Add the test API key for all requests
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const config: RequestInit = {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  };
  
  // Check cache for GET requests
  if (cacheEnabled && config.method === 'GET' && !options.skipCache) {
    const cacheKey = getCacheKey(url, options);
    const cachedData = cache[cacheKey];
    
    if (cachedData && isCacheValid(cachedData.timestamp)) {
      console.log('Using cached data for:', endpoint);
      return cachedData.data as T;
    }
  }
  
  // Function to handle the actual fetch with retries
  const fetchWithRetry = async (retries: number): Promise<T> => {
    try {
      const response = await fetch(url, config);
      
      // Handle 401 Unauthorized (token expired)
      if (response.status === 401) {
        const refreshResult = await refreshTokenAndRetry();
        if (refreshResult) {
          return refreshResult;
        }
      }
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API error: ${response.status}`);
      }
      
      // For 204 No Content responses
      if (response.status === 204) {
        return {} as T;
      }
      
      const responseData = await response.json() as ApiResponse<T>;
      console.log('API Response:', endpoint, responseData.status);
      
      // Check if the API response indicates success
      if (responseData.status === 'success') {
        const processedData = processResponseData(endpoint, responseData.data);
        
        // Cache successful GET responses
        if (cacheEnabled && config.method === 'GET') {
          const cacheKey = getCacheKey(url, options);
          cache[cacheKey] = { 
            data: processedData, 
            timestamp: Date.now() 
          };
        }
        
        return processedData as T;
      } else {
        throw new Error(responseData.message || 'API returned an error');
      }
    } catch (error: any) {
      if (retries > 0 && !error.message?.includes('401')) {
        console.log(`Retrying API request (${retries} retries left): ${endpoint}`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        return fetchWithRetry(retries - 1);
      }
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  };
  
  // Function to try refreshing the token and retrying the request
  const refreshTokenAndRetry = async (): Promise<T | null> => {
    try {
      const refreshResult = await refreshAuthToken();
      if (refreshResult) {
        // If token refresh was successful, update the Authorization header and retry
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
          config.headers = headers;
        }
        return await fetchWithRetry(0); // Don't count this as a retry
      }
      return null;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    }
  };
  
  return fetchWithRetry(maxRetries);
}

// Helper function to process response data based on endpoint
function processResponseData(endpoint: string, data: any): any {
  // Special case handling for endpoints that return nested data structures
  if (endpoint.includes('/workouts/workouts') && data.workouts && Array.isArray(data.workouts)) {
    return data.workouts;
  }
  
  // Handle clients endpoint that returns { clients: [...] }
  if (endpoint.includes('/clients') && !endpoint.includes('/clients/') && data.clients && Array.isArray(data.clients)) {
    return data.clients;
  }
  
  return data;
}

// Helper function to refresh the auth token
async function refreshAuthToken(): Promise<boolean> {
  // Dispatch an event that our AppContent component will listen for
  try {
    const event = new CustomEvent('auth:token-refresh-needed');
    window.dispatchEvent(event);
    
    // Return true to indicate we've attempted to refresh the token
    // The actual refresh happens asynchronously via the event listener
    return true;
  } catch (error) {
    console.error('Error triggering auth token refresh:', error);
    return false;
  }
}

// Helper to clear cache entries
export function clearApiCache(endpoint?: string): void {
  if (endpoint) {
    // Clear specific endpoint cache entries
    const prefix = `GET:${API_BASE_URL}${endpoint}`;
    Object.keys(cache).forEach(key => {
      if (key.startsWith(prefix)) {
        delete cache[key];
      }
    });
  } else {
    // Clear all cache
    Object.keys(cache).forEach(key => {
      delete cache[key];
    });
  }
}

export const apiClient = {
  get: <T>(endpoint: string, options: RequestOptions = {}): Promise<T> => 
    request<T>(endpoint, { ...options, method: 'GET' }),
  
  post: <T>(endpoint: string, data: any, options: RequestOptions = {}): Promise<T> => 
    request<T>(endpoint, { ...options, method: 'POST', body: data, cache: false }),
  
  put: <T>(endpoint: string, data: any, options: RequestOptions = {}): Promise<T> => 
    request<T>(endpoint, { ...options, method: 'PUT', body: data, cache: false }),
  
  delete: <T>(endpoint: string, options: RequestOptions = {}): Promise<T> => 
    request<T>(endpoint, { ...options, method: 'DELETE', cache: false }),
    
  clearCache: clearApiCache
};

// Types
export interface Client {
  id: string;
  name: string;
  email: string;
  phone?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface Exercise {
  id: string;
  name: string;
  sets: number;
  reps: number;
  weight: number;
  notes?: string;
}

export interface Workout {
  id: string;
  client_id: string;
  client_name: string;
  date: string;
  type: string;
  duration: number;
  notes?: string;
  exercises: Exercise[];
  created_at: string;
  updated_at?: string;
}

// Client API endpoints
export const clientsApi = {
  getAll: (options: RequestOptions = {}) => apiClient.get<Client[]>('/clients', options),
  getById: (id: string, options: RequestOptions = {}) => apiClient.get<Client>(`/clients/${id}`, options),
  create: (data: Omit<Client, 'id' | 'created_at' | 'updated_at'>, options: RequestOptions = {}) => 
    apiClient.post<Client>('/clients', data, options),
  update: (id: string, data: Partial<Omit<Client, 'id' | 'created_at' | 'updated_at'>>, options: RequestOptions = {}) => 
    apiClient.put<Client>(`/clients/${id}`, data, options),
  delete: (id: string, options: RequestOptions = {}) => apiClient.delete<void>(`/clients/${id}`, options),
};

// Workout API endpoints
export const workoutsApi = {
  getAll: (options: RequestOptions = {}) => apiClient.get<Workout[]>('/workouts/workouts', options),
  getById: (id: string, options: RequestOptions = {}) => apiClient.get<Workout>(`/workouts/workouts/${id}`, options),
  getByClientId: (clientId: string, options: RequestOptions = {}) => 
    apiClient.get<Workout[]>(`/workouts/workouts?client_id=${clientId}`, options),
  create: (data: Omit<Workout, 'id' | 'created_at' | 'updated_at'>, options: RequestOptions = {}) => 
    apiClient.post<Workout>('/workouts/workouts', data, options),
  update: (id: string, data: Partial<Omit<Workout, 'id' | 'created_at' | 'updated_at'>>, options: RequestOptions = {}) => 
    apiClient.put<Workout>(`/workouts/workouts/${id}`, data, options),
  delete: (id: string, options: RequestOptions = {}) => apiClient.delete<void>(`/workouts/workouts/${id}`, options),
}; 