/**
 * Helper functions for dealing with auth token storage
 * Useful for debugging and fixing token storage issues
 */

/**
 * Standardize token storage by migrating any existing tokens to the standard key
 * This function helps ensure consistent token storage
 */
export function standardizeTokenStorage() {
  if (typeof window === 'undefined') {
    console.warn('standardizeTokenStorage called server-side');
    return { migrated: false };
  }
  
  const LEGACY_KEY = 'sb-auth-token';
  const STANDARD_KEY = 'supabase.auth.token';
  
  // Check if we have a token in the legacy format
  const legacyToken = localStorage.getItem(LEGACY_KEY);
  const standardToken = localStorage.getItem(STANDARD_KEY);
  
  // Results object for diagnostics
  const results = {
    migrated: false,
    hadLegacyToken: !!legacyToken,
    hadStandardToken: !!standardToken,
    action: 'none'
  };
  
  // If legacy token exists but standard doesn't, migrate
  if (legacyToken && !standardToken) {
    try {
      localStorage.setItem(STANDARD_KEY, legacyToken);
      localStorage.removeItem(LEGACY_KEY);
      results.migrated = true;
      results.action = 'migrated';
      console.log('Auth token migrated from legacy to standard format');
    } catch (e) {
      console.error('Error migrating auth token:', e);
      results.action = 'error';
    }
  } 
  // If both exist, keep standard and remove legacy
  else if (legacyToken && standardToken) {
    localStorage.removeItem(LEGACY_KEY);
    results.action = 'removed-legacy';
    console.log('Removed legacy auth token (standard token exists)');
  }
  
  return results;
}

/**
 * Diagnose token storage issues
 * Returns information about token storage for debugging
 */
export function diagnoseTokenStorage() {
  if (typeof window === 'undefined') {
    return { error: 'diagnoseTokenStorage called server-side' };
  }
  
  // List all auth-related keys in localStorage
  const keys = Object.keys(localStorage).filter(key => 
    key.includes('supabase') || key.includes('auth') || key.includes('sb-')
  );
  
  // Check for the standard token
  const hasStandardToken = localStorage.getItem('supabase.auth.token') !== null;
  
  // Check for cookies with auth-related names
  const cookieNames = document.cookie
    .split(';')
    .map(cookie => cookie.trim().split('=')[0])
    .filter(name => 
      name.includes('supabase') || name.includes('auth') || name.includes('sb-')
    );
  
  return {
    timestamp: new Date().toISOString(),
    hasStandardToken,
    authRelatedKeys: keys,
    authRelatedCookies: cookieNames,
    standardStorageKey: 'supabase.auth.token'
  };
}

/**
 * Clear all auth-related storage
 * Useful for forcing a clean logout
 */
export function clearAllAuthStorage() {
  if (typeof window === 'undefined') {
    return { error: 'clearAllAuthStorage called server-side' };
  }
  
  // Clear localStorage items
  const keys = Object.keys(localStorage).filter(key => 
    key.includes('supabase') || key.includes('auth') || key.includes('sb-')
  );
  
  keys.forEach(key => localStorage.removeItem(key));
  
  // Clear cookies
  const cookieNames = document.cookie
    .split(';')
    .map(cookie => cookie.trim().split('=')[0])
    .filter(name => 
      name.includes('supabase') || name.includes('auth') || name.includes('sb-')
    );
  
  cookieNames.forEach(name => {
    document.cookie = `${name}=; Max-Age=0; Path=/;`;
  });
  
  return {
    clearedStorageKeys: keys,
    clearedCookies: cookieNames
  };
} 