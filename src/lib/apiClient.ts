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

// Cache storage for API responses
const apiCache: Record<string, { timestamp: number; data: any }> = {};
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
export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body = null,
    cache = true,
    retries = 3,
    retryDelay = 1000,
    skipCache = false,
  } = options;

  const url = `${API_BASE_URL}${endpoint}`;
  const token = getJwtToken();
  const cacheEnabled = cache !== false; // Cache enabled by default
  const maxRetries = retries; // Use the provided retries
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-API-Key': 'test_key_12345', // Add the test API key for all requests
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const config: RequestInit = {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
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
      console.log(`API Request: ${method} ${endpoint}`);
      const response = await fetch(url, config);
      
      // Handle 401 Unauthorized (token expired)
      if (response.status === 401) {
        console.log('401 Unauthorized - Token may have expired. Attempting refresh...');
        const refreshResult = await refreshTokenAndRetry();
        if (refreshResult) {
          return refreshResult;
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
      
      // Only retry on network errors, not on API errors
      if (retries > 0 && error.message?.includes('Failed to fetch')) {
        console.log(`Retrying API request (${retries} retries left): ${endpoint}`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        return fetchWithRetry(retries - 1);
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