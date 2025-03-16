'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/authContext';
import Card from '@/components/ui/Card';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { getJwtToken } from '@/lib/tokenHelper';
import { Client, clientsApi, Exercise } from '@/lib/apiClient';
import { workoutsApi } from '@/lib/apiClient';
import WorkoutTemplates from '@/components/WorkoutTemplates';

interface WorkoutFormData {
  client_id: string;
  client_name?: string;
  date: string;
  type: string;
  duration: number;
  notes: string;
  exercises: Exercise[];
  customTypeName?: string;
}

// Define WorkoutTemplate interface to match what's used in WorkoutTemplates
interface WorkoutTemplate {
  id: string;
  name: string;
  type: string;
  exercises: Exercise[];
  createdAt: Date;
}

// Create a client component that uses useSearchParams
function WorkoutPageContent() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const clientIdParam = searchParams?.get('clientId') || null;
  
  const [clients, setClients] = useState<Client[]>([]);
  const [formData, setFormData] = useState<WorkoutFormData>({
    client_id: searchParams?.get('client_id') || '',
    date: new Date().toISOString().split('T')[0],
    type: 'Strength',
    duration: 60,
    notes: '',
    exercises: [
      {
        id: crypto.randomUUID(),
        name: '',
        sets: 3,
        reps: 10,
        weight: 0,
        notes: '',
      },
    ],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);

  useEffect(() => {
    if (user) {
      fetchClients();
    }
  }, [user]);

  const fetchClients = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Use the clientsApi to fetch clients
      const clientsData = await clientsApi.getAll();
      setClients(clientsData);
    } catch (err) {
      console.error('Error fetching clients:', err);
      setError('Failed to load clients. Please try again later.');
      // Sample data for development purposes
      setClients([
        { id: '1', name: 'John Doe', email: 'john@example.com', phone: '', created_at: '', updated_at: '' },
        { id: '2', name: 'Jane Smith', email: 'jane@example.com', phone: '', created_at: '', updated_at: '' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleExerciseChange = (id: string, field: keyof Exercise, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      exercises: prev.exercises.map((exercise) =>
        exercise.id === id ? { ...exercise, [field]: value } : exercise
      ),
    }));
  };

  const addExercise = () => {
    setFormData((prev) => ({
      ...prev,
      exercises: [
        ...prev.exercises,
        {
          id: crypto.randomUUID(),
          name: '',
          sets: 3,
          reps: 10,
          weight: 0,
          notes: '',
        },
      ],
    }));
  };

  const removeExercise = (id: string) => {
    setFormData((prev) => ({
      ...prev,
      exercises: prev.exercises.filter((exercise) => exercise.id !== id),
    }));
  };

  const handleTemplateSelect = (template: WorkoutTemplate) => {
    setFormData((prev) => ({
      ...prev,
      type: template.type,
      exercises: template.exercises,
    }));
    
    setShowTemplates(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // If already saving, prevent double submission
    if (isSaving) return;
    
    // Validate custom workout name if type is Custom
    if (formData.type === 'Custom' && (!formData.customTypeName || formData.customTypeName.trim() === '')) {
      setError('Please enter a name for your custom workout type');
      return;
    }
    
    setIsSaving(true);
    setError(null);

    try {
      // Find the selected client to get their name
      const selectedClient = clients.find(client => client.id === formData.client_id);
      
      // Prepare workout data
      let workoutType = formData.type;
      
      // If type is Custom and a custom name is provided, use the custom name
      if (formData.type === 'Custom' && formData.customTypeName) {
        workoutType = formData.customTypeName;
      }
      
      // Use the workoutsApi instead of direct fetch
      const workoutData = {
        ...formData,
        client_name: selectedClient?.name || 'Unknown Client',
        type: workoutType
      };
      
      const result = await workoutsApi.create(workoutData);
      
      // Redirect to workouts list with timestamp to force refresh
      if (result && result.id) {
        router.push(`/workouts/${result.id}?t=${Date.now()}`);
      } else {
        router.push(`/workouts?t=${Date.now()}`);
      }
    } catch (err: any) {
      console.error('Error creating workout:', err);
      // Display a more specific error message if available
      const errorMessage = err.message || 'Failed to create workout. Please try again.';
      setError(errorMessage);
      // Allow the user to try again by resetting the saving state
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
            Please sign in to create workouts
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
        <h1 className="text-2xl font-bold text-gray-900">Create New Workout</h1>
        
        <div className="ml-auto">
          <Button
            variant="outline"
            onClick={() => setShowTemplates(!showTemplates)}
          >
            {showTemplates ? 'Hide Templates' : 'Use Template'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-800 rounded-md">
          {error}
        </div>
      )}

      {showTemplates && (
        <div className="mb-6">
          <WorkoutTemplates onSelectTemplate={handleTemplateSelect} />
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : Array.isArray(clients) && clients.length > 0 ? (
        <Card>
          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="client_id"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Client
                  </label>
                  <select
                    id="client_id"
                    name="client_id"
                    value={formData.client_id}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select a client</option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.name}
                      </option>
                    ))}
                  </select>
                </div>

                <Input
                  label="Date"
                  type="date"
                  id="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="type"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Workout Type
                  </label>
                  <select
                    id="type"
                    name="type"
                    value={formData.type}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="Strength">Strength</option>
                    <option value="Cardio">Cardio</option>
                    <option value="Flexibility">Flexibility</option>
                    <option value="HIIT">HIIT</option>
                    <option value="Recovery">Recovery</option>
                    <option value="Custom">Custom</option>
                  </select>
                  
                  {formData.type === 'Custom' && (
                    <div className="mt-2">
                      <label
                        htmlFor="customType"
                        className="block text-sm font-medium text-gray-700 mb-1"
                      >
                        Custom Workout Name
                      </label>
                      <input
                        type="text"
                        id="customType"
                        className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Enter custom workout name"
                        value={formData.customTypeName || ''}
                        onChange={(e) => {
                          const customName = e.target.value;
                          setFormData((prev) => ({
                            ...prev,
                            customTypeName: customName
                          }));
                        }}
                        required
                      />
                    </div>
                  )}
                </div>

                <Input
                  label="Duration (minutes)"
                  type="number"
                  id="duration"
                  name="duration"
                  value={formData.duration.toString()}
                  onChange={handleChange}
                  required
                  min="1"
                  max="300"
                />
              </div>

              <div>
                <label
                  htmlFor="notes"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Notes
                </label>
                <textarea
                  id="notes"
                  name="notes"
                  rows={3}
                  value={formData.notes || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter any additional notes about this workout"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-lg font-medium text-gray-900">Exercises</h3>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addExercise}
                  >
                    Add Exercise
                  </Button>
                </div>

                {formData.exercises.length === 0 ? (
                  <div className="text-center py-6 bg-gray-50 rounded-md">
                    <p className="text-gray-500">No exercises added yet</p>
                    <Button
                      type="button"
                      variant="outline"
                      className="mt-2"
                      onClick={addExercise}
                    >
                      Add Your First Exercise
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {formData.exercises.map((exercise, index) => (
                      <div
                        key={exercise.id}
                        className="border border-gray-200 rounded-md p-4"
                      >
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="text-md font-medium text-gray-900">
                            Exercise {index + 1}
                          </h4>
                          <Button
                            type="button"
                            variant="danger"
                            onClick={() => removeExercise(exercise.id)}
                            className="px-2 py-1 text-sm"
                          >
                            Remove
                          </Button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                          <Input
                            label="Exercise Name"
                            type="text"
                            value={exercise.name}
                            onChange={(e) =>
                              handleExerciseChange(
                                exercise.id,
                                'name',
                                e.target.value
                              )
                            }
                            placeholder="e.g. Bench Press"
                            required
                          />

                          <div className="grid grid-cols-3 gap-2">
                            <Input
                              label="Sets"
                              type="number"
                              value={exercise.sets.toString()}
                              onChange={(e) =>
                                handleExerciseChange(
                                  exercise.id,
                                  'sets',
                                  parseInt(e.target.value)
                                )
                              }
                              required
                              min="1"
                              max="100"
                            />
                            <Input
                              label="Reps"
                              type="number"
                              value={exercise.reps.toString()}
                              onChange={(e) =>
                                handleExerciseChange(
                                  exercise.id,
                                  'reps',
                                  parseInt(e.target.value)
                                )
                              }
                              required
                              min="1"
                              max="1000"
                            />
                            <Input
                              label="Weight (lbs)"
                              type="number"
                              value={exercise.weight.toString()}
                              onChange={(e) =>
                                handleExerciseChange(
                                  exercise.id,
                                  'weight',
                                  parseInt(e.target.value)
                                )
                              }
                              required
                              min="0"
                              max="2000"
                            />
                          </div>
                        </div>

                        <div>
                          <label
                            htmlFor={`exercise-notes-${exercise.id}`}
                            className="block text-sm font-medium text-gray-700 mb-1"
                          >
                            Notes (optional)
                          </label>
                          <textarea
                            id={`exercise-notes-${exercise.id}`}
                            value={exercise.notes || ''}
                            onChange={(e) =>
                              handleExerciseChange(
                                exercise.id,
                                'notes',
                                e.target.value
                              )
                            }
                            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            rows={2}
                            placeholder="Add any notes about this exercise"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex justify-end">
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSaving}
                >
                  {isSaving ? 'Creating...' : 'Create Workout'}
                </Button>
              </div>
            </div>
          </form>
        </Card>
      ) : (
        <Card>
          <div className="text-center py-8">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No clients found
            </h3>
            <p className="text-gray-500 mb-6">
              You need to add clients before you can create workouts
            </p>
            <Link href="/clients/new">
              <Button variant="primary">Add Your First Client</Button>
            </Link>
          </div>
        </Card>
      )}
    </div>
  );
}

// Main page component that wraps the content in a Suspense boundary
export default function NewWorkoutPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    }>
      <WorkoutPageContent />
    </Suspense>
  );
} 