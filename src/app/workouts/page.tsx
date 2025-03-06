'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/authContext';
import Navigation from '@/components/Navigation';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { getJwtToken } from '@/lib/tokenHelper';

interface Workout {
  id: string;
  client_name: string;
  client_id: string;
  date: string;
  type: string;
  duration: number;
  notes?: string;
}

export default function WorkoutsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      fetchWorkouts();
    }
  }, [user]);

  const fetchWorkouts = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Replace with your actual API endpoint
      const response = await fetch('http://localhost:8000/api/workouts', {
        headers: {
          Authorization: `Bearer ${getJwtToken() || ''}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch workouts');
      }
      
      const data = await response.json();
      setWorkouts(data);
    } catch (err) {
      console.error('Error fetching workouts:', err);
      setError('Failed to load workouts. Please try again later.');
      
      // For demo purposes, add some sample workouts
      setWorkouts([
        {
          id: '1',
          client_name: 'John Doe',
          client_id: '1',
          date: new Date().toISOString(),
          type: 'Strength Training',
          duration: 60,
          notes: 'Focused on upper body. Increased weight on bench press.',
        },
        {
          id: '2',
          client_name: 'Jane Smith',
          client_id: '2',
          date: new Date(Date.now() - 86400000).toISOString(), // Yesterday
          type: 'Cardio',
          duration: 45,
          notes: '5k run followed by stretching.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navigation />
        <main className="flex-grow flex items-center justify-center">
          <Card>
            <div className="text-center p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Please sign in to view workouts
              </h2>
              <Link href="/signin">
                <Button variant="primary">Sign In</Button>
              </Link>
            </div>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      
      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Workouts</h1>
            <Link href="/workouts/new">
              <Button variant="primary">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 mr-2"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
                    clipRule="evenodd"
                  />
                </svg>
                Add New Workout
              </Button>
            </Link>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-800 rounded-md">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : workouts.length === 0 ? (
            <Card>
              <div className="text-center py-12">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No workouts recorded yet
                </h3>
                <p className="text-gray-500 mb-6">
                  Get started by adding your first workout
                </p>
                <Link href="/workouts/new">
                  <Button variant="primary">Add New Workout</Button>
                </Link>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {workouts.map((workout) => (
                <Link key={workout.id} href={`/workouts/${workout.id}`}>
                  <Card className="h-full hover:shadow-md transition-shadow cursor-pointer">
                    <div className="flex flex-col h-full">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {workout.type}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {new Date(workout.date).toLocaleDateString()}
                          </p>
                        </div>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {workout.duration} min
                        </span>
                      </div>
                      
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-700">
                          Client: {workout.client_name}
                        </p>
                      </div>
                      
                      {workout.notes && (
                        <p className="text-sm text-gray-600 line-clamp-3 mb-4">
                          {workout.notes}
                        </p>
                      )}
                      
                      <div className="mt-auto text-right">
                        <span className="text-blue-600 text-sm font-medium">
                          View Details →
                        </span>
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
} 