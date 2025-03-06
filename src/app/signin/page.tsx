'use client'; // Mark this as a Client Component

import { useState } from 'react';
import { supabase } from '@/lib/supabaseClient';

export default function SignIn() {
  const [email, setEmail] = useState<string>('');
  const [message, setMessage] = useState<string>('');

  const handleSignIn = async () => {
    const { error } = await supabase.auth.signInWithOtp({ email });
    if (error) {
      setMessage('Error sending magic link: ' + error.message);
    } else {
      setMessage('Magic link sent! Check your email.');
    }
  };

  return (
    <div>
      <h1>Sign In</h1>
      <input
        type="email"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <button onClick={handleSignIn}>Send Magic Link</button>
      {message && <p>{message}</p>}
    </div>
  );
}