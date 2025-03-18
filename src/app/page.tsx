'use client';

import { useAuth } from '@/lib/authContext';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { useTheme } from '@/lib/themeContext';

export default function Home() {
  const { user } = useAuth();
  const { theme } = useTheme();

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className={`text-3xl font-bold ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'} mb-6`}>Welcome to Trainer&apos;s Memory</h1>
      
      {user ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card title="Clients">
            <p className={`${theme === 'light' ? 'text-gray-600' : 'text-gray-300'} mb-4`}>
              Manage your fitness clients, track their progress, and store important information.
            </p>
            <Link href="/clients">
              <Button variant="primary" fullWidth>
                View Clients
              </Button>
            </Link>
          </Card>
          
          <Card title="Workouts">
            <p className={`${theme === 'light' ? 'text-gray-600' : 'text-gray-300'} mb-4`}>
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
            <h2 className={`text-2xl font-semibold ${theme === 'light' ? 'text-gray-800' : 'text-gray-200'} mb-4`}>
              Your Personal Fitness Trainer Assistant
            </h2>
            <p className={`${theme === 'light' ? 'text-gray-600' : 'text-gray-300'} mb-6`}>
              Trainer&apos;s Memory helps fitness professionals manage clients, track workouts, and monitor progress all in one place.
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
  );
}