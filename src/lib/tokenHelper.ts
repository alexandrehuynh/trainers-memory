/**
 * Helper function to get the JWT token from localStorage
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
      const tokenData = JSON.parse(tokenStr);
      return tokenData.access_token || null;
    }

    // If not found, try to get from project-specific key
    // Extract project reference from URL
    const url = localStorage.getItem('supabase.auth.refreshUrl') || '';
    const projectRef = url.match(/\/([^\/]+)\/auth\/v1/)?.[1];
    
    if (projectRef) {
      const projectKey = `sb-${projectRef}-auth-token`;
      const projectTokenStr = localStorage.getItem(projectKey);
      
      if (projectTokenStr) {
        const projectTokenData = JSON.parse(projectTokenStr);
        return projectTokenData.access_token || null;
      }
    }

    return null;
  } catch (error) {
    console.error('Error getting JWT token:', error);
    return null;
  }
} 