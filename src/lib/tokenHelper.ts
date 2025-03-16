/**
 * Helper function to get the JWT token from localStorage or cookies
 * This handles different Supabase storage formats
 */
export function getJwtToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    // Try to get the token from the standard Supabase key
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

    // If not found, try to get from project-specific key
    // Extract project reference from URL or refreshUrl
    const url = localStorage.getItem('supabase.auth.refreshUrl') || '';
    let projectRef = url.match(/\/([^\/]+)\/auth\/v1/)?.[1];
    
    // If not found in refreshUrl, try to get from SUPABASE_URL env variable
    if (!projectRef && typeof process !== 'undefined') {
      projectRef = process.env.NEXT_PUBLIC_SUPABASE_URL?.match(/([^/.]+)\.supabase/)?.[1] || '';
    }
    
    if (projectRef) {
      // Look for specific project token format
      const projectKey = `sb-${projectRef}-auth-token`;
      const projectTokenStr = localStorage.getItem(projectKey);
      
      if (projectTokenStr) {
        try {
          const projectTokenData = JSON.parse(projectTokenStr);
          if (projectTokenData?.access_token) {
            return projectTokenData.access_token;
          }
        } catch (e) {
          console.error(`Error parsing token from ${projectKey}:`, e);
        }
      }
    }

    // Try generic sb-auth-token as fallback
    const genericTokenStr = localStorage.getItem('sb-auth-token');
    if (genericTokenStr) {
      try {
        const genericTokenData = JSON.parse(genericTokenStr);
        if (genericTokenData?.access_token) {
          return genericTokenData.access_token;
        }
      } catch (e) {
        console.error('Error parsing token from sb-auth-token:', e);
      }
    }
    
    // Last resort - try to get from cookie using document.cookie
    // This is helpful for situations where localStorage might be getting cleared
    try {
      const cookieStr = document.cookie;
      const cookieTokenMatch = /sb-access-token=([^;]+)/.exec(cookieStr);
      if (cookieTokenMatch && cookieTokenMatch[1]) {
        return cookieTokenMatch[1];
      }
      
      // Try to match Supabase auth cookie format
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

    return null;
  } catch (error) {
    console.error('Error getting JWT token:', error);
    return null;
  }
} 