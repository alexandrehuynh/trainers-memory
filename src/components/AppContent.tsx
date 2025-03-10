'use client';

import { useEffect } from 'react';
import Navigation from '@/components/Navigation';
import { useAuth } from '@/lib/authContext';

export default function AppContent({ children }: { children: React.ReactNode }) {
  const { refreshToken } = useAuth();
  
  useEffect(() => {
    // Listen for token refresh events from the API client
    const handleTokenRefreshNeeded = () => {
      console.log('Token refresh needed, attempting refresh...');
      refreshToken()
        .then(success => {
          console.log('Token refresh result:', success ? 'success' : 'failed');
        })
        .catch(error => {
          console.error('Error during token refresh:', error);
        });
    };
    
    window.addEventListener('auth:token-refresh-needed', handleTokenRefreshNeeded);
    
    return () => {
      window.removeEventListener('auth:token-refresh-needed', handleTokenRefreshNeeded);
    };
  }, [refreshToken]);
  
  return (
    <div className="flex flex-col min-h-screen">
      <Navigation />
      <main className="flex-grow container mx-auto p-4 sm:p-6">
        {children}
      </main>
      <footer className="py-4 text-center text-sm text-gray-500">
        © {new Date().getFullYear()} Trainer's Memory
      </footer>
    </div>
  );
} 