'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/authContext';
import { supabase } from '@/lib/supabaseClient';

export default function DebugAuthPage() {
  const { user, session, signOut } = useAuth();
  const [authState, setAuthState] = useState<any>(null);
  const [cookies, setCookies] = useState<string[]>([]);
  const [sessionState, setSessionState] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch debug information
  useEffect(() => {
    const fetchDebugInfo = async () => {
      try {
        setLoading(true);
        
        // Simplified debug state logic
        const authItems: Record<string, string | null> = {};
        if (typeof window !== 'undefined') {
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.includes('supabase')) {
              authItems[key] = localStorage.getItem(key);
            }
          }
        }
        setAuthState({ localStorage: authItems });
        
        // Get cookies for display
        if (typeof document !== 'undefined') {
          setCookies(document.cookie.split(';').map(c => c.trim()));
        }
        
        // Check session directly from Supabase
        const { data } = await supabase.auth.getSession();
        setSessionState({
          hasSession: !!data.session,
          expiresAt: data.session?.expires_at 
            ? new Date(data.session.expires_at * 1000).toISOString() 
            : null,
          userId: data.session?.user?.id || null,
          email: data.session?.user?.email || null,
        });
      } catch (e) {
        console.error('Error fetching debug info:', e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDebugInfo();
  }, []);
  
  // Function to fix the auth state
  const fixAuthState = async () => {
    try {
      setLoading(true);
      // Simplified session refresh logic
      const { error } = await supabase.auth.refreshSession();
      alert(error ? `Error: ${error.message}` : 'Session refreshed successfully');
      
      // Refresh the page to show updated state
      window.location.reload();
    } catch (e) {
      console.error('Error fixing auth state:', e);
      alert(`Error fixing auth state: ${(e as Error).message}`);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-2xl font-bold mb-4">Authentication Debug Page</h1>
      
      <div className="border rounded p-4 mb-4 bg-gray-50">
        <h2 className="text-xl font-semibold mb-2">Current Auth Status</h2>
        <p><strong>Is Authenticated:</strong> {user ? 'Yes' : 'No'}</p>
        <p><strong>User Email:</strong> {user?.email || 'Not logged in'}</p>
        <p><strong>User ID:</strong> {user?.id || 'Not logged in'}</p>
        <p><strong>Role:</strong> {user?.role || 'None'}</p>
        <p><strong>Session Expiry:</strong> {session?.expires_at 
          ? new Date(session.expires_at * 1000).toLocaleString() 
          : 'No session'}</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="border rounded p-4 bg-gray-50">
          <h2 className="text-xl font-semibold mb-2">LocalStorage</h2>
          {loading ? (
            <p>Loading...</p>
          ) : (
            <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-60">
              {JSON.stringify(authState?.localStorage || {}, null, 2)}
            </pre>
          )}
        </div>
        
        <div className="border rounded p-4 bg-gray-50">
          <h2 className="text-xl font-semibold mb-2">Cookies</h2>
          {loading ? (
            <p>Loading...</p>
          ) : (
            <ul className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-60">
              {cookies.length > 0 
                ? cookies.map((cookie, index) => <li key={index}>{cookie}</li>)
                : <li>No cookies found</li>}
            </ul>
          )}
        </div>
      </div>
      
      <div className="border rounded p-4 mb-6 bg-gray-50">
        <h2 className="text-xl font-semibold mb-2">Supabase Session Check</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-60">
            {JSON.stringify(sessionState || {}, null, 2)}
          </pre>
        )}
      </div>
      
      <div className="flex space-x-4">
        <button 
          onClick={fixAuthState}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? 'Working...' : 'Fix Session Cookie'}
        </button>
        
        <button
          onClick={() => signOut()}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Sign Out
        </button>
        
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          Refresh Page
        </button>
      </div>
    </div>
  );
} 