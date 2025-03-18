/**
 * Helper function to get the JWT token from localStorage or cookies
 * This handles different Supabase storage formats with preference for standardized keys
 */
export function getJwtToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    // PRIORITY 1: Standard localStorage key
    const tokenStr = localStorage.getItem('supabase.auth.token');
    if (tokenStr) {
      try {
        const tokenData = JSON.parse(tokenStr);
        if (tokenData?.access_token) {
          return tokenData.access_token;
        }
      } catch (e) {
        console.error('Error parsing token from supabase.auth.token:', e);
      }
    }

    // PRIORITY 2: Standard cookie
    try {
      const cookieStr = document.cookie;
      const supabaseCookieMatch = /supabase-auth-token=([^;]+)/.exec(cookieStr);
      if (supabaseCookieMatch && supabaseCookieMatch[1]) {
        try {
          const cookieData = JSON.parse(decodeURIComponent(supabaseCookieMatch[1]));
          if (cookieData.access_token) {
            return cookieData.access_token;
          }
        } catch (e) {
          console.error('Error parsing token from supabase-auth-token cookie:', e);
        }
      }
    } catch (e) {
      console.error('Error accessing cookies:', e);
    }

    // FALLBACKS - these will be removed in a future release
    // We keep minimal fallbacks for backward compatibility during migration
    
    // Check for generic token format (should be migrated by supabaseClient.ts)
    const genericTokenStr = localStorage.getItem('sb-auth-token');
    if (genericTokenStr) {
      try {
        const genericTokenData = JSON.parse(genericTokenStr);
        if (genericTokenData?.access_token) {
          console.warn('Using deprecated token format. Please refresh your session.');
          return genericTokenData.access_token;
        }
      } catch (e) {
        console.error('Error parsing token from sb-auth-token:', e);
      }
    }
    
    return null;
  } catch (error) {
    console.error('Error getting JWT token:', error);
    return null;
  }
} 