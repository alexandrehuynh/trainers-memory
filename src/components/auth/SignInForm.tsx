'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/authContext';
import Card from '@/components/ui/Card';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

export default function SignInForm() {
  const { signIn, resetPassword, register, signInWithPassword } = useAuth();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | '' }>({
    text: '',
    type: '',
  });
  const [mode, setMode] = useState<'magic-link' | 'password' | 'register' | 'reset'>('magic-link');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage({ text: '', type: '' });

    try {
      if (mode === 'magic-link') {
        // Send magic link
        const { error, success } = await signIn(email);
        if (error) {
          setMessage({
            text: `Error sending magic link: ${error.message}`,
            type: 'error',
          });
        } else if (success) {
          setMessage({
            text: 'Magic link sent! Check your email for a login link.',
            type: 'success',
          });
        }
      } else if (mode === 'password') {
        // Implement password authentication
        const { error, success } = await signInWithPassword(email, password);
        if (error) {
          setMessage({
            text: `Authentication failed: ${error.message}`,
            type: 'error',
          });
        } else if (success) {
          setMessage({
            text: 'Sign in successful! Redirecting...',
            type: 'success',
          });
          // The auth state change listener will handle redirect
        }
      } else if (mode === 'register') {
        // Validate passwords match
        if (password !== confirmPassword) {
          setMessage({
            text: 'Passwords do not match',
            type: 'error',
          });
          setIsLoading(false);
          return;
        }

        // Enhanced password validation
        if (password.length < 8) {
          setMessage({
            text: 'Password must be at least 8 characters long',
            type: 'error',
          });
          setIsLoading(false);
          return;
        }
        
        // Check for password complexity
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumbers = /[0-9]/.test(password);
        const hasSpecialChar = /[^A-Za-z0-9]/.test(password);
        
        if (!(hasUppercase && hasLowercase && hasNumbers)) {
          setMessage({
            text: 'Password must contain at least one uppercase letter, one lowercase letter, and one number',
            type: 'error',
          });
          setIsLoading(false);
          return;
        }
        
        if (!hasSpecialChar) {
          setMessage({
            text: 'Password must contain at least one special character',
            type: 'error',
          });
          setIsLoading(false);
          return;
        }

        // Call register method from auth context
        const { error, success, needsEmailConfirmation } = await register(email, password);
        if (error) {
          setMessage({
            text: `Registration failed: ${error.message}`,
            type: 'error',
          });
        } else if (success) {
          if (needsEmailConfirmation) {
            setMessage({
              text: 'Registration successful! Please check your email to confirm your account.',
              type: 'success',
            });
          } else {
            setMessage({
              text: 'Registration successful! You can now sign in.',
              type: 'success',
            });
            // Switch to password mode for immediate login
            setMode('password');
          }
        }
      } else if (mode === 'reset') {
        const { error, success } = await resetPassword(email);
        if (error) {
          setMessage({
            text: `Error sending reset instructions: ${error.message}`,
            type: 'error',
          });
        } else if (success) {
          setMessage({
            text: 'Password reset instructions sent! Check your email.',
            type: 'success',
          });
        }
      }
    } catch (err: any) {
      setMessage({
        text: `An unexpected error occurred: ${err.message}`,
        type: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to render the appropriate title and description
  const renderHeaderText = () => {
    switch (mode) {
      case 'magic-link':
        return {
          title: 'Sign In with Magic Link',
          description: "We'll email you a secure link - just click it to sign in instantly without a password."
        };
      case 'password':
        return {
          title: 'Sign In with Password',
          description: "Enter your email and password to access your account."
        };
      case 'register':
        return {
          title: 'Create Account',
          description: "Set up a new account with a password for future sign-ins."
        };
      case 'reset':
        return {
          title: 'Reset Password',
          description: "We'll email you instructions to reset your password."
        };
      default:
        return {
          title: 'Sign In',
          description: ""
        };
    }
  };

  const headerText = renderHeaderText();

  return (
    <Card className="w-full max-w-md mx-auto">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{headerText.title}</h1>
        <p className="text-gray-600 mt-2">
          {headerText.description}
        </p>
      </div>

      {message.text && (
        <div
          className={`mb-6 p-4 rounded-md ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          {/* Password input (only for password and register modes) */}
          {(mode === 'password' || mode === 'register') && (
            <div className="space-y-2">
              <Input
                label="Password"
                type="password"
                placeholder="Your password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              />
              
              {/* Password requirements helper text */}
              {mode === 'register' && (
                <div className="text-xs text-gray-500 mt-1">
                  <p>Password must:</p>
                  <ul className="list-disc list-inside pl-2">
                    <li>Be at least 8 characters long</li>
                    <li>Include at least one uppercase letter</li>
                    <li>Include at least one lowercase letter</li>
                    <li>Include at least one number</li>
                    <li>Include at least one special character</li>
                  </ul>
                </div>
              )}
            </div>
          )}

          {mode === 'register' && (
            <Input
              label="Confirm Password"
              type="password"
              placeholder="Confirm your password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          )}

          <div className="flex justify-between space-x-3 pt-2">
            {/* Authentication method selector */}
            <div className="text-sm space-x-4 flex items-center flex-wrap">
              <div 
                className={`cursor-pointer ${mode === 'magic-link' ? 'text-blue-600 font-medium' : 'text-gray-500 hover:text-gray-700'} mr-2 mb-1`}
                onClick={() => setMode('magic-link')}
              >
                Magic Link
              </div>
              <div 
                className={`cursor-pointer ${mode === 'password' ? 'text-blue-600 font-medium' : 'text-gray-500 hover:text-gray-700'} mr-2 mb-1`}
                onClick={() => setMode('password')}
              >
                Password
              </div>
              <div 
                className={`cursor-pointer ${mode === 'register' ? 'text-blue-600 font-medium' : 'text-gray-500 hover:text-gray-700'} mb-1`}
                onClick={() => setMode('register')}
              >
                Register
              </div>
            </div>
            
            <div 
              className="text-sm text-blue-600 hover:text-blue-800 cursor-pointer"
              onClick={() => setMode(mode === 'reset' ? 'magic-link' : 'reset')}
            >
              {mode === 'reset' ? 'Back to sign in' : 'Forgot password?'}
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            fullWidth
            isLoading={isLoading}
            disabled={
              !email || 
              (mode === 'password' && !password) ||
              (mode === 'register' && (!password || !confirmPassword))
            }
          >
            {mode === 'magic-link' && 'Send Magic Link'}
            {mode === 'password' && 'Sign In'}
            {mode === 'register' && 'Create Account'}
            {mode === 'reset' && 'Reset Password'}
          </Button>
        </div>
      </form>

      {mode === 'magic-link' && (
        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <h3 className="text-sm font-medium text-blue-800">What is a Magic Link?</h3>
          <p className="text-sm text-blue-700 mt-1">
            A magic link is a secure, passwordless way to sign in. We'll send a special link to your email that will 
            automatically log you in when clicked - no password needed. It's both more secure and more convenient!
          </p>
        </div>
      )}
    </Card>
  );
}