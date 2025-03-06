'use client'; // Mark this as a Client Component

import { supabase } from '@/lib/supabaseClient';
import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function Home() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Check if the user is already signed in
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user);
    });

    // Listen for auth state changes (e.g., user signs in or out)
    supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user);
    });
  }, []);

  return (
    <div>
      <h1>Welcome to Trainer's Memory</h1>
      {user ? (
        <p>Signed in as {user.email}</p>
      ) : (
        <div>
          <p>Please sign in to continue.</p>
          <Link href="/signin">
            <button>Sign In</button>
          </Link>
        </div>
      )}
    </div>
  );
}