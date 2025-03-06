'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/authContext';
import Navigation from '@/components/Navigation';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { getJwtToken } from '@/lib/tokenHelper';

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
  const clientId = params.id as string;
  
  const [client, setClient] = useState<Client | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (user) {
      fetchClient();
    }
  }, [user, clientId]);

  const fetchClient = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Replace with your actual API endpoint
      const response = await fetch(`http://localhost:8000/api/clients/${clientId}`, {
        headers: {
          Authorization: `Bearer ${getJwtToken() || ''}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch client details');
      }
      
      const data = await response.json();
      setClient(data);
    } catch (err) {
      console.error('Error fetching client:', err);
      setError('Failed to load client details. Please try again later.');
      
      // For demo purposes, create a sample client
      setClient({
        id: clientId,
        name: 'John Doe',
        email: 'john@example.com',
        phone: '555-123-4567',
        notes: 'Client is interested in strength training and weight loss. Has previous knee injury.',
        created_at: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    
    try {
      // Replace with your actual API endpoint
      const response = await fetch(`http://localhost:8000/api/clients/${clientId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${getJwtToken() || ''}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete client');
      }
      
      // Redirect to clients list on success
      router.push('/clients');
    } catch (err) {
      console.error('Error deleting client:', err);
      setError('Failed to delete client. Please try again.');
      
      // For demo purposes, simulate success and redirect
      setTimeout(() => {
        router.push('/clients');
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
                Please sign in to view client details
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

              <Card>
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No workouts recorded yet</p>
                  <Link href={`/workouts/new?clientId=${clientId}`}>
                    <Button variant="primary">Record First Workout</Button>
                  </Link>
                </div>
              </Card>
            </>
          ) : (
            <Card>
              <div className="text-center py-8">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Client not found
                </h3>
                <p className="text-gray-500 mb-6">
                  The client you're looking for doesn't exist or has been deleted
                </p>
                <Link href="/clients">
                  <Button variant="primary">Back to Clients</Button>
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
    </div>
  );
} 