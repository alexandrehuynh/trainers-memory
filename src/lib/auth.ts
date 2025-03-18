import { supabase } from './supabaseClient';

/**
 * Signs in a user with email and password
 */
export async function signIn(email: string, password: string) {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      console.error('Sign in error:', error);
      return { success: false, error: error.message };
    }

    return { success: true, user: data.user, session: data.session };
  } catch (error: unknown) {
    console.error('Exception during sign in:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'An unknown error occurred'
    };
  }
}

/**
 * Signs out the current user
 * @internal This function is used by the UI components
 */
export async function signOut() {
  try {
    const { error } = await supabase.auth.signOut();
    
    if (error) {
      console.error('Sign out error:', error);
      return { success: false, error: error.message };
    }
    
    return { success: true };
  } catch (error: unknown) {
    console.error('Exception during sign out:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'An unknown error occurred'
    };
  }
}

/**
 * Checks if the user is currently signed in
 */
export async function checkAuthStatus() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return { 
      isAuthenticated: !!session, 
      user: session?.user || null,
      session
    };
  } catch (error) {
    console.error('Error checking auth status:', error);
    return { isAuthenticated: false, user: null, session: null };
  }
} 