'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Parse the hash from the URL
        const hash = window.location.hash;
        console.log('Auth callback processing. Hash:', hash);

        // Verify the session
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('Error getting session:', error.message);
          router.push('/signin?error=session');
          return;
        }

        if (session) {
          console.log('Session verified, redirecting to dashboard');
          // Redirect to the dashboard or home page
          router.push('/clients');
        } else {
          console.log('No session found, redirecting to signin');
          router.push('/signin');
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        router.push('/signin?error=callback');
      }
    };

    handleAuthCallback();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold mb-2">Verifying your login...</h2>
        <p className="text-gray-500">You'll be redirected automatically.</p>
      </div>
    </div>
  );
} 