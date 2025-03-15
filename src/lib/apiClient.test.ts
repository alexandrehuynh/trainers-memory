import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { clearApiCache, request } from './apiClient';

// Mock the global fetch function
global.fetch = vi.fn();

// Mock token helper
vi.mock('./tokenHelper', () => ({
  getJwtToken: vi.fn().mockReturnValue('mock-token'),
}));

describe('API Client', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    vi.mocked(fetch).mockReset();
    
    // Clear any cached responses
    clearApiCache();
    
    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  
  afterEach(() => {
    vi.restoreAllMocks();
  });
  
  test('request should add authorization header when token exists', async () => {
    // Mock successful response
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        status: 'success',
        message: 'Success',
        data: { test: 'data' },
        timestamp: new Date().toISOString(),
        api_version: 'v1',
      }),
    } as Response);
    
    // Call the function
    await request('/test-endpoint');
    
    // Check that fetch was called with the correct arguments
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/test-endpoint',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer mock-token',
        }),
      })
    );
  });
  
  test('request should process response data correctly for workouts endpoint', async () => {
    // Mock successful response with nested data structure
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        status: 'success',
        message: 'Success',
        data: {
          workouts: [
            { id: '1', client_name: 'Test Client' },
            { id: '2', client_name: 'Another Client' },
          ],
          total: 2,
        },
        timestamp: new Date().toISOString(),
        api_version: 'v1',
      }),
    } as Response);
    
    // Call the function
    const result = await request('/workouts/workouts');
    
    // Check that the response was processed correctly
    expect(result).toEqual([
      { id: '1', client_name: 'Test Client' },
      { id: '2', client_name: 'Another Client' },
    ]);
  });
  
  test('request should clear cache after mutations', async () => {
    // Mock successful response
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        status: 'success',
        message: 'Success',
        data: { id: '1' },
        timestamp: new Date().toISOString(),
        api_version: 'v1',
      }),
    } as Response);
    
    // Spy on clearApiCache
    const clearCacheSpy = vi.spyOn({ clearApiCache }, 'clearApiCache');
    
    // Make a POST request
    await request('/clients', { method: 'POST', body: { name: 'Test' } });
    
    // Check that clearApiCache was called
    expect(clearCacheSpy).toHaveBeenCalled();
  });
  
  test('request should retry on network errors', async () => {
    // Mock a failed fetch that eventually succeeds
    vi.mocked(fetch)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          status: 'success',
          data: { test: 'data' },
          timestamp: new Date().toISOString(),
          api_version: 'v1',
        }),
      } as Response);
    
    // Call the function
    const result = await request('/test-endpoint', { retries: 1 });
    
    // Check that fetch was called twice
    expect(fetch).toHaveBeenCalledTimes(2);
    
    // Check that the result is correct
    expect(result).toEqual({ test: 'data' });
  });
}); 