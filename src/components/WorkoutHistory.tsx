'use client';

import { useState, useEffect, useMemo } from 'react';
import { useTheme } from '@/lib/themeContext';
import Card from '@/components/ui/Card';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import { Workout, Exercise, workoutsApi } from '@/lib/apiClient';

interface WorkoutHistoryProps {
  clientId?: string;
  limit?: number;
  showFilters?: boolean;
}

export default function WorkoutHistory({ clientId, limit = 10, showFilters = true }: WorkoutHistoryProps) {
  const { theme } = useTheme();
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedExercise, setSelectedExercise] = useState<string>('all');
  const [selectedMetric, setSelectedMetric] = useState<'weight' | 'reps' | 'sets'>('weight');
  const [chartType, setChartType] = useState<'line' | 'bar' | 'pie'>('line');

  // Text colors based on theme
  const textColor = theme === 'light' ? '#1F2937' : '#F3F4F6';
  const labelColor = theme === 'light' ? '#6B7280' : '#9CA3AF';
  const gridColor = theme === 'light' ? '#E5E7EB' : '#374151';

  useEffect(() => {
    fetchWorkouts();
  }, [clientId]);

  const fetchWorkouts = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      let workoutData: Workout[];
      
      if (clientId) {
        // If clientId is provided, fetch workouts for that client
        workoutData = await workoutsApi.getByClientId(clientId);
      } else {
        // Otherwise, fetch all workouts
        workoutData = await workoutsApi.getAll();
      }
      
      // Filter the results based on limit if needed
      if (limit && workoutData.length > limit) {
        workoutData = workoutData.slice(0, limit);
      }
      
      // Sort workouts by date in ascending order for proper chronological display
      workoutData.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      setWorkouts(workoutData);
    } catch (err) {
      console.error('Error fetching workout history:', err);
      setError('Failed to load workout history. Please try again later.');
      setWorkouts([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Extract unique exercise names from all workouts
  const exerciseOptions = useMemo(() => {
    const exerciseSet = new Set<string>();
    
    workouts.forEach(workout => {
      workout.exercises.forEach(exercise => {
        if (exercise.name && exercise.name.trim() !== '') {
          exerciseSet.add(exercise.name);
        }
      });
    });
    
    return ['all', ...Array.from(exerciseSet)];
  }, [workouts]);

  // Process workout data for charts
  const chartData = useMemo(() => {
    if (!workouts.length) return [];
    
    if (selectedExercise === 'all') {
      // For "all exercises", we'll create workout summary data
      return workouts.map(workout => {
        // Calculate averages across all exercises
        const exerciseCount = workout.exercises.length;
        const totalWeight = workout.exercises.reduce((sum, ex) => sum + (ex.weight || 0), 0);
        const totalReps = workout.exercises.reduce((sum, ex) => sum + (ex.reps || 0), 0);
        const totalSets = workout.exercises.reduce((sum, ex) => sum + (ex.sets || 0), 0);
        
        return {
          date: new Date(workout.date).toLocaleDateString(),
          avgWeight: exerciseCount ? Math.round(totalWeight / exerciseCount) : 0,
          avgReps: exerciseCount ? Math.round(totalReps / exerciseCount) : 0,
          avgSets: exerciseCount ? Math.round(totalSets / exerciseCount) : 0,
          type: workout.type,
          duration: workout.duration,
          name: `Workout on ${new Date(workout.date).toLocaleDateString()}`
        };
      });
    } else {
      // For a specific exercise, track its progress over time
      const exerciseData: { 
        date: string;
        weight: number;
        reps: number;
        sets: number;
        name: string;
      }[] = [];
      
      workouts.forEach(workout => {
        const matchingExercise = workout.exercises.find(ex => ex.name === selectedExercise);
        
        if (matchingExercise) {
          exerciseData.push({
            date: new Date(workout.date).toLocaleDateString(),
            weight: matchingExercise.weight || 0,
            reps: matchingExercise.reps || 0,
            sets: matchingExercise.sets || 0,
            name: selectedExercise
          });
        }
      });
      
      return exerciseData;
    }
  }, [workouts, selectedExercise]);
  
  // Process workout types for pie chart
  const workoutTypeData = useMemo(() => {
    if (!workouts.length) return [];
    
    const typeCount: Record<string, number> = {};
    
    workouts.forEach(workout => {
      const type = workout.type || 'Unknown';
      typeCount[type] = (typeCount[type] || 0) + 1;
    });
    
    return Object.entries(typeCount).map(([name, value]) => ({ name, value }));
  }, [workouts]);

  // Colors for pie chart
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

  // Create metric display name
  const getMetricDisplayName = () => {
    if (selectedExercise === 'all') {
      if (selectedMetric === 'weight') return 'Average Weight (lbs)';
      if (selectedMetric === 'reps') return 'Average Reps';
      if (selectedMetric === 'sets') return 'Average Sets';
    } else {
      if (selectedMetric === 'weight') return 'Weight (lbs)';
      if (selectedMetric === 'reps') return 'Reps';
      if (selectedMetric === 'sets') return 'Sets';
    }
    return 'Value';
  };

  if (isLoading) {
    return (
      <Card>
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="p-6 text-red-500">
          <p>{error}</p>
        </div>
      </Card>
    );
  }

  if (!workouts.length) {
    return (
      <Card>
        <div className="p-6 text-center">
          <p className={theme === 'light' ? 'text-gray-600' : 'text-gray-400'}>
            No workout history available.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-6">
        <h2 className={`text-xl font-semibold mb-6 ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'}`}>
          Workout History
        </h2>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div>
              <label htmlFor="exercise-select" className={`block text-sm font-medium ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'} mb-1`}>
                Exercise
              </label>
              <select
                id="exercise-select"
                value={selectedExercise}
                onChange={(e) => setSelectedExercise(e.target.value)}
                className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                  theme === 'light' ? 'bg-white text-gray-900' : 'bg-gray-800 text-white border-gray-700'
                }`}
              >
                {exerciseOptions.map((exercise) => (
                  <option key={exercise} value={exercise}>
                    {exercise === 'all' ? 'All Exercises' : exercise}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="metric-select" className={`block text-sm font-medium ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'} mb-1`}>
                Metric
              </label>
              <select
                id="metric-select"
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value as 'weight' | 'reps' | 'sets')}
                className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                  theme === 'light' ? 'bg-white text-gray-900' : 'bg-gray-800 text-white border-gray-700'
                }`}
              >
                <option value="weight">Weight</option>
                <option value="reps">Reps</option>
                <option value="sets">Sets</option>
              </select>
            </div>

            <div>
              <label htmlFor="chart-select" className={`block text-sm font-medium ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'} mb-1`}>
                Chart Type
              </label>
              <select
                id="chart-select"
                value={chartType}
                onChange={(e) => setChartType(e.target.value as 'line' | 'bar' | 'pie')}
                className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                  theme === 'light' ? 'bg-white text-gray-900' : 'bg-gray-800 text-white border-gray-700'
                }`}
              >
                <option value="line">Line Chart</option>
                <option value="bar">Bar Chart</option>
                {selectedExercise === 'all' && <option value="pie">Workout Types</option>}
              </select>
            </div>

            <div className="flex items-end">
              <button 
                onClick={fetchWorkouts}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Refresh Data
              </button>
            </div>
          </div>
        )}

        {chartType === 'pie' && selectedExercise === 'all' ? (
          // Pie chart for workout types
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={workoutTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {workoutTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        ) : chartType === 'line' ? (
          // Line chart for progression
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis 
                  dataKey="date" 
                  stroke={labelColor}
                  style={{ 
                    fontSize: '0.8rem',
                    fontFamily: 'sans-serif',
                    fill: labelColor 
                  }}
                />
                <YAxis 
                  stroke={labelColor}
                  style={{ 
                    fontSize: '0.8rem', 
                    fontFamily: 'sans-serif',
                    fill: labelColor 
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: theme === 'light' ? '#fff' : '#1F2937',
                    border: `1px solid ${theme === 'light' ? '#E5E7EB' : '#374151'}`,
                    color: textColor
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey={selectedExercise === 'all' ? `avg${selectedMetric.charAt(0).toUpperCase() + selectedMetric.slice(1)}` : selectedMetric}
                  name={getMetricDisplayName()}
                  stroke="#8884d8"
                  activeDot={{ r: 8 }}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          // Bar chart for progression
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis 
                  dataKey="date" 
                  stroke={labelColor}
                  style={{ 
                    fontSize: '0.8rem',
                    fontFamily: 'sans-serif',
                    fill: labelColor 
                  }}
                />
                <YAxis 
                  stroke={labelColor}
                  style={{ 
                    fontSize: '0.8rem', 
                    fontFamily: 'sans-serif',
                    fill: labelColor 
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: theme === 'light' ? '#fff' : '#1F2937',
                    border: `1px solid ${theme === 'light' ? '#E5E7EB' : '#374151'}`,
                    color: textColor
                  }}
                />
                <Legend />
                <Bar
                  dataKey={selectedExercise === 'all' ? `avg${selectedMetric.charAt(0).toUpperCase() + selectedMetric.slice(1)}` : selectedMetric}
                  name={getMetricDisplayName()}
                  fill="#8884d8"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
        
        <div className="mt-4 text-sm text-gray-500">
          {chartData.length === 0 && selectedExercise !== 'all' && (
            <p className="text-center text-amber-500">
              No data available for {selectedExercise}. Try selecting a different exercise.
            </p>
          )}
        </div>
      </div>
    </Card>
  );
} 