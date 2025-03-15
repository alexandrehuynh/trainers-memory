'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/authContext';
import Card from '@/components/ui/Card';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import Navigation from '@/components/Navigation';

// Force dynamic rendering for this route
export const dynamic = 'force-dynamic';

// Add metadata for the route
export const metadata = {
  title: 'Sign In - Trainer\'s Memory',
  description: 'Sign in to your Trainer\'s Memory account',
};

export default function SignIn() {
  const { signIn, resetPassword } = useAuth();
  const [email, setEmail] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | '' }>({
    text: '',
    type: '',
  });
  const [mode, setMode] = useState<'signin' | 'reset'>('signin');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage({ text: '', type: '' });

    try {
      if (mode === 'signin') {
        const { error, success } = await signIn(email);
        if (error) {
          setMessage({
            text: `Error sending magic link: ${error.message}`,
            type: 'error',
          });
        } else if (success) {
          setMessage({
            text: 'Magic link sent! Check your email to sign in.',
            type: 'success',
          });
        }
      } else if (mode === 'reset') {
        const { error, success } = await resetPassword(email);
        if (error) {
          setMessage({
            text: `Error sending reset link: ${error.message}`,
            type: 'error',
          });
        } else if (success) {
          setMessage({
            text: 'Password reset link sent! Check your email.',
            type: 'success',
          });
        }
      }
    } catch (error) {
      setMessage({
        text: 'An unexpected error occurred. Please try again.',
        type: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      
      <main className="flex-grow flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <Card>
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold text-gray-900">
                {mode === 'signin' ? 'Sign In' : 'Reset Password'}
              </h1>
              <p className="mt-2 text-sm text-gray-600">
                {mode === 'signin'
                  ? 'Enter your email to receive a magic link'
                  : 'Enter your email to receive a password reset link'}
              </p>
            </div>

            {message.text && (
              <div
                className={`mb-6 p-3 rounded-md ${
                  message.type === 'success'
                    ? 'bg-green-50 text-green-800'
                    : 'bg-red-50 text-red-800'
                }`}
              >
                {message.text}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <Input
                label="Email address"
                type="email"
                id="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                fullWidth
              />

              <Button
                type="submit"
                variant="primary"
                isLoading={isLoading}
                fullWidth
                className="mt-2"
              >
                {mode === 'signin' ? 'Send Magic Link' : 'Send Reset Link'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <button
                onClick={() =>
                  setMode(mode === 'signin' ? 'reset' : 'signin')
                }
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {mode === 'signin'
                  ? 'Forgot password?'
                  : 'Back to sign in'}
              </button>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}