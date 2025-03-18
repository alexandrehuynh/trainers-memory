'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/authContext';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { workoutsApi, Workout } from '@/lib/apiClient';
import { clientsApi } from '@/lib/apiClient';

interface Client {
  id: string;
  name: string;
  email: string;
  phone?: string;
  notes?: string;
  created_at: string;
}

export default function ClientDetailPage() {
  const { user, isLoading: authLoading } = useAuth();
  const params = useParams();
  const router = useRouter();
  const clientId = params?.id as string || '';
  
  const [client, setClient] = useState<Client | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [workoutsLoading, setWorkoutsLoading] = useState(false);

  const fetchClient = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const client = await clientsApi.getById(clientId);
      setClient(client);
      console.log('Successfully fetched client from API:', client);
    } catch (err) {
      console.error('Error fetching client:', err);
      setError('Failed to load client. Please try again later.');
      
      // For demo purposes
      setClient({
        id: clientId || 'sample-id',
        name: 'John Doe',
        email: 'john@example.com',
        phone: '555-123-4567',
        notes: 'Regular client since 2022',
        created_at: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  }, [clientId]);

  const fetchClientWorkouts = useCallback(async () => {
    setWorkoutsLoading(true);
    try {
      const workouts = await workoutsApi.getByClientId(clientId);
      setWorkouts(workouts);
      console.log('Successfully fetched client workouts from API:', workouts);
    } catch (err) {
      console.error('Error fetching client workouts:', err);
      
      // For demo purposes, add sample workouts
      setWorkouts([
        {
          id: '1',
          client_id: clientId,
          client_name: client?.name || 'Client',
          date: new Date().toISOString(),
          type: 'Strength Training',
          duration: 60,
          notes: 'Upper body focus',
          exercises: [],
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          client_id: clientId,
          client_name: client?.name || 'Client',
          date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week ago
          type: 'Cardio',
          duration: 45,
          notes: '5k run',
          exercises: [],
          created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
      ]);
    } finally {
      setWorkoutsLoading(false);
    }
  }, [clientId, client]);

  useEffect(() => {
    if (user) {
      fetchClient();
    }
  }, [user, clientId, fetchClient]);

  useEffect(() => {
    if (user && client) {
      fetchClientWorkouts();
    }
  }, [user, client, clientId, fetchClientWorkouts]);

  const handleDelete = async () => {
    setIsDeleting(true);
    
    try {
      await clientsApi.delete(clientId);
      
      router.push('/clients');
    } catch (err) {
      console.error('Error deleting client:', err);
      setError('Failed to delete client. Please try again.');
      
      if (process.env.NODE_ENV === 'development') {
        setTimeout(() => {
          setShowDeleteConfirm(false);
          router.push('/clients');
        }, 1000);
      }
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
      <Card>
        <div className="text-center p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Please sign in to view client details
          </h2>
          <Link href="/signin">
            <Button variant="primary">Sign In</Button>
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <>
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center mb-6">
          <Link href="/clients" className="text-blue-600 hover:text-blue-800 mr-2">
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
          <h1 className="text-2xl font-bold text-gray-900">Client Details</h1>
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
        ) : client ? (
          <>
            <Card className="mb-6">
              <div className="flex justify-between items-start mb-6">
                <h2 className="text-xl font-semibold text-gray-900">{client.name}</h2>
                <div className="flex space-x-2">
                  <Link href={`/clients/${clientId}/edit`}>
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

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Email</h3>
                  <p className="mt-1">{client.email}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Phone</h3>
                  <p className="mt-1">{client.phone || 'Not provided'}</p>
                </div>
                <div className="md:col-span-2">
                  <h3 className="text-sm font-medium text-gray-500">Notes</h3>
                  <p className="mt-1 whitespace-pre-line">
                    {client.notes || 'No notes available'}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Client since</h3>
                  <p className="mt-1">
                    {new Date(client.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </Card>

            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Workouts</h2>
              <Link href={`/workouts/new?clientId=${clientId}`}>
                <Button variant="primary" size="sm">
                  Add Workout
                </Button>
              </Link>
            </div>

            {workoutsLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : workouts.length === 0 ? (
              <Card>
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No workouts recorded yet</p>
                  <Link href={`/workouts/new?clientId=${clientId}`}>
                    <Button variant="primary">Record First Workout</Button>
                  </Link>
                </div>
              </Card>
            ) : (
              <div className="space-y-4">
                {workouts.map((workout) => (
                  <Link key={workout.id} href={`/workouts/${workout.id}`}>
                    <Card className="hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium text-gray-900">{workout.type}</h3>
                          <p className="text-sm text-gray-500">
                            {new Date(workout.date).toLocaleDateString()}
                          </p>
                        </div>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {workout.duration} min
                        </span>
                      </div>
                      {workout.notes && (
                        <p className="mt-2 text-sm text-gray-600 line-clamp-2">{workout.notes}</p>
                      )}
                    </Card>
                  </Link>
                ))}
                <div className="text-center pt-4">
                  <Link href={`/workouts?clientId=${clientId}`}>
                    <Button variant="outline">View All Workouts</Button>
                  </Link>
                </div>
              </div>
            )}
          </>
        ) : (
          <Card>
            <div className="text-center py-8">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Client not found
              </h3>
              <p className="text-gray-500 mb-6">
                The client you&apos;re looking for doesn&apos;t exist or has been deleted
              </p>
              <Link href="/clients">
                <Button variant="primary">Back to Clients</Button>
              </Link>
            </div>
          </Card>
        )}
      </div>

      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Delete Client
            </h3>
            <p className="text-gray-500 mb-6">
              Are you sure you want to delete {client?.name}? This action cannot be undone.
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
    </>
  );
} 