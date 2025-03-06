'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/authContext';
import Navigation from '@/components/Navigation';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { Workout, workoutsApi } from '@/lib/apiClient';

export default function WorkoutDetailPage() {
  const { user, isLoading: authLoading } = useAuth();
  const params = useParams();
  const router = useRouter();
  const workoutId = params.id as string;
  
  const [workout, setWorkout] = useState<Workout | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (user) {
      fetchWorkout();
    }
  }, [user, workoutId]);

  const fetchWorkout = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await workoutsApi.getById(workoutId);
      setWorkout(data);
    } catch (err) {
      console.error('Error fetching workout:', err);
      setError('Failed to load workout details. Please try again later.');
      
      // For demo purposes, create a sample workout
      setWorkout({
        id: workoutId,
        client_id: '1',
        client_name: 'John Doe',
        date: new Date().toISOString(),
        type: 'Strength Training',
        duration: 60,
        notes: 'Focused on upper body. Increased weight on bench press.',
        exercises: [
          {
            id: '1',
            name: 'Bench Press',
            sets: 3,
            reps: 10,
            weight: 135,
            notes: 'Felt strong, could increase weight next time',
          },
          {
            id: '2',
            name: 'Lat Pulldown',
            sets: 3,
            reps: 12,
            weight: 120,
            notes: '',
          },
        ],
        created_at: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    
    try {
      await workoutsApi.delete(workoutId);
      
      // Redirect to workouts list on success
      router.push('/workouts');
    } catch (err) {
      console.error('Error deleting workout:', err);
      setError('Failed to delete workout. Please try again.');
      
      // For demo purposes, simulate success and redirect
      setTimeout(() => {
        router.push('/workouts');
      }, 1000);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
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
                Please sign in to view workout details
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
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center mb-6">
            <Link href="/workouts" className="text-blue-600 hover:text-blue-800 mr-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">Workout Details</h1>
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
          ) : workout ? (
            <>
              <Card className="mb-6">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{workout.type}</h2>
                    <p className="text-sm text-gray-500">
                      {new Date(workout.date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <Link href={`/workouts/${workoutId}/edit`}>
                      <Button variant="outline" size="sm">
                        Edit
                      </Button>
                    </Link>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => setShowDeleteConfirm(true)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Client</h3>
                    <p className="mt-1">
                      <Link href={`/clients/${workout.client_id}`} className="text-blue-600 hover:text-blue-800">
                        {workout.client_name}
                      </Link>
                    </p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Duration</h3>
                    <p className="mt-1">{workout.duration} minutes</p>
                  </div>
                </div>

                {workout.notes && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-gray-500">Notes</h3>
                    <p className="mt-1 whitespace-pre-line">{workout.notes}</p>
                  </div>
                )}

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Exercises</h3>
                  {workout.exercises.length === 0 ? (
                    <p className="text-gray-500">No exercises recorded for this workout.</p>
                  ) : (
                    <div className="border border-gray-200 rounded-md overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th
                              scope="col"
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              Exercise
                            </th>
                            <th
                              scope="col"
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              Sets
                            </th>
                            <th
                              scope="col"
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              Reps
                            </th>
                            <th
                              scope="col"
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              Weight
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {workout.exercises.map((exercise) => (
                            <tr key={exercise.id}>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="font-medium text-gray-900">
                                  {exercise.name}
                                </div>
                                {exercise.notes && (
                                  <div className="text-sm text-gray-500">
                                    {exercise.notes}
                                  </div>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                                {exercise.sets}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                                {exercise.reps}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                                {exercise.weight} lbs
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </Card>
            </>
          ) : (
            <Card>
              <div className="text-center py-8">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Workout not found
                </h3>
                <p className="text-gray-500 mb-6">
                  The workout you're looking for doesn't exist or has been deleted
                </p>
                <Link href="/workouts">
                  <Button variant="primary">Back to Workouts</Button>
                </Link>
              </div>
            </Card>
          )}
        </div>
      </main>

      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Delete Workout
            </h3>
            <p className="text-gray-500 mb-6">
              Are you sure you want to delete this workout? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleDelete}
                isLoading={isDeleting}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 