'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/authContext';
import { useTheme } from '@/lib/themeContext';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import ImportWorkoutsModal from '@/components/ImportWorkoutsModal';
import ExportWorkoutsModal from '@/components/ExportWorkoutsModal';
import ScanWorkoutModal from '@/components/ScanWorkoutModal';
import { Workout, workoutsApi } from '@/lib/apiClient';

export default function WorkoutsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { theme } = useTheme();
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showScanModal, setShowScanModal] = useState(false);
  
  // Development mode flag - set to true to use sample data and avoid API calls
  const USE_SAMPLE_DATA = false; // Toggle this when backend is ready

  const fetchWorkouts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    // If we're in development mode with sample data, skip the API call
    if (USE_SAMPLE_DATA) {
      console.log('Development mode: Using sample workout data');
      setWorkouts([
        {
          id: '1',
          client_name: 'John Doe',
          client_id: '1',
          date: new Date().toISOString(),
          type: 'Strength Training',
          duration: 60,
          notes: 'Focused on upper body',
          exercises: [],
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          client_name: 'Jane Smith',
          client_id: '2',
          date: new Date(Date.now() - 86400000).toISOString(), // Yesterday
          type: 'Cardio',
          duration: 45,
          notes: 'HIIT session',
          exercises: [],
          created_at: new Date(Date.now() - 86400000).toISOString(),
        },
        {
          id: '3',
          client_name: 'Alex Johnson',
          client_id: '3',
          date: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
          type: 'Flexibility',
          duration: 30,
          notes: 'Yoga and stretching',
          exercises: [],
          created_at: new Date(Date.now() - 172800000).toISOString(),
        },
      ]);
      setIsLoading(false);
      return;
    }
    
    try {
      console.log('Attempting to fetch workouts from API...');
      // Using the updated workouts API which already handles the response format
      const workouts = await workoutsApi.getAll();
      setWorkouts(workouts);
      console.log('Successfully fetched workouts from API:', workouts);
    } catch (err) {
      console.error('Error fetching workouts:', err);
      setError('Failed to load workouts from API. Using sample data instead.');
      console.log('Using sample workout data for development');
      
      // For demo purposes, add some sample workouts
      setWorkouts([
        {
          id: '1',
          client_name: 'John Doe',
          client_id: '1',
          date: new Date().toISOString(),
          type: 'Strength Training',
          duration: 60,
          notes: 'Focused on upper body',
          exercises: [],
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          client_name: 'Jane Smith',
          client_id: '2',
          date: new Date(Date.now() - 86400000).toISOString(), // Yesterday
          type: 'Cardio',
          duration: 45,
          notes: 'HIIT session',
          exercises: [],
          created_at: new Date(Date.now() - 86400000).toISOString(),
        },
        {
          id: '3',
          client_name: 'Alex Johnson',
          client_id: '3',
          date: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
          type: 'Flexibility',
          duration: 30,
          notes: 'Yoga and stretching',
          exercises: [],
          created_at: new Date(Date.now() - 172800000).toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Only fetch workouts if user is authenticated
    if (user) {
      fetchWorkouts();
    }
  }, [user, fetchWorkouts]);

  const handleImportSuccess = (count: number) => {
    setShowImportModal(false);
    // Show success message
    alert(`Successfully imported ${count} workouts`);
    // Refresh the workout list
    fetchWorkouts();
  };

  const handleScanSuccess = (count: number) => {
    setShowScanModal(false);
    // Show success message
    alert(`Successfully imported ${count} workouts from scanned document`);
    // Refresh the workout list
    fetchWorkouts();
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
            Please sign in to view workouts
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
        <h1 className={`text-2xl font-bold ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'}`}>Workouts</h1>
        <div className="flex space-x-2">
          <Button 
            variant="outline"
            onClick={() => setShowScanModal(true)}
          >
            Scan Document
          </Button>
          <Button 
            variant="outline"
            onClick={() => setShowExportModal(true)}
          >
            Export Workouts
          </Button>
          <Button 
            variant="outline"
            onClick={() => setShowImportModal(true)}
          >
            Import from Spreadsheet
          </Button>
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
            <h3 className={`text-lg font-medium ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'} mb-2`}>
              No workouts yet
            </h3>
            <p className={`${theme === 'light' ? 'text-gray-500' : 'text-gray-400'} mb-6`}>
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
                      <h3 className={`text-lg font-medium ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'}`}>
                        {workout.type || 'Workout'}
                      </h3>
                      <p className={`text-sm ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
                        {new Date(workout.date || workout.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${theme === 'light' ? 'bg-blue-100 text-blue-800' : 'bg-blue-900 text-blue-200'}`}>
                      {workout.duration} min
                    </span>
                  </div>
                  
                  <div className="mb-4">
                    <p className={`text-sm font-medium ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'}`}>
                      Client: {workout.client_name || 'Unknown'}
                    </p>
                  </div>
                  
                  {workout.notes && (
                    <p className={`text-sm ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'} line-clamp-3 mb-4`}>
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

      {showImportModal && (
        <ImportWorkoutsModal
          isOpen={showImportModal}
          onClose={() => setShowImportModal(false)}
          onSuccess={handleImportSuccess}
        />
      )}

      {showExportModal && (
        <ExportWorkoutsModal
          isOpen={showExportModal}
          onClose={() => setShowExportModal(false)}
        />
      )}

      {showScanModal && (
        <ScanWorkoutModal
          isOpen={showScanModal}
          onClose={() => setShowScanModal(false)}
          onSuccess={handleScanSuccess}
        />
      )}
    </div>
  );
} 