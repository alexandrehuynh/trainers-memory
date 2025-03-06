'use client';

import { useAuth } from '@/lib/authContext';
import Navigation from '@/components/Navigation';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';

export default function Home() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      
      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Welcome to Trainer's Memory</h1>
          
          {user ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card title="Clients">
                <p className="text-gray-600 mb-4">
                  Manage your fitness clients, track their progress, and store important information.
                </p>
                <Link href="/clients">
                  <Button variant="primary" fullWidth>
                    View Clients
                  </Button>
                </Link>
              </Card>
              
              <Card title="Workouts">
                <p className="text-gray-600 mb-4">
                  Create workout templates, log completed sessions, and track progress over time.
                </p>
                <Link href="/workouts">
                  <Button variant="primary" fullWidth>
                    Manage Workouts
                  </Button>
                </Link>
              </Card>
            </div>
          ) : (
            <Card>
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                  Your Personal Fitness Trainer Assistant
                </h2>
                <p className="text-gray-600 mb-6">
                  Trainer's Memory helps fitness professionals manage clients, track workouts, and monitor progress all in one place.
                </p>
                <Link href="/signin">
                  <Button variant="primary" size="lg">
                    Get Started
                  </Button>
                </Link>
              </div>
            </Card>
          )}
        </div>
      </main>
      
      <footer className="bg-white border-t border-gray-200 py-6">
        <div className="container mx-auto px-4">
          <p className="text-center text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} Trainer's Memory. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}