import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Missing Supabase environment variables. Please check your .env file.');
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
            document.cookie = `sb-auth-token=${value}; Max-Age=${60 * 60 * 24 * 7}; Path=/; SameSite=Lax; ${secure}`;
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
            document.cookie = 'sb-auth-token=; Max-Age=0; Path=/;';
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