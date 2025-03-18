import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Missing Supabase environment variables. Please check your .env file.');
}

// Function to migrate old token formats to the standardized format
function migrateAuthTokens() {
  if (typeof window === 'undefined') return;
  
  try {
    // Check if we already have the standard token format
    const standardToken = localStorage.getItem('supabase.auth.token');
    if (standardToken) {
      // No need to migrate if we already have the standard token
      return;
    }
    
    // Check for other token formats
    
    // Project-specific format
    const projectRef = process.env.NEXT_PUBLIC_SUPABASE_URL?.match(/([^/.]+)\.supabase/)?.[1];
    if (projectRef) {
      const projectKey = `sb-${projectRef}-auth-token`;
      const projectToken = localStorage.getItem(projectKey);
      
      if (projectToken) {
        console.log(`Migrating auth token from ${projectKey} to standardized format`);
        localStorage.setItem('supabase.auth.token', projectToken);
        
        // Set the cookie as well
        const secure = process.env.NODE_ENV === 'production' ? 'Secure;' : '';
        document.cookie = `supabase-auth-token=${projectToken}; Max-Age=${60 * 60 * 24 * 7}; Path=/; SameSite=Lax; ${secure}`;
        return;
      }
    }
    
    // Generic sb-auth-token format
    const genericToken = localStorage.getItem('sb-auth-token');
    if (genericToken) {
      console.log('Migrating auth token from sb-auth-token to standardized format');
      localStorage.setItem('supabase.auth.token', genericToken);
      
      // Set the cookie as well
      const secure = process.env.NODE_ENV === 'production' ? 'Secure;' : '';
      document.cookie = `supabase-auth-token=${genericToken}; Max-Age=${60 * 60 * 24 * 7}; Path=/; SameSite=Lax; ${secure}`;
    }
  } catch (error) {
    console.error('Error migrating auth tokens:', error);
  }
}

// Run migration on load
if (typeof window !== 'undefined') {
  migrateAuthTokens();
}

// Create the Supabase client with persistence configuration
export const supabase = createClient(supabaseUrl as string, supabaseKey as string, {
  auth: {
    persistSession: true,  // Enable session persistence 
    storageKey: 'supabase.auth.token', // Use consistent storage key
    storage: {
      getItem: (key) => {
        if (typeof window === 'undefined') return null;
        return window.localStorage.getItem(key);
      },
      setItem: (key, value) => {
        if (typeof window === 'undefined') return;
        window.localStorage.setItem(key, value);
        // Also try to set in sessionStorage as a backup
        try { window.sessionStorage.setItem(key, value); } catch (e) {}
        
        // Manually set a cookie to ensure middleware can access authentication
        if (typeof document !== 'undefined' && value && key.includes('auth')) {
          try {
            const secure = process.env.NODE_ENV === 'production' ? 'Secure;' : '';
            // Use a consistent cookie name matching our localStorage key pattern
            document.cookie = `supabase-auth-token=${value}; Max-Age=${60 * 60 * 24 * 7}; Path=/; SameSite=Lax; ${secure}`;
          } catch (e) {
            console.error('Error setting auth cookie:', e);
          }
        }
      },
      removeItem: (key) => {
        if (typeof window === 'undefined') return;
        window.localStorage.removeItem(key);
        try { window.sessionStorage.removeItem(key); } catch (e) {}
        
        // Also remove the cookie
        if (typeof document !== 'undefined' && key.includes('auth')) {
          try {
            document.cookie = 'supabase-auth-token=; Max-Age=0; Path=/;';
          } catch (e) {
            console.error('Error removing auth cookie:', e);
          }
        }
      },
    },
    autoRefreshToken: true, // Auto refresh token
    detectSessionInUrl: true, // Detect session in URL for magic links
  }
});