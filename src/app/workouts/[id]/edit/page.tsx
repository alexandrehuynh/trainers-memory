'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/authContext';
import Navigation from '@/components/Navigation';
import Card from '@/components/ui/Card';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { Client, Exercise, Workout, clientsApi, workoutsApi } from '@/lib/apiClient';

interface WorkoutFormData {
  client_id: string;
  date: string;
  type: string;
  duration: number;
  notes: string;
  exercises: Exercise[];
}

export default function EditWorkoutPage() {
  const { user, isLoading: authLoading } = useAuth();
  const params = useParams();
  const router = useRouter();
  const workoutId = params.id as string;
  
  const [clients, setClients] = useState<Client[]>([]);
  const [formData, setFormData] = useState<WorkoutFormData>({
    client_id: '',
    date: new Date().toISOString().split('T')[0],
    type: '',
    duration: 60,
    notes: '',
    exercises: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      Promise.all([fetchWorkout(), fetchClients()]);
    }
  }, [user, workoutId]);

  const fetchWorkout = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await workoutsApi.getById(workoutId);
      
      setFormData({
        client_id: data.client_id,
        date: new Date(data.date).toISOString().split('T')[0],
        type: data.type,
        duration: data.duration,
        notes: data.notes || '',
        exercises: data.exercises.map(exercise => ({
          ...exercise,
          id: exercise.id || crypto.randomUUID(),
        })),
      });
    } catch (err) {
      console.error('Error fetching workout:', err);
      setError('Failed to load workout details. Please try again later.');
      
      // For demo purposes, set sample data
      setFormData({
        client_id: '1',
        date: new Date().toISOString().split('T')[0],
        type: 'Strength Training',
        duration: 60,
        notes: 'Focused on upper body. Increased weight on bench press.',
        exercises: [
          {
            id: crypto.randomUUID(),
            name: 'Bench Press',
            sets: 3,
            reps: 10,
            weight: 135,
            notes: 'Felt strong, could increase weight next time',
          },
          {
            id: crypto.randomUUID(),
            name: 'Lat Pulldown',
            sets: 3,
            reps: 12,
            weight: 120,
            notes: '',
          },
        ],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const data = await clientsApi.getAll();
      setClients(data);
    } catch (err) {
      console.error('Error fetching clients:', err);
      
      // For demo purposes, add some sample clients
      setClients([
        { id: '1', name: 'John Doe', email: 'john@example.com', created_at: new Date().toISOString() },
        { id: '2', name: 'Jane Smith', email: 'jane@example.com', created_at: new Date().toISOString() },
      ]);
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      await workoutsApi.update(workoutId, formData);

      // Redirect to workout details on success
      router.push(`/workouts/${workoutId}`);
    } catch (err) {
      console.error('Error updating workout:', err);
      setError('Failed to update workout. Please try again.');
      
      // For demo purposes, simulate success and redirect
      setTimeout(() => {
        router.push(`/workouts/${workoutId}`);
      }, 1000);
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
      <div className="min-h-screen flex flex-col">
        <Navigation />
        <main className="flex-grow flex items-center justify-center">
          <Card>
            <div className="text-center p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Please sign in to edit workouts
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
            <Link href={`/workouts/${workoutId}`} className="text-blue-600 hover:text-blue-800 mr-2">
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
            <h1 className="text-2xl font-bold text-gray-900">Edit Workout</h1>
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
                    <Input
                      label="Workout Type"
                      id="type"
                      name="type"
                      value={formData.type}
                      onChange={handleChange}
                      required
                      placeholder="e.g., Strength, Cardio, HIIT"
                    />

                    <Input
                      label="Duration (minutes)"
                      type="number"
                      id="duration"
                      name="duration"
                      value={formData.duration.toString()}
                      onChange={(e) => {
                        const value = parseInt(e.target.value) || 0;
                        setFormData((prev) => ({
                          ...prev,
                          duration: value
                        }));
                      }}
                      required
                      min="1"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="notes"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Workout Notes
                    </label>
                    <textarea
                      id="notes"
                      name="notes"
                      rows={3}
                      value={formData.notes}
                      onChange={handleChange}
                      placeholder="Overall notes about the workout"
                      className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    ></textarea>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-medium text-gray-900">Exercises</h3>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={addExercise}
                      >
                        Add Exercise
                      </Button>
                    </div>

                    {formData.exercises.map((exercise, index) => (
                      <div
                        key={exercise.id}
                        className="border border-gray-200 rounded-md p-4 mb-4"
                      >
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="font-medium text-gray-700">
                            Exercise {index + 1}
                          </h4>
                          {formData.exercises.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeExercise(exercise.id)}
                              className="text-red-600 hover:text-red-800"
                            >
                              Remove
                            </button>
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                          <Input
                            label="Exercise Name"
                            id={`exercise-${exercise.id}-name`}
                            value={exercise.name}
                            onChange={(e) =>
                              handleExerciseChange(exercise.id, 'name', e.target.value)
                            }
                            required
                            placeholder="e.g., Bench Press, Squat"
                          />

                          <div className="grid grid-cols-3 gap-2">
                            <Input
                              label="Sets"
                              type="number"
                              id={`exercise-${exercise.id}-sets`}
                              value={exercise.sets.toString()}
                              onChange={(e) =>
                                handleExerciseChange(
                                  exercise.id,
                                  'sets',
                                  parseInt(e.target.value) || 0
                                )
                              }
                              required
                              min="1"
                            />
                            <Input
                              label="Reps"
                              type="number"
                              id={`exercise-${exercise.id}-reps`}
                              value={exercise.reps.toString()}
                              onChange={(e) =>
                                handleExerciseChange(
                                  exercise.id,
                                  'reps',
                                  parseInt(e.target.value) || 0
                                )
                              }
                              required
                              min="0"
                            />
                            <Input
                              label="Weight (lbs)"
                              type="number"
                              id={`exercise-${exercise.id}-weight`}
                              value={exercise.weight.toString()}
                              onChange={(e) =>
                                handleExerciseChange(
                                  exercise.id,
                                  'weight',
                                  parseInt(e.target.value) || 0
                                )
                              }
                              min="0"
                            />
                          </div>
                        </div>

                        <div>
                          <label
                            htmlFor={`exercise-${exercise.id}-notes`}
                            className="block text-sm font-medium text-gray-700 mb-1"
                          >
                            Notes
                          </label>
                          <textarea
                            id={`exercise-${exercise.id}-notes`}
                            value={exercise.notes}
                            onChange={(e) =>
                              handleExerciseChange(exercise.id, 'notes', e.target.value)
                            }
                            rows={2}
                            placeholder="Notes about this exercise"
                            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          ></textarea>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-end space-x-3">
                    <Link href={`/workouts/${workoutId}`}>
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
      </main>
    </div>
  );
} 