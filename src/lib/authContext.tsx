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
      const response = await fetch('http://localhost:8000/api/v1/auth/user', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

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
      }
      return null;
    } catch (error) {
      console.error('Error fetching user role:', error);
      return null;
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
          }
        } else {
          setUser(null);
          setUserRole(null);
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
          const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
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

  return (
    <AuthContext.Provider value={{ 
      user, 
      session, 
      isLoading, 
      userRole,
      signIn, 
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