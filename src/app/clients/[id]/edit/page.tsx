'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/authContext';
import Card from '@/components/ui/Card';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { getJwtToken } from '@/lib/tokenHelper';

interface ClientFormData {
  name: string;
  email: string;
  phone: string;
  notes: string;
}

export default function EditClientPage() {
  const { user, isLoading: authLoading } = useAuth();
  const params = useParams();
  const router = useRouter();
  const clientId = params.id as string;
  
  const [formData, setFormData] = useState<ClientFormData>({
    name: '',
    email: '',
    phone: '',
    notes: '',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      fetchClient();
    }
  }, [user, clientId]);

  const fetchClient = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/clients/${clientId}`, {
        headers: {
          Authorization: `Bearer ${getJwtToken() || ''}`,
          'X-API-Key': 'test_key_12345'
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch client');
      }
      
      const data = await response.json();
      setFormData({
        name: data.name,
        email: data.email,
        phone: data.phone || '',
        notes: data.notes || '',
      });
    } catch (err) {
      console.error('Error fetching client:', err);
      setError('Failed to load client. Please try again later.');
      
      // For demo purposes
      setFormData({
        name: 'John Doe',
        email: 'john@example.com',
        phone: '555-123-4567',
        notes: 'Regular client since 2022',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/v1/clients/${clientId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getJwtToken() || ''}`,
          'X-API-Key': 'test_key_12345'
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update client');
      }
      
      // Redirect to client detail page on success
      router.push(`/clients/${clientId}`);
    } catch (err) {
      console.error('Error updating client:', err);
      setError('Failed to update client. Please try again.');
    } finally {
      setIsSaving(false);
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
            Please sign in to edit clients
          </h2>
          <Link href="/signin">
            <Button variant="primary">Sign In</Button>
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center mb-6">
        <Link href={`/clients/${clientId}`} className="text-blue-600 hover:text-blue-800 mr-2">
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
        <h1 className="text-2xl font-bold text-gray-900">Edit Client</h1>
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
      ) : (
        <Card>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <Input
                label="Name"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Client's full name"
              />

              <Input
                label="Email"
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="client@example.com"
              />

              <Input
                label="Phone"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="(555) 123-4567"
              />

              <div className="mb-4">
                <label
                  htmlFor="notes"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Notes
                </label>
                <textarea
                  id="notes"
                  name="notes"
                  rows={4}
                  value={formData.notes}
                  onChange={handleChange}
                  placeholder="Additional information about the client"
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                ></textarea>
              </div>

              <div className="flex justify-end space-x-3">
                <Link href={`/clients/${clientId}`}>
                  <Button variant="outline" type="button">
                    Cancel
                  </Button>
                </Link>
                <Button
                  variant="primary"
                  type="submit"
                  isLoading={isSaving}
                >
                  Save Changes
                </Button>
              </div>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
} 