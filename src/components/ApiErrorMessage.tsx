'use client';

import React from 'react';
import Button from '@/components/ui/Button';

interface ApiErrorMessageProps {
  error: Error | string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  showFallbackData?: boolean;
}

/**
 * Component to display API error messages with retry options
 */
export default function ApiErrorMessage({
  error,
  onRetry,
  onDismiss,
  showFallbackData = false,
}: ApiErrorMessageProps) {
  if (!error) return null;

  const errorMessage = typeof error === 'string' ? error : error.message;
  
  // Determine if this is a network error
  const isNetworkError = 
    errorMessage.includes('Failed to fetch') || 
    errorMessage.includes('Network Error') ||
    errorMessage.includes('connect to the server');
  
  // Determine if this is an authentication error
  const isAuthError = 
    errorMessage.includes('Unauthorized') || 
    errorMessage.includes('Authentication') ||
    errorMessage.includes('Invalid token') ||
    errorMessage.includes('Invalid API key');

  return (
    <div className="rounded-md bg-red-50 p-4 mb-6">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-red-400"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">
            {isNetworkError
              ? 'Connection Error'
              : isAuthError
              ? 'Authentication Error'
              : 'Error'}
          </h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{errorMessage}</p>
            
            {isNetworkError && (
              <p className="mt-2">
                The server might be down or your internet connection might be unstable.
                {showFallbackData && " We're showing you cached data in the meantime."}
              </p>
            )}
            
            {isAuthError && (
              <p className="mt-2">
                Your session may have expired. Try signing in again.
              </p>
            )}
          </div>
          
          <div className="mt-4 flex gap-2">
            {onRetry && (
              <Button
                variant="outline"
                onClick={onRetry}
                className="text-sm px-2 py-1 h-auto"
              >
                Retry
              </Button>
            )}
            
            {isAuthError && (
              <Button
                variant="primary"
                onClick={() => window.location.href = '/signin'}
                className="text-sm px-2 py-1 h-auto"
              >
                Sign In
              </Button>
            )}
            
            {onDismiss && (
              <Button
                variant="outline"
                onClick={onDismiss}
                className="text-sm px-2 py-1 h-auto"
              >
                Dismiss
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 