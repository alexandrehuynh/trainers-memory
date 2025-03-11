'use client';

import { useState, useEffect } from 'react';
import Button from './ui/Button';
import { Client, clientsApi, workoutsApi, Workout } from '@/lib/apiClient';
import * as XLSX from 'xlsx';

interface ExportWorkoutsModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientId?: string; // Optional: if provided, will only export workouts for this client
}

export default function ExportWorkoutsModal({ isOpen, onClose, clientId }: ExportWorkoutsModalProps) {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState<'csv' | 'excel'>('excel');
  const [selectedClientId, setSelectedClientId] = useState<string>(clientId || '');
  const [exportStatus, setExportStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [dateRange, setDateRange] = useState<{
    startDate: string;
    endDate: string;
  }>({
    startDate: new Date(new Date().setMonth(new Date().getMonth() - 3)).toISOString().split('T')[0], // 3 months ago
    endDate: new Date().toISOString().split('T')[0], // Today
  });

  useEffect(() => {
    if (isOpen) {
      fetchClients();
      if (clientId) {
        setSelectedClientId(clientId);
      }
    }
  }, [isOpen, clientId]);

  const fetchClients = async () => {
    try {
      const data = await clientsApi.getAll();
      setClients(data);
    } catch (err) {
      console.error('Error fetching clients:', err);
      setError('Failed to load clients. Please try again.');
    }
  };

  const fetchWorkouts = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      let workoutData: Workout[];
      
      // Fetch workouts based on selected client (or all workouts)
      if (selectedClientId) {
        workoutData = await workoutsApi.getByClientId(selectedClientId);
      } else {
        workoutData = await workoutsApi.getAll();
      }
      
      // Filter by date range if specified
      if (dateRange.startDate || dateRange.endDate) {
        workoutData = workoutData.filter(workout => {
          const workoutDate = new Date(workout.date);
          
          if (dateRange.startDate && new Date(dateRange.startDate) > workoutDate) {
            return false;
          }
          
          if (dateRange.endDate && new Date(dateRange.endDate) < workoutDate) {
            return false;
          }
          
          return true;
        });
      }
      
      // Sort by date (newest first)
      workoutData.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      
      setWorkouts(workoutData);
    } catch (err) {
      console.error('Error fetching workouts:', err);
      setError('Failed to load workouts. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDateRangeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setDateRange(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const generateExerciseColumns = (workout: Workout) => {
    let exerciseData: Record<string, any> = {};
    
    workout.exercises.forEach((exercise, index) => {
      const exerciseNum = index + 1;
      exerciseData[`exercise${exerciseNum}_name`] = exercise.name;
      exerciseData[`exercise${exerciseNum}_sets`] = exercise.sets;
      exerciseData[`exercise${exerciseNum}_reps`] = exercise.reps;
      exerciseData[`exercise${exerciseNum}_weight`] = exercise.weight;
      exerciseData[`exercise${exerciseNum}_notes`] = exercise.notes || '';
    });
    
    return exerciseData;
  };

  const exportWorkouts = async () => {
    if (workouts.length === 0) {
      await fetchWorkouts();
      if (workouts.length === 0) {
        setError('No workouts found to export.');
        return;
      }
    }
    
    setExportStatus('loading');
    
    try {
      // Prepare data for export
      const exportData = workouts.map(workout => {
        const clientName = clients.find(c => c.id === workout.client_id)?.name || 'Unknown Client';
        
        return {
          client_name: clientName,
          client_id: workout.client_id,
          date: new Date(workout.date).toISOString().split('T')[0],
          type: workout.type,
          duration: workout.duration,
          notes: workout.notes || '',
          exercise_count: workout.exercises.length,
          ...generateExerciseColumns(workout)
        };
      });
      
      if (exportFormat === 'excel') {
        exportToExcel(exportData);
      } else {
        exportToCSV(exportData);
      }
      
      setExportStatus('success');
      setTimeout(() => {
        setExportStatus('idle');
      }, 3000);
    } catch (err) {
      console.error('Error exporting workouts:', err);
      setError(`Failed to export workouts: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setExportStatus('error');
    }
  };
  
  const exportToExcel = (data: any[]) => {
    // Create workbook and worksheet
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(data);
    
    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Workouts');
    
    // Generate filename based on client and date range
    const clientName = selectedClientId 
      ? clients.find(c => c.id === selectedClientId)?.name.replace(/\s+/g, '_') || 'filtered'
      : 'all';
      
    const filename = `workouts_${clientName}_${dateRange.startDate}_to_${dateRange.endDate}.xlsx`;
    
    // Write and download file
    XLSX.writeFile(workbook, filename);
  };
  
  const exportToCSV = (data: any[]) => {
    // Convert data to CSV
    const worksheet = XLSX.utils.json_to_sheet(data);
    const csvOutput = XLSX.utils.sheet_to_csv(worksheet);
    
    // Create blob and download link
    const blob = new Blob([csvOutput], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    // Generate filename based on client and date range
    const clientName = selectedClientId 
      ? clients.find(c => c.id === selectedClientId)?.name.replace(/\s+/g, '_') || 'filtered'
      : 'all';
      
    const filename = `workouts_${clientName}_${dateRange.startDate}_to_${dateRange.endDate}.csv`;
    
    // Create download link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    
    // Clean up
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-xl w-full">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Export Workouts
          </h3>
        </div>
        
        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-800 rounded-md">
              {error}
            </div>
          )}
          
          {exportStatus === 'success' && (
            <div className="mb-6 p-4 bg-green-50 text-green-800 rounded-md">
              Workouts exported successfully!
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label htmlFor="client-select" className="block text-sm font-medium text-gray-700 mb-1">
                Client
              </label>
              <select
                id="client-select"
                value={selectedClientId}
                onChange={(e) => setSelectedClientId(e.target.value)}
                disabled={!!clientId}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Clients</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  id="startDate"
                  name="startDate"
                  value={dateRange.startDate}
                  onChange={handleDateRangeChange}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  id="endDate"
                  name="endDate"
                  value={dateRange.endDate}
                  onChange={handleDateRangeChange}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export Format
              </label>
              <div className="flex space-x-4">
                <label className="inline-flex items-center">
                  <input
                    type="radio"
                    className="form-radio h-4 w-4 text-blue-600"
                    checked={exportFormat === 'excel'}
                    onChange={() => setExportFormat('excel')}
                  />
                  <span className="ml-2 text-gray-700">Excel (.xlsx)</span>
                </label>
                <label className="inline-flex items-center">
                  <input
                    type="radio"
                    className="form-radio h-4 w-4 text-blue-600"
                    checked={exportFormat === 'csv'}
                    onChange={() => setExportFormat('csv')}
                  />
                  <span className="ml-2 text-gray-700">CSV</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isLoading || exportStatus === 'loading'}
          >
            Cancel
          </Button>
          
          <Button
            variant="primary"
            onClick={exportWorkouts}
            isLoading={isLoading || exportStatus === 'loading'}
          >
            {exportStatus === 'loading' ? 'Exporting...' : 'Export Workouts'}
          </Button>
        </div>
      </div>
    </div>
  );
} 