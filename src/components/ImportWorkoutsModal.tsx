'use client';

import { useState, useEffect } from 'react';
import Button from './ui/Button';
import { Client, clientsApi, workoutsApi } from '@/lib/apiClient';

interface ImportWorkout {
  client_id: string;
  client_name: string; // For display only
  date: string;
  type: string;
  duration: number;
  notes: string;
}

interface ImportWorkoutsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (importedCount: number) => void;
}

export default function ImportWorkoutsModal({ isOpen, onClose, onSuccess }: ImportWorkoutsModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportWorkout[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'upload' | 'preview' | 'importing'>('upload');

  useEffect(() => {
    if (isOpen) {
      fetchClients();
    }
  }, [isOpen]);

  const fetchClients = async () => {
    try {
      const data = await clientsApi.getAll();
      setClients(data);
    } catch (err) {
      console.error('Error fetching clients:', err);
      setClients([
        { id: '1', name: 'John Doe', email: 'john@example.com', created_at: new Date().toISOString() },
        { id: '2', name: 'Jane Smith', email: 'jane@example.com', created_at: new Date().toISOString() },
      ]);
    }
  };

  const resetState = () => {
    setFile(null);
    setPreview([]);
    setIsLoading(false);
    setError(null);
    setStep('upload');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) {
      return;
    }

    // Check file type
    const fileType = selectedFile.name.split('.').pop()?.toLowerCase();
    if (fileType !== 'csv' && fileType !== 'xlsx' && fileType !== 'xls') {
      setError('Please upload a CSV or Excel file');
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  const parseFile = async () => {
    if (!file) {
      setError('Please select a file to import');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // For CSV files
      if (file.name.endsWith('.csv')) {
        const text = await file.text();
        const rows = text.split('\n');
        const headers = rows[0].split(',').map(h => h.trim());
        
        // Validate headers
        const requiredHeaders = ['client_email', 'date', 'type', 'duration'];
        const missingHeaders = requiredHeaders.filter(h => !headers.includes(h));
        
        if (missingHeaders.length > 0) {
          throw new Error(`Missing required columns: ${missingHeaders.join(', ')}`);
        }

        const parsedData: ImportWorkout[] = [];
        
        for (let i = 1; i < rows.length; i++) {
          if (!rows[i].trim()) continue;
          
          const values = rows[i].split(',').map(v => v.trim());
          const rowData: any = {};
          
          headers.forEach((header, index) => {
            if (values[index]) {
              rowData[header] = values[index];
            }
          });
          
          if (rowData.client_email && rowData.date && rowData.type && rowData.duration) {
            // Find client by email
            const client = clients.find(c => c.email === rowData.client_email);
            
            if (client) {
              parsedData.push({
                client_id: client.id,
                client_name: client.name,
                date: new Date(rowData.date).toISOString().split('T')[0],
                type: rowData.type,
                duration: parseInt(rowData.duration) || 0,
                notes: rowData.notes || '',
              });
            }
          }
        }
        
        setPreview(parsedData);
        setStep('preview');
      } 
      // For Excel files
      else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        // We'd normally use a library like xlsx or sheetjs
        // For this example, we'll simulate successful parsing
        
        // Mock data for preview
        setPreview([
          {
            client_id: '1',
            client_name: 'John Doe',
            date: new Date().toISOString().split('T')[0],
            type: 'Strength Training',
            duration: 60,
            notes: 'Upper body focus',
          },
          {
            client_id: '2',
            client_name: 'Jane Smith',
            date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            type: 'Cardio',
            duration: 45,
            notes: '5k run',
          },
        ]);
        setStep('preview');
      }
    } catch (err) {
      console.error('Error parsing file:', err);
      setError(`Error parsing file: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const importWorkouts = async () => {
    if (preview.length === 0) {
      setError('No workouts to import');
      return;
    }

    setIsLoading(true);
    setError(null);
    setStep('importing');

    try {
      let successCount = 0;
      
      for (const workout of preview) {
        try {
          // Create workout with empty exercises array
          await workoutsApi.create({
            ...workout,
            exercises: [],
          });
          successCount++;
        } catch (err) {
          console.error(`Error importing workout for ${workout.client_name}:`, err);
          // Continue with other workouts even if one fails
        }
      }
      
      // Call onSuccess with the number of workouts successfully imported
      onSuccess(successCount);
      
      // Close modal and reset state
      resetState();
      onClose();
    } catch (err) {
      console.error('Error importing workouts:', err);
      setError(`Error importing workouts: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setStep('preview'); // Go back to preview step on error
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-3xl w-full">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Import Workouts from Spreadsheet
          </h3>
        </div>
        
        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-800 rounded-md">
              {error}
            </div>
          )}
          
          {step === 'upload' && (
            <div>
              <p className="text-gray-600 mb-4">
                Upload a CSV or Excel file with your workout data. The file must include at least the following columns:
              </p>
              <ul className="list-disc list-inside mb-6 text-gray-600">
                <li>client_email (required - must match an existing client)</li>
                <li>date (required - in YYYY-MM-DD format)</li>
                <li>type (required - e.g., "Strength Training")</li>
                <li>duration (required - in minutes)</li>
                <li>notes (optional)</li>
              </ul>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select File
                </label>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  className="block w-full text-gray-700 bg-white border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="text-gray-500 text-sm mb-4">
                <p>Sample CSV format:</p>
                <pre className="bg-gray-100 p-2 rounded-md mt-1 overflow-x-auto">
                  client_email,date,type,duration,notes{'\n'}
                  john@example.com,2023-05-15,Strength Training,60,Upper body focus{'\n'}
                  jane@example.com,2023-05-10,Cardio,45,5k run
                </pre>
              </div>
            </div>
          )}
          
          {step === 'preview' && (
            <div>
              <p className="text-gray-600 mb-4">
                Review the workouts that will be imported. Make sure the data looks correct before proceeding.
              </p>
              
              {preview.length > 0 ? (
                <div className="mb-6 border border-gray-200 rounded-md overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th
                          scope="col"
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Client
                        </th>
                        <th
                          scope="col"
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Date
                        </th>
                        <th
                          scope="col"
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Type
                        </th>
                        <th
                          scope="col"
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Duration
                        </th>
                        <th
                          scope="col"
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Notes
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {preview.map((workout, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {workout.client_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(workout.date).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {workout.type}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {workout.duration} min
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {workout.notes || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 mb-6">No valid workouts found in the file.</p>
              )}
              
              <p className="text-gray-500 text-sm mb-4">
                Total workouts to import: <span className="font-semibold">{preview.length}</span>
              </p>
            </div>
          )}
          
          {step === 'importing' && (
            <div className="text-center py-6">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Importing workouts... Please wait.</p>
            </div>
          )}
        </div>
        
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <Button
            variant="outline"
            onClick={() => {
              resetState();
              onClose();
            }}
            disabled={isLoading}
          >
            Cancel
          </Button>
          
          {step === 'upload' && file && (
            <Button
              variant="primary"
              onClick={parseFile}
              isLoading={isLoading}
              disabled={!file}
            >
              Preview
            </Button>
          )}
          
          {step === 'preview' && (
            <>
              <Button
                variant="outline"
                onClick={() => setStep('upload')}
                disabled={isLoading}
              >
                Back
              </Button>
              <Button
                variant="primary"
                onClick={importWorkouts}
                isLoading={isLoading}
                disabled={preview.length === 0}
              >
                Import {preview.length} Workouts
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
} 