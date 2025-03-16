import { getJwtToken } from './tokenHelper';
import { getBaseApiUrl, getApiUrl } from './apiUtils';

// Debug environment variables to ensure correct configuration
console.log('API Client Environment Variables:', {
  NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || '(not set)',
  NEXT_PUBLIC_USE_LOCAL_BACKEND: process.env.NEXT_PUBLIC_USE_LOCAL_BACKEND || '(not set)',
  NEXT_PUBLIC_USE_FALLBACK_ROLES: process.env.NEXT_PUBLIC_USE_FALLBACK_ROLES || '(not set)',
  NEXT_PUBLIC_API_PATH_PREFIX: process.env.NEXT_PUBLIC_API_PATH_PREFIX || '(not set)',
  NODE_ENV: process.env.NODE_ENV || '(not set)'
});

// Determine backend URL based on environment
const isProduction = process.env.NODE_ENV === 'production';
const useLocalBackend = !isProduction && process.env.NEXT_PUBLIC_USE_LOCAL_BACKEND === 'true';
const localBackendUrl = 'http://localhost:8000';
const backendBaseUrl = useLocalBackend ? localBackendUrl : getBaseApiUrl();

console.log('API client using backend URL:', backendBaseUrl);
console.log('Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');

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

// Cache storage for API responses
const apiCache: Record<string, { timestamp: number; data: any }> = {};
const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes in milliseconds

// Backend connection state
let isBackendAvailable = true; // Assume backend is available initially
let lastBackendCheck = 0;
const BACKEND_CHECK_INTERVAL = 30 * 1000; // Check backend availability every 30 seconds

// Function to check if backend is available
async function checkBackendAvailability(): Promise<boolean> {
  // Don't check too frequently
  const now = Date.now();
  if (now - lastBackendCheck < BACKEND_CHECK_INTERVAL) {
    return isBackendAvailable;
  }
  
  lastBackendCheck = now;
  console.log(`Checking backend availability: ${backendBaseUrl}`);
  
  try {
    // Use the AbortController to add a short timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    // Use the health endpoint for checking backend availability
    let healthUrl;
    if (isProduction) {
      // In production, always use the production backend URL
      healthUrl = `${getBaseApiUrl()}/health`;
    } else if (useLocalBackend) {
      // For local development with local backend flag enabled
      healthUrl = `${localBackendUrl}/health`;
    } else {
      // For other non-production environments
      healthUrl = `${getBaseApiUrl()}/health`;
    }
    
    console.log(`Trying health check at: ${healthUrl}`);
    
    const response = await fetch(healthUrl, {
      method: 'GET',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      console.log(`Backend is available at ${backendBaseUrl}`);
      isBackendAvailable = true;
      return true;
    } else {
      console.warn(`Backend health check failed with status: ${response.status}`);
      isBackendAvailable = false;
      return false;
    }
  } catch (error) {
    console.error(`Backend connection check failed for ${backendBaseUrl}:`, error);
    isBackendAvailable = false;
    return false;
  }
}

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
export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body = null,
    cache = true,
    retries = 3,
    retryDelay = 1000,
    skipCache = false,
  } = options;

  // Ensure endpoint has the API version prefix if it doesn't already include it
  const apiEndpoint = endpoint.startsWith('/api/v1') ? 
    endpoint : 
    endpoint.startsWith('/') ? 
      `/api/v1${endpoint}` : 
      `/api/v1/${endpoint}`;

  // Use the appropriate URL based on the environment
  let url;
  if (isProduction) {
    // In production, always use the production backend URL
    url = getApiUrl(apiEndpoint);
  } else if (useLocalBackend) {
    // For local development with local backend flag enabled
    url = `${localBackendUrl}${apiEndpoint}`;
  } else {
    // For other non-production environments, use the configured backend URL
    url = getApiUrl(apiEndpoint);
  }
  
  const token = getJwtToken();
  const cacheEnabled = cache !== false; // Cache enabled by default
  const maxRetries = retries; // Use the provided retries
  
  console.log(`API Request initiated: ${method} ${url}`);
  console.log(`Token present: ${!!token}`);
  console.log(`Request config:`, { method, url, headers: options.headers, useCache: cacheEnabled });
  
  // Check backend availability first for GET requests
  // For mutations we'll always try to make the request
  if (method === 'GET') {
    const backendAvailable = await checkBackendAvailability();
    if (!backendAvailable) {
      console.warn(`Backend not available, using fallback data for ${endpoint}`);
      if (endpoint.includes('/clients')) {
        return generateSampleClients() as unknown as T;
      } else if (endpoint.includes('/workouts')) {
        return generateSampleWorkouts() as unknown as T;
      }
    }
  }
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || 'test_key_12345', // Use environment variable if available
    ...options.headers,
  };
  
  console.log('Request headers:', headers); // Log headers for debugging
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
    console.log('Using auth token:', token.substring(0, 10) + '...'); // Log part of the token for debugging
  } else {
    console.warn('No authentication token available for request to:', endpoint);
  }
  
  const config: RequestInit = {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    // Add a timeout using AbortController - reduce to a more reasonable 8 seconds
    signal: AbortSignal.timeout(8000) // 8 second timeout
  };
  
  // Check cache for GET requests
  if (cacheEnabled && method === 'GET' && !skipCache) {
    const cacheKey = getCacheKey(url, options);
    const cachedData = apiCache[cacheKey];
    if (cachedData && isCacheValid(cachedData.timestamp)) {
      console.log(`Cache hit for ${endpoint}`);
      return cachedData.data;
    }
  }
  
  // Function to handle the actual fetch with retries
  const fetchWithRetry = async (retries: number): Promise<T> => {
    try {
      console.log(`API Request: ${method} ${endpoint} - attempt ${maxRetries - retries + 1}/${maxRetries + 1}`);
      const startTime = Date.now();
      
      const response = await fetch(url, config);
      const endTime = Date.now();
      console.log(`API Response received in ${endTime - startTime}ms for ${endpoint}`);
      
      // Handle 401 Unauthorized (token expired)
      if (response.status === 401) {
        console.log('401 Unauthorized - Token may have expired or API key is invalid');
        
        try {
          const errorData = await response.json();
          console.error('Auth error details:', errorData);
        } catch (e) {
          console.error('Could not parse 401 error response');
        }
        
        const refreshResult = await refreshTokenAndRetry();
        if (refreshResult) {
          return refreshResult;
        }
      }
      
      // Handle 500 Internal Server Error for more detailed logging
      if (response.status === 500) {
        console.error('500 Internal Server Error from backend');
        try {
          const errorText = await response.text();
          console.error('Server error details:', errorText);
        } catch (e) {
          console.error('Could not read error details from 500 response');
        }
      }
      
      // For all other non-200 responses, try to parse the error
      if (!response.ok) {
        let errorMessage = `API error: ${response.status} ${response.statusText}`;
        
        try {
          const errorData = await response.json();
          if (errorData && errorData.message) {
            errorMessage = errorData.message;
          }
        } catch (e) {
          // If we can't parse JSON, use the text content if available
          try {
            const errorText = await response.text();
            if (errorText) {
              errorMessage = errorText;
            }
          } catch (textError) {
            // If we can't get text either, just use the status
            console.error('Could not parse error response', textError);
          }
        }
        
        console.error(`API returned error: ${errorMessage}`);
        throw new Error(errorMessage);
      }
      
      // Parse successful response
      const data = await response.json();
      console.log(`API data received for ${endpoint}:`, { dataSize: JSON.stringify(data).length });
      
      // Process response data based on endpoint to maintain compatibility
      const processedData = processResponseData(endpoint, data);
      
      // Cache GET responses if caching is enabled
      if (cacheEnabled && method === 'GET') {
        const cacheKey = getCacheKey(url, options);
        apiCache[cacheKey] = {
          data: processedData,
          timestamp: Date.now(),
        };
      }
      
      return processedData;
    } catch (error: any) {
      console.error(`API Error for ${endpoint}:`, error.message);
      
      // Check if this is an AbortError (timeout)
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        console.error(`Request timeout for ${endpoint} - ${error.message}`);
        // Fallback to sample data if available
        if (endpoint.includes('/clients')) {
          console.error(`Timeout fetching clients - using fallback data`);
          // Return fallback sample client data
          return generateSampleClients() as unknown as T;
        } else if (endpoint.includes('/workouts')) {
          console.error(`Timeout fetching workouts - using fallback data`);
          // Return fallback sample workout data
          return generateSampleWorkouts() as unknown as T;
        }
      }
      
      // Only retry on network errors, not on API errors
      if (retries > 0 && (error.message?.includes('Failed to fetch') || error.name === 'TypeError' || error.name === 'AbortError')) {
        console.log(`Retrying API request (${retries} retries left): ${endpoint}`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        return fetchWithRetry(retries - 1);
      }
      
      // If we've exhausted retries and still failed, use fallback data
      if (endpoint.includes('/clients')) {
        console.error(`All retries failed for ${endpoint} - using fallback client data`);
        return generateSampleClients() as unknown as T;
      } else if (endpoint.includes('/workouts')) {
        console.error(`All retries failed for ${endpoint} - using fallback workout data`);
        return generateSampleWorkouts() as unknown as T;
      }
      
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
  
  // Determine if this is a mutation operation that should invalidate cache
  const isMutation = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method || '');
  
  try {
    const result = await fetchWithRetry(maxRetries);
    
    // Clear relevant caches after successful mutations
    if (isMutation) {
      // Parse the endpoint to determine what resource is being modified
      const resourcePath = endpoint.split('/')[1]; // e.g., 'clients' from '/clients/123'
      console.log(`Clearing cache for resource: ${resourcePath} after ${method} operation`);
      
      // Clear the specific endpoint cache
      clearApiCache(endpoint);
      
      // Clear the collection endpoint cache as well (e.g., "/clients" when modifying "/clients/123")
      if (resourcePath) {
        clearApiCache(`/${resourcePath}`);
        console.log(`Also cleared collection cache: /${resourcePath}`);
        
        // For client operations, also clear any potentially related workout caches
        if (resourcePath === 'clients') {
          clearApiCache('/workouts');
          console.log('Also cleared workouts cache as it may contain client information');
        }
      }
    }
    
    return result;
  } catch (error) {
    throw error;
  }
}

// Helper function to process response data based on endpoint
function processResponseData(endpoint: string, data: any): any {
  // Handle formatted API responses with { status, data } structure
  if (data && typeof data === 'object' && data.status === 'success' && data.data !== undefined) {
    // Special case handling for endpoints that return nested data structures
    if (endpoint.includes('/workouts') && data.data.workouts && Array.isArray(data.data.workouts)) {
      return data.data.workouts;
    }
    
    // Handle clients endpoint that returns { clients: [...] }
    if (endpoint.includes('/clients') && !endpoint.includes('/clients/') && data.data.clients && Array.isArray(data.data.clients)) {
      return data.data.clients;
    }
    
    // For other endpoints, just return the data property
    return data.data;
  }
  
  // For responses that don't follow the standard format
  // Check for nested data structures directly
  if (data && typeof data === 'object') {
    if (endpoint.includes('/workouts') && data.workouts && Array.isArray(data.workouts)) {
      return data.workouts;
    }
    
    if (endpoint.includes('/clients') && !endpoint.includes('/clients/') && data.clients && Array.isArray(data.clients)) {
      return data.clients;
    }
  }
  
  // Default case - return the data as is
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
    const cacheKeys = Object.keys(apiCache);
    const keysToRemove = cacheKeys.filter(key => key.includes(endpoint));
    
    keysToRemove.forEach(key => {
      console.log(`Clearing cache for: ${key}`);
      delete apiCache[key];
    });
    
    console.log(`Cleared ${keysToRemove.length} cache entries for: ${endpoint}`);
  } else {
    console.log('Clearing entire API cache');
    Object.keys(apiCache).forEach(key => delete apiCache[key]);
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
  getAll: (options: RequestOptions = {}) => apiClient.get<Workout[]>('/workouts', options),
  getById: (id: string, options: RequestOptions = {}) => apiClient.get<Workout>(`/workouts/${id}`, options),
  getByClientId: (clientId: string, options: RequestOptions = {}) => 
    apiClient.get<Workout[]>(`/workouts?client_id=${clientId}`, options),
  create: (data: Omit<Workout, 'id' | 'created_at' | 'updated_at'>, options: RequestOptions = {}) => 
    apiClient.post<Workout>('/workouts', data, options),
  update: (id: string, data: Partial<Omit<Workout, 'id' | 'created_at' | 'updated_at'>>, options: RequestOptions = {}) => 
    apiClient.put<Workout>(`/workouts/${id}`, data, options),
  delete: (id: string, options: RequestOptions = {}) => apiClient.delete<void>(`/workouts/${id}`, options),
};

// Add OCR API interface and methods to the apiClient

// OCR related interfaces
export interface OCRResult {
  client_id?: string;
  workout_records: {
    date: string;
    type: string;
    duration: number;
    notes: string;
    exercises: Array<{
      name: string;
      sets: number;
      reps: number;
      weight: number;
      notes: string;
    }>;
  }[];
  ocr_text: string;
  original_image_url?: string;
}

// Add OCR API object
export const ocrApi = {
  /**
   * Process an image containing workout notes using OCR
   */
  processImage: async (
    imageFile: File,
    clientId?: string
  ): Promise<OCRResult> => {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    if (clientId) {
      formData.append('client_id', clientId);
    }

    const response = await request<OCRResult>(
      '/transformation/ocr/process',
      {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type here - the browser will set it with the correct boundary for FormData
        },
        cache: false,
      }
    );

    return response;
  },

  /**
   * Convert OCR results to workout data and save to database
   */
  saveOCRResults: async (
    clientId: string,
    workoutRecords: OCRResult['workout_records']
  ): Promise<{ success: boolean; count: number }> => {
    const response = await request<{ success: boolean; count: number }>(
      '/transformation/ocr/save',
      {
        method: 'POST',
        body: { client_id: clientId, workout_records: workoutRecords },
        cache: false,
      }
    );

    return response;
  },
};

// Function to analyze client workout data using AI
export async function analyzeClientData(clientId: string, query: string, forceRefresh: boolean = false) {
  const endpoint = `/intelligence/analysis/analyze`;
  const response = await request<any>(endpoint, {
    method: 'POST',
    body: { client_id: clientId, query, force_refresh: forceRefresh },
    cache: false // Don't cache the API request itself, as we're using server-side caching
  });
  return response.data;
}

// Function to clear the OpenAI cache
export async function clearOpenAICache(clientId?: string) {
  const endpoint = `/intelligence/analysis/clear-cache`;
  const response = await request<any>(endpoint, {
    method: 'POST',
    body: clientId ? { client_id: clientId } : {},
    cache: false
  });
  return response.data;
}

// Function to get OpenAI rate limit status
export async function getOpenAIRateLimitStatus() {
  const endpoint = `/intelligence/analysis/rate-limit-status`;
  const response = await request<any>(endpoint, { cache: false });
  return response.data;
}

// Nutrition-related types and API endpoints
export interface MealPlanRequirements {
  goal: 'muscle_gain' | 'fat_loss' | 'maintenance' | 'performance';
  calories_per_day: number;
  meals_per_day: number;
  duration_days: number;
  dietary_preferences?: string[];
  restrictions?: string[];
  include_shopping_list?: boolean;
}

export interface NutritionData {
  time_period: string;
  daily_entries: Array<{
    date: string;
    meals: Array<{
      name: string;
      time: string;
      foods: Array<{
        name: string;
        amount: string;
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
      }>;
    }>;
    totals: {
      calories: number;
      protein: number;
      carbs: number;
      fat: number;
      water?: number;
    };
  }>;
}

export interface MealPlan {
  client_id: string;
  plan_name: string;
  goal: string;
  calories_per_day: number;
  macronutrient_targets: {
    protein: string;
    carbs: string;
    fat: string;
  };
  daily_plans: Array<any>; // Detailed structure omitted for brevity
  shopping_list?: Record<string, Array<{ item: string; quantity: string }>>;
  notes: string;
}

export interface NutritionAnalysis {
  client_id: string;
  time_period: string;
  analysis_date: string;
  nutrition_analysis: {
    caloric_intake: {
      average_daily: number;
      assessment: string;
    };
    macronutrient_distribution: {
      protein: {
        average_daily: number;
        percentage: number;
        assessment: string;
      };
      carbohydrates: {
        average_daily: number;
        percentage: number;
        assessment: string;
      };
      fat: {
        average_daily: number;
        percentage: number;
        assessment: string;
      };
    };
    meal_patterns: {
      average_meals_per_day: number;
      meal_timing: string;
      assessment: string;
    };
    hydration: {
      average_daily_water: number;
      assessment: string;
    };
  };
  recommendations: string[];
  overall_assessment: string;
}

// Nutrition API endpoints
export const nutritionApi = {
  /**
   * Generate a personalized meal plan based on client requirements
   */
  generateMealPlan: async (
    clientId: string,
    requirements: MealPlanRequirements
  ): Promise<MealPlan> => {
    const response = await request<MealPlan>(
      `/nutrition/meal-plans?client_id=${clientId}`,
      {
        method: 'POST',
        body: requirements,
        cache: false,
      }
    );
    return response;
  },

  /**
   * Analyze nutrition data and provide insights
   */
  analyzeNutrition: async (
    clientId: string,
    nutritionData: NutritionData
  ): Promise<NutritionAnalysis> => {
    const response = await request<NutritionAnalysis>(
      `/nutrition/nutrition-analysis?client_id=${clientId}`,
      {
        method: 'POST',
        body: nutritionData,
        cache: false,
      }
    );
    return response;
  }
};

// Generate sample client data for fallback
function generateSampleClients(): Client[] {
  console.log('Generating sample client data for fallback');
  notifyFallbackDataUsed('clients');
  return [
    {
      id: 'sample-1',
      name: 'Alex Smith (Sample)',
      email: 'alex@example.com',
      phone: '555-123-4567',
      notes: 'Sample client data - API connection failed',
      created_at: new Date().toISOString(),
    },
    {
      id: 'sample-2',
      name: 'Jamie Johnson (Sample)',
      email: 'jamie@example.com',
      phone: '555-987-6543',
      notes: 'Sample client data - API connection failed',
      created_at: new Date().toISOString(),
    }
  ];
}

// Generate sample workout data for fallback
function generateSampleWorkouts(): Workout[] {
  console.log('Generating sample workout data for fallback');
  notifyFallbackDataUsed('workouts');
  return [
    {
      id: 'sample-w1',
      client_id: 'sample-1',
      client_name: 'Alex Smith (Sample)',
      date: new Date().toISOString().split('T')[0],
      type: 'Strength',
      duration: 60,
      notes: 'Sample workout data - API connection failed',
      exercises: [
        {
          id: 'ex-1',
          name: 'Bench Press',
          sets: 3,
          reps: 10,
          weight: 135
        },
        {
          id: 'ex-2',
          name: 'Squats',
          sets: 3,
          reps: 12,
          weight: 185
        }
      ],
      created_at: new Date().toISOString()
    }
  ];
}

// Function to notify the user that fallback data is being used
function notifyFallbackDataUsed(dataType: string): void {
  // Create a notification element if it doesn't exist
  const existingNotification = document.getElementById('fallback-data-notification');
  if (existingNotification) {
    return; // Notification already exists, don't create another one
  }
  
  const notification = document.createElement('div');
  notification.id = 'fallback-data-notification';
  notification.style.position = 'fixed';
  notification.style.bottom = '20px';
  notification.style.right = '20px';
  notification.style.backgroundColor = '#f44336';
  notification.style.color = 'white';
  notification.style.padding = '15px 20px';
  notification.style.borderRadius = '5px';
  notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  
  notification.innerHTML = `
    <div style="font-weight: bold; margin-bottom: 8px;">Unable to connect to API</div>
    <div>Using sample ${dataType} data instead. Please check your internet connection and try again later.</div>
    <button id="dismiss-notification" style="background: white; color: #f44336; border: none; padding: 5px 10px; margin-top: 10px; cursor: pointer; border-radius: 3px;">Dismiss</button>
  `;
  
  document.body.appendChild(notification);
  
  // Add event listener to dismiss button
  document.getElementById('dismiss-notification')?.addEventListener('click', () => {
    document.body.removeChild(notification);
  });
  
  // Automatically remove after 10 seconds
  setTimeout(() => {
    if (document.body.contains(notification)) {
      document.body.removeChild(notification);
    }
  }, 10000);
} 