'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/authContext';
import { useTheme } from '@/lib/themeContext';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { getJwtToken } from '@/lib/tokenHelper';
import ImportClientsModal from '@/components/ImportClientsModal';
import { Client, clientsApi } from '@/lib/apiClient';

export default function ClientsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { theme } = useTheme();
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);
  
  // Development mode flag - set to true to use sample data and avoid API calls
  const USE_SAMPLE_DATA = false; // Toggle this when backend is ready

  useEffect(() => {
    // Only fetch clients if user is authenticated
    if (user) {
      fetchClients();
    }
  }, [user]);

  const fetchClients = async () => {
    setIsLoading(true);
    setError(null);
    
    // If we're in development mode with sample data, skip the API call
    if (USE_SAMPLE_DATA) {
      console.log('Development mode: Using sample client data');
      setClients([
        {
          id: '1',
          name: 'John Doe',
          email: 'john@example.com',
          phone: '555-123-4567',
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          name: 'Jane Smith',
          email: 'jane@example.com',
          phone: '555-987-6543',
          created_at: new Date().toISOString(),
        },
        {
          id: '3',
          name: 'Alex Johnson',
          email: 'alex@example.com',
          phone: '555-456-7890',
          created_at: new Date().toISOString(),
        },
      ]);
      setIsLoading(false);
      return;
    }
    
    try {
      console.log('Attempting to fetch clients from API...');
      // Using the updated client API which already handles the response format
      const clients = await clientsApi.getAll();
      setClients(clients);
      console.log('Successfully fetched clients from API:', clients);
    } catch (err) {
      console.error('Error fetching clients:', err);
      setError('Failed to load clients from API. Using sample data instead.');
      console.log('Using sample client data for development');
      // For demo purposes, add some sample clients
      setClients([
        {
          id: '1',
          name: 'John Doe',
          email: 'john@example.com',
          phone: '555-123-4567',
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          name: 'Jane Smith',
          email: 'jane@example.com',
          phone: '555-987-6543',
          created_at: new Date().toISOString(),
        },
        {
          id: '3',
          name: 'Alex Johnson',
          email: 'alex@example.com',
          phone: '555-456-7890',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImportSuccess = (count: number) => {
    setShowImportModal(false);
    // Show success message
    alert(`Successfully imported ${count} clients`);
    // Refresh the client list
    fetchClients();
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
          <h2 className={`text-xl font-semibold ${theme === 'light' ? 'text-gray-800' : 'text-gray-200'} mb-4`}>
            Please sign in to view clients
          </h2>
          <Link href="/signin">
            <Button variant="primary">Sign In</Button>
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className={`text-2xl font-bold ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'}`}>Clients</h1>
        <div className="flex space-x-2">
          <Button 
            variant="outline"
            onClick={() => setShowImportModal(true)}
          >
            Import from Spreadsheet
          </Button>
          <Link href="/clients/new">
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
              Add New Client
            </Button>
          </Link>
        </div>
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
      ) : clients.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <h3 className={`text-lg font-medium ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'} mb-2`}>
              No clients yet
            </h3>
            <p className={`${theme === 'light' ? 'text-gray-500' : 'text-gray-400'} mb-6`}>
              Get started by adding your first client
            </p>
            <Link href="/clients/new">
              <Button variant="primary">Add New Client</Button>
            </Link>
          </div>
        </Card>
      ) : (
        <div className={`${theme === 'light' ? 'bg-white' : 'bg-gray-800'} shadow-sm rounded-lg overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className={`${theme === 'light' ? 'bg-gray-50' : 'bg-gray-700'}`}>
                <tr>
                  <th
                    scope="col"
                    className={`px-6 py-3 text-left text-xs font-medium ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'} uppercase tracking-wider`}
                  >
                    Name
                  </th>
                  <th
                    scope="col"
                    className={`px-6 py-3 text-left text-xs font-medium ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'} uppercase tracking-wider`}
                  >
                    Email
                  </th>
                  <th
                    scope="col"
                    className={`px-6 py-3 text-left text-xs font-medium ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'} uppercase tracking-wider`}
                  >
                    Phone
                  </th>
                  <th
                    scope="col"
                    className={`px-6 py-3 text-left text-xs font-medium ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'} uppercase tracking-wider`}
                  >
                    Added
                  </th>
                  <th
                    scope="col"
                    className={`px-6 py-3 text-right text-xs font-medium ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'} uppercase tracking-wider`}
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className={`${theme === 'light' ? 'bg-white divide-y divide-gray-200' : 'bg-gray-800 divide-y divide-gray-700'}`}>
                {clients.map((client) => (
                  <tr key={client.id} className={`${theme === 'light' ? 'hover:bg-gray-50' : 'hover:bg-gray-700'}`}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`font-medium ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'}`}>
                        {client.name}
                      </div>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'}`}>
                      {client.email}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'}`}>
                      {client.phone || '-'}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap ${theme === 'light' ? 'text-gray-500' : 'text-gray-300'}`}>
                      {new Date(client.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        href={`/clients/${client.id}`}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        View
                      </Link>
                      <Link
                        href={`/clients/${client.id}/edit`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Edit
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showImportModal && (
        <ImportClientsModal
          isOpen={showImportModal}
          onClose={() => setShowImportModal(false)}
          onSuccess={handleImportSuccess}
        />
      )}
    </div>
  );
} 