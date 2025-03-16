'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { useRouter } from 'next/navigation';
import { supabase } from './supabaseClient';

interface UserRole {
  role: string;
  permissions: string[];
}

interface AuthUser extends User {
  role?: string;
  permissions?: string[];
}

interface AuthContextType {
  user: AuthUser | null;
  session: Session | null;
  isLoading: boolean;
  userRole: UserRole | null;
  signIn: (email: string) => Promise<{ error: Error | null; success: boolean }>;
  // Add password authentication methods (commented out until Supabase is configured)
  signInWithPassword: (email: string, password: string) => Promise<{ error: Error | null; success: boolean }>;
  register: (email: string, password: string) => Promise<{ error: Error | null; success: boolean; needsEmailConfirmation?: boolean }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: Error | null; success: boolean }>;
  refreshToken: () => Promise<boolean>;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [userRole, setUserRole] = useState<UserRole | null>(null);
  const router = useRouter();

  // Fetch user role and permissions from the backend
  const fetchUserRole = async (token: string) => {
    try {
      // Configuration options:
      // 1. NEXT_PUBLIC_USE_FALLBACK_ROLES=true - Use Supabase user metadata without backend
      // 2. NEXT_PUBLIC_BACKEND_URL - URL for the backend API (local or cloud)
      // 3. NEXT_PUBLIC_USE_LOCAL_BACKEND=true - Use localhost backend instead of cloud

      // Determine backend URL 
      const useLocalBackend = process.env.NEXT_PUBLIC_USE_LOCAL_BACKEND === 'true';
      const cloudBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://trainers-memory.onrender.com';
      const localBackendUrl = 'http://localhost:8000';
      const backendUrl = useLocalBackend ? localBackendUrl : cloudBackendUrl;
      
      // Check if we're using Supabase user metadata instead of backend API
      const useFallback = process.env.NEXT_PUBLIC_USE_FALLBACK_ROLES === 'true';
      
      // Log the current backend configuration for debugging
      console.log('Auth backend config:', { 
        backendUrl, 
        useLocalBackend, 
        useFallback 
      });
      
      if (useFallback) {
        // Get user metadata from Supabase directly
        const { data: userData, error } = await supabase.auth.getUser(token);
        
        if (error) {
          console.error('Error getting user from Supabase:', error);
          return defaultUserRole();
        }
        
        const userMetadata = userData?.user?.user_metadata || {};
        const appMetadata = userData?.user?.app_metadata || {};
        
        // Use role from metadata or default to 'trainer'
        const role = userMetadata.role || appMetadata.role || 'trainer';
        
        // Define permissions based on role
        const roleData = {
          role,
          permissions: getPermissionsForRole(role)
        };
        
        setUserRole(roleData);
        
        // Update user with role information
        if (user) {
          setUser({
            ...user,
            role: roleData.role,
            permissions: roleData.permissions
          });
        }
        
        return roleData;
      }
      
      // Try to fetch from backend API if fallback is not enabled
      try {
        const response = await fetch(`${backendUrl}/api/v1/auth/user`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        console.log(`Backend API request to ${backendUrl}/api/v1/auth/user:`, response.status);

        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            const roleData = {
              role: data.data.role || 'user',
              permissions: data.data.permissions || []
            };
            setUserRole(roleData);
            
            // Update user with role information
            if (user) {
              setUser({
                ...user,
                role: roleData.role,
                permissions: roleData.permissions
              });
            }
            
            return roleData;
          }
        } else {
          console.warn(`Backend API returned status ${response.status}`);
        }
      } catch (error) {
        console.warn('Backend API not available, using fallback role:', error);
      }
      
      // Fallback if API fails
      return defaultUserRole();
    } catch (error) {
      console.error('Error in fetchUserRole:', error);
      return defaultUserRole();
    }
  };
  
  // Helper function to create a default role
  const defaultUserRole = () => {
    const roleData = {
      role: 'trainer',
      permissions: getPermissionsForRole('trainer')
    };
    
    setUserRole(roleData);
    
    // Update user with role information
    if (user) {
      setUser({
        ...user,
        role: roleData.role,
        permissions: roleData.permissions
      });
    }
    
    return roleData;
  };
  
  // Helper function to get permissions based on role
  const getPermissionsForRole = (role: string) => {
    switch (role) {
      case 'admin':
        return [
          'read:own_data', 'create:client', 'update:client', 'delete:client',
          'create:workout', 'update:workout', 'delete:workout',
          'read:all_data', 'manage:users'
        ];
      case 'trainer':
        return [
          'read:own_data', 'create:client', 'update:client', 'delete:client',
          'create:workout', 'update:workout', 'delete:workout'
        ];
      default: // user
        return ['read:own_data'];
    }
  };

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      try {
        setIsLoading(true);
        const { data } = await supabase.auth.getSession();
        setSession(data.session);
        
        if (data.session?.user) {
          setUser(data.session.user);
          
          // Fetch user role if we have a session
          if (data.session.access_token) {
            await fetchUserRole(data.session.access_token);
            
            // Set cookie for middleware access
            if (typeof document !== 'undefined') {
              try {
                const secure = process.env.NODE_ENV === 'production' ? 'Secure;' : '';
                document.cookie = `sb-auth-token=${JSON.stringify({ access_token: data.session.access_token })}; Max-Age=${60 * 60 * 24 * 7}; Path=/; SameSite=Lax; ${secure}`;
              } catch (e) {
                console.error('Error setting auth cookie:', e);
              }
            }
          }
        } else {
          setUser(null);
          setUserRole(null);
        }
      } catch (error) {
        console.error('Error getting initial session:', error);
      } finally {
        setIsLoading(false);
      }
    };

    getInitialSession();

    // Set up auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        setSession(session);
        
        if (session?.user) {
          setUser(session.user);
          
          // Fetch user role if we have a new session
          if (session.access_token) {
            await fetchUserRole(session.access_token);
            
            // Update cookie with new session token
            if (typeof document !== 'undefined') {
              try {
                const secure = process.env.NODE_ENV === 'production' ? 'Secure;' : '';
                document.cookie = `sb-auth-token=${JSON.stringify({ access_token: session.access_token })}; Max-Age=${60 * 60 * 24 * 7}; Path=/; SameSite=Lax; ${secure}`;
              } catch (e) {
                console.error('Error setting auth cookie:', e);
              }
            }
          }
        } else {
          setUser(null);
          setUserRole(null);
          
          // Clear auth cookie
          if (typeof document !== 'undefined') {
            document.cookie = 'sb-auth-token=; Max-Age=0; Path=/;';
          }
        }
        
        setIsLoading(false);
      }
    );

    // Clean up on unmount
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string) => {
    try {
      const { error } = await supabase.auth.signInWithOtp({ email });
      if (error) {
        throw error;
      }
      return { error: null, success: true };
    } catch (error) {
      console.error('Error signing in:', error);
      return { error: error as Error, success: false };
    }
  };

  const signOut = async () => {
    try {
      await supabase.auth.signOut();
      setUser(null);
      setUserRole(null);
      
      // Clear all possible auth cookies
      if (typeof document !== 'undefined') {
        try {
          // Clear standard Supabase auth cookies
          document.cookie = 'sb-auth-token=; Max-Age=0; Path=/;';
          document.cookie = 'supabase-auth-token=; Max-Age=0; Path=/;';
          document.cookie = 'sb-access-token=; Max-Age=0; Path=/;';
          
          // Clear project-specific cookie if applicable
          const projectRef = process.env.NEXT_PUBLIC_SUPABASE_URL?.match(/([^/.]+)\.supabase/)?.[1];
          if (projectRef) {
            document.cookie = `sb-${projectRef}-auth-token=; Max-Age=0; Path=/;`;
          }
        } catch (e) {
          console.error('Error clearing auth cookies:', e);
        }
      }
      
      // Redirect to sign-in page
      router.push('/signin');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const resetPassword = async (email: string) => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email);
      if (error) {
        throw error;
      }
      return { error: null, success: true };
    } catch (error) {
      console.error('Error resetting password:', error);
      return { error: error as Error, success: false };
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      // First try to refresh using Supabase's built-in refresh
      const { data, error } = await supabase.auth.refreshSession();
      
      if (error) {
        // If Supabase refresh fails, try our custom backend refresh
        if (session?.refresh_token) {
          // Determine backend URL (same logic as fetchUserRole)
          const useLocalBackend = process.env.NEXT_PUBLIC_USE_LOCAL_BACKEND === 'true';
          const cloudBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://trainers-memory.onrender.com';
          const localBackendUrl = 'http://localhost:8000';
          const backendUrl = useLocalBackend ? localBackendUrl : cloudBackendUrl;
          
          try {
            const response = await fetch(`${backendUrl}/api/v1/auth/refresh`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Refresh-Token': session.refresh_token
              }
            });
            
            if (response.ok) {
              const responseData = await response.json();
              if (responseData.status === 'success') {
                // Update the session with the new token
                const newSession = {
                  ...session,
                  access_token: responseData.data.access_token
                };
                setSession(newSession);
                return true;
              }
            }
          } catch (error) {
            console.warn('Backend refresh token failed:', error);
          }
        }
        return false;
      }
      
      // If Supabase refresh succeeded
      if (data.session) {
        setSession(data.session);
        setUser(data.session.user);
        
        // Fetch updated role information
        if (data.session.access_token) {
          await fetchUserRole(data.session.access_token);
        }
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error refreshing token:', error);
      return false;
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!userRole || !userRole.permissions) return false;
    return userRole.permissions.includes(permission);
  };

  // Implement password authentication
  const signInWithPassword = async (email: string, password: string) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) {
        return { error, success: false };
      }
      
      // Update user state immediately on successful login
      if (data?.user) {
        setUser(data.user);
        setSession(data.session);
        
        if (data.session?.access_token) {
          await fetchUserRole(data.session.access_token);
          
          // After successful authentication, set a cookie that middleware can access
          if (typeof document !== 'undefined') {
            try {
              const secure = process.env.NODE_ENV === 'production' ? 'Secure;' : '';
              document.cookie = `sb-auth-token=${JSON.stringify({ access_token: data.session.access_token })}; Max-Age=${60 * 60 * 24 * 7}; Path=/; SameSite=Lax; ${secure}`;
            } catch (e) {
              console.error('Error setting auth cookie:', e);
            }
          }
        }
        
        // Redirect to home page on successful login with slight delay to ensure cookies are set
        setTimeout(() => {
          router.push('/');
        }, 100);
      }
      
      return { error: null, success: true };
    } catch (error) {
      console.error('Error signing in with password:', error);
      return { error: error as Error, success: false };
    }
  }

  const register = async (email: string, password: string) => {
    try {
      // Set initial role to 'trainer' for new users
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            role: 'trainer' // Default role for new users
          }
        }
      });
      
      if (error) {
        return { error, success: false };
      }
      
      // Note: Supabase may require email confirmation depending on your settings
      return { 
        error: null, 
        success: true,
        needsEmailConfirmation: data?.user?.identities?.length === 0 || !!data?.user?.confirmation_sent_at 
      };
    } catch (error) {
      console.error('Error registering user:', error);
      return { error: error as Error, success: false };
    }
  }

  return (
    <AuthContext.Provider value={{ 
      user, 
      session, 
      isLoading, 
      userRole,
      signIn, 
      signInWithPassword,
      register,
      signOut, 
      resetPassword,
      refreshToken,
      hasPermission
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 