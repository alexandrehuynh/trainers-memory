'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/authContext';
import { useTheme } from '@/lib/themeContext';
import Button from './ui/Button';

export default function Navigation() {
  const { user, signOut } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <nav className={`${theme === 'light' ? 'bg-white border-gray-200' : 'bg-gray-800 border-gray-700'} shadow-sm border-b`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className={`text-xl font-bold ${theme === 'light' ? 'text-blue-600' : 'text-blue-400'}`}>
                Trainer&apos;s Memory
              </Link>
            </div>
            {user && (
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  href="/clients"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium ${theme === 'light' ? 'text-gray-500 hover:text-gray-700 hover:border-gray-300' : 'text-gray-300 hover:text-white hover:border-gray-500'}`}
                >
                  Clients
                </Link>
                <Link
                  href="/workouts"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium ${theme === 'light' ? 'text-gray-500 hover:text-gray-700 hover:border-gray-300' : 'text-gray-300 hover:text-white hover:border-gray-500'}`}
                >
                  Workouts
                </Link>
              </div>
            )}
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            {/* Theme toggle button */}
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-md ${theme === 'light' ? 'text-gray-500 hover:text-gray-700' : 'text-gray-400 hover:text-gray-200'} focus:outline-none mr-4`}
              aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              {theme === 'light' ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                </svg>
              )}
            </button>
            
            {user ? (
              <div className="flex items-center space-x-4">
                <span className={`text-sm ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'}`}>{user.email}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={signOut}
                  className={`${theme === 'light' ? 'text-gray-700 border-gray-400' : 'text-gray-200 border-gray-500'}`}
                >
                  Sign Out
                </Button>
              </div>
            ) : (
              <Link href="/signin">
                <Button variant="primary" size="sm">
                  Sign In
                </Button>
              </Link>
            )}
          </div>
          <div className="-mr-2 flex items-center sm:hidden">
            {/* Mobile theme toggle */}
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-md ${theme === 'light' ? 'text-gray-500 hover:text-gray-700' : 'text-gray-400 hover:text-gray-200'} focus:outline-none`}
              aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              {theme === 'light' ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                </svg>
              )}
            </button>
            <button
              onClick={toggleMenu}
              className={`inline-flex items-center justify-center p-2 rounded-md ${theme === 'light' ? 'text-gray-400 hover:text-gray-500 hover:bg-gray-100' : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700'} focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500`}
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className={`${isMenuOpen ? 'hidden' : 'block'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              <svg
                className={`${isMenuOpen ? 'block' : 'hidden'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className={`${isMenuOpen ? 'block' : 'hidden'} sm:hidden`}>
        {user && (
          <div className="pt-2 pb-3 space-y-1">
            <Link
              href="/clients"
              className={`block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium ${theme === 'light' ? 'text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800' : 'text-gray-300 hover:bg-gray-700 hover:border-gray-600 hover:text-white'}`}
            >
              Clients
            </Link>
            <Link
              href="/workouts"
              className={`block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium ${theme === 'light' ? 'text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800' : 'text-gray-300 hover:bg-gray-700 hover:border-gray-600 hover:text-white'}`}
            >
              Workouts
            </Link>
          </div>
        )}
        <div className={`pt-4 pb-3 border-t ${theme === 'light' ? 'border-gray-200' : 'border-gray-700'}`}>
          {user ? (
            <div className="flex items-center px-4">
              <div className="flex-shrink-0">
                <div className={`h-10 w-10 rounded-full ${theme === 'light' ? 'bg-gray-200' : 'bg-gray-700'} flex items-center justify-center`}>
                  <span className={`${theme === 'light' ? 'text-gray-500' : 'text-gray-300'} font-medium`}>
                    {user.email?.charAt(0).toUpperCase()}
                  </span>
                </div>
              </div>
              <div className="ml-3">
                <div className={`text-base font-medium ${theme === 'light' ? 'text-gray-800' : 'text-gray-200'}`}>
                  {user.email}
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="ml-auto"
                onClick={signOut}
              >
                Sign Out
              </Button>
            </div>
          ) : (
            <div className="px-4">
              <Link href="/signin">
                <Button variant="primary" fullWidth>
                  Sign In
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
} 