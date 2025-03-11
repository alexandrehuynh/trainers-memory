'use client';

import { useState, useEffect, useMemo } from 'react';
import { useTheme } from '@/lib/themeContext';
import Card from '@/components/ui/Card';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, ReferenceLine
} from 'recharts';
import { Workout, Exercise, workoutsApi } from '@/lib/apiClient';

interface ExerciseProgressionProps {
  clientId: string;
  exerciseName: string; 
  limit?: number;
}

interface ProgressPoint {
  date: string;
  weight: number;
  reps: number;
  sets: number;
  volume: number; // weight * reps * sets
  workout: string;
}

export default function ExerciseProgression({ clientId, exerciseName, limit = 10 }: ExerciseProgressionProps) {
  const { theme } = useTheme();
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<'weight' | 'reps' | 'sets' | 'volume'>('weight');

  // Text colors based on theme
  const textColor = theme === 'light' ? '#1F2937' : '#F3F4F6';
  const labelColor = theme === 'light' ? '#6B7280' : '#9CA3AF';
  const gridColor = theme === 'light' ? '#E5E7EB' : '#374151';

  useEffect(() => {
    if (clientId && exerciseName) {
      fetchWorkouts();
    }
  }, [clientId, exerciseName]);

  const fetchWorkouts = async () => {
    if (!clientId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch workouts for this client
      const workoutData = await workoutsApi.getByClientId(clientId);
      
      // Filter workouts to only include those with the specified exercise
      const relevantWorkouts = workoutData.filter((workout: Workout) => 
        workout.exercises.some((exercise: Exercise) => 
          exercise.name.toLowerCase() === exerciseName.toLowerCase()
        )
      ).slice(0, limit);
      
      setWorkouts(relevantWorkouts);
    } catch (err) {
      console.error('Error fetching exercise progression:', err);
      setError('Failed to load exercise progression data.');
      setWorkouts([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Process workout data for progression chart
  const progressionData = useMemo(() => {
    if (!workouts.length) return [];
    
    const data: ProgressPoint[] = [];
    
    // Sort workouts by date
    const sortedWorkouts = [...workouts].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
    
    // Get exercise data from each workout
    sortedWorkouts.forEach(workout => {
      const matchingExercise = workout.exercises.find(
        ex => ex.name.toLowerCase() === exerciseName.toLowerCase()
      );
      
      if (matchingExercise) {
        const volume = 
          (matchingExercise.weight || 0) * 
          (matchingExercise.reps || 0) * 
          (matchingExercise.sets || 0);
          
        data.push({
          date: new Date(workout.date).toLocaleDateString(),
          weight: matchingExercise.weight || 0,
          reps: matchingExercise.reps || 0,
          sets: matchingExercise.sets || 0,
          volume,
          workout: workout.type
        });
      }
    });
    
    return data;
  }, [workouts, exerciseName]);

  // Calculate improvement statistics
  const stats = useMemo(() => {
    if (progressionData.length < 2) {
      return {
        change: 0,
        percentChange: 0,
        trend: 'neutral',
        average: 0
      };
    }
    
    const first = progressionData[0][selectedMetric];
    const last = progressionData[progressionData.length - 1][selectedMetric];
    const change = last - first;
    const percentChange = (change / first) * 100;
    
    // Calculate average
    const sum = progressionData.reduce((acc, curr) => acc + curr[selectedMetric], 0);
    const average = sum / progressionData.length;
    
    return {
      change,
      percentChange,
      trend: change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral',
      average
    };
  }, [progressionData, selectedMetric]);

  // Get display name for the selected metric
  const getMetricDisplayName = () => {
    switch (selectedMetric) {
      case 'weight': return 'Weight (lbs)';
      case 'reps': return 'Reps';
      case 'sets': return 'Sets';
      case 'volume': return 'Volume (weight × reps × sets)';
      default: return 'Value';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="p-4 text-red-500">
          <p>{error}</p>
        </div>
      </Card>
    );
  }

  if (!progressionData.length) {
    return (
      <Card>
        <div className="p-6 text-center">
          <p className={theme === 'light' ? 'text-gray-600' : 'text-gray-400'}>
            No progression data available for {exerciseName}.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-6">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6">
          <h2 className={`text-xl font-semibold ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'} mb-2 md:mb-0`}>
            {exerciseName} Progression
          </h2>
          
          <div className="flex items-center">
            <label htmlFor="metric-select" className={`text-sm font-medium ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'} mr-2`}>
              Metric:
            </label>
            <select
              id="metric-select"
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value as 'weight' | 'reps' | 'sets' | 'volume')}
              className={`rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                theme === 'light' ? 'bg-white text-gray-900' : 'bg-gray-800 text-white border-gray-700'
              }`}
            >
              <option value="weight">Weight</option>
              <option value="reps">Reps</option>
              <option value="sets">Sets</option>
              <option value="volume">Volume</option>
            </select>
          </div>
        </div>
        
        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className={`p-4 rounded-md ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-800'}`}>
            <p className={`text-sm font-medium ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
              Change
            </p>
            <div className="flex items-baseline">
              <p 
                className={`text-2xl font-bold ${
                  stats.trend === 'positive' 
                    ? 'text-green-600' 
                    : stats.trend === 'negative' 
                      ? 'text-red-600' 
                      : theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                }`}
              >
                {stats.change > 0 ? '+' : ''}{stats.change.toFixed(1)}
              </p>
              <p className={`ml-2 text-sm ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
                {getMetricDisplayName().split(' ')[0]}
              </p>
            </div>
          </div>
          
          <div className={`p-4 rounded-md ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-800'}`}>
            <p className={`text-sm font-medium ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
              Percent Change
            </p>
            <div className="flex items-baseline">
              <p 
                className={`text-2xl font-bold ${
                  stats.trend === 'positive' 
                    ? 'text-green-600' 
                    : stats.trend === 'negative' 
                      ? 'text-red-600' 
                      : theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                }`}
              >
                {stats.percentChange > 0 ? '+' : ''}{stats.percentChange.toFixed(1)}%
              </p>
            </div>
          </div>
          
          <div className={`p-4 rounded-md ${theme === 'light' ? 'bg-gray-50' : 'bg-gray-800'}`}>
            <p className={`text-sm font-medium ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
              Average
            </p>
            <div className="flex items-baseline">
              <p className={`text-2xl font-bold ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'}`}>
                {stats.average.toFixed(1)}
              </p>
              <p className={`ml-2 text-sm ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
                {getMetricDisplayName().split(' ')[0]}
              </p>
            </div>
          </div>
        </div>
        
        {/* Progression chart */}
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={progressionData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis 
                dataKey="date" 
                stroke={labelColor}
                style={{ fontSize: '0.8rem', fontFamily: 'sans-serif', fill: labelColor }}
              />
              <YAxis 
                stroke={labelColor} 
                style={{ fontSize: '0.8rem', fontFamily: 'sans-serif', fill: labelColor }}
              />
              <Tooltip
                formatter={(value) => [`${value}`, getMetricDisplayName()]}
                labelFormatter={(label) => `Date: ${label}`}
                contentStyle={{
                  backgroundColor: theme === 'light' ? '#fff' : '#1F2937',
                  border: `1px solid ${theme === 'light' ? '#E5E7EB' : '#374151'}`,
                  color: textColor
                }}
              />
              <Legend />
              <Bar 
                dataKey={selectedMetric} 
                name={getMetricDisplayName()} 
                fill="#8884d8" 
              />
              <ReferenceLine 
                y={stats.average} 
                stroke="#FF8042" 
                strokeDasharray="3 3" 
                label={{ value: 'Average', position: 'insideBottomRight', fill: '#FF8042' }} 
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {progressionData.length > 0 && (
          <div className="mt-4">
            <h3 className={`text-md font-medium mb-2 ${theme === 'light' ? 'text-gray-800' : 'text-gray-200'}`}>
              Performance Insights
            </h3>
            <div className={`p-4 rounded-md ${
              stats.trend === 'positive' 
                ? 'bg-green-50 border border-green-100' 
                : stats.trend === 'negative' 
                  ? 'bg-red-50 border border-red-100'
                  : 'bg-blue-50 border border-blue-100'
            }`}>
              <p className={`text-sm ${
                stats.trend === 'positive' 
                  ? 'text-green-800' 
                  : stats.trend === 'negative' 
                    ? 'text-red-800'
                    : 'text-blue-800'
              }`}>
                {stats.trend === 'positive' 
                  ? `Great progress! ${exerciseName} ${selectedMetric} has increased by ${stats.percentChange.toFixed(1)}% over ${progressionData.length} workouts.`
                  : stats.trend === 'negative'
                    ? `${exerciseName} ${selectedMetric} has decreased by ${Math.abs(stats.percentChange).toFixed(1)}%. Consider adjusting the workout intensity or technique.`
                    : `${exerciseName} ${selectedMetric} has remained consistent across ${progressionData.length} workouts.`
                }
              </p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
} 