import { supabase } from './supabaseClient';

/**
 * Gets debug information about the current auth state
 */
export function debugAuthState() {
  if (typeof window === 'undefined') {
    return { localStorage: null };
  }

  // Get all Supabase related items from local storage
  const authItems: Record<string, string | null> = {};
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.includes('supabase')) {
      authItems[key] = localStorage.getItem(key);
    }
  }

  return { localStorage: authItems };
}

/**
 * Ensures that the current session is properly synced to cookies
 */
export async function ensureSessionInCookies() {
  try {
    // Get the current session
    const { data } = await supabase.auth.getSession();
    if (!data.session) {
      return false;
    }

    // Force refreshing the session to update cookies
    await supabase.auth.refreshSession();
    return true;
  } catch (error) {
    console.error('Error ensuring session in cookies:', error);
    return false;
  }
} 