'use client';

import { useState, useEffect } from 'react';
import Button from './ui/Button';
import { Client, clientsApi, workoutsApi } from '@/lib/apiClient';
import * as XLSX from 'xlsx';

interface ImportWorkout {
  client_id: string;
  client_name: string; // For display only
  date: string;
  type: string;
  duration: number;
  notes: string;
  exercises: Array<{
    id: string;
    name: string;
    sets: number;
    reps: number;
    weight: number;
    notes: string;
  }>;
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

  const parseExercises = (rowData: any): Array<{ id: string; name: string; sets: number; reps: number; weight: number; notes: string; }> => {
    const exercises = [];
    let exerciseIndex = 1;
    
    // Look for exercise columns in pattern: exercise1_name, exercise1_sets, etc.
    while (rowData[`exercise${exerciseIndex}_name`]) {
      const exerciseName = rowData[`exercise${exerciseIndex}_name`];
      
      if (exerciseName && exerciseName.trim() !== '') {
        exercises.push({
          id: crypto.randomUUID(),
          name: exerciseName,
          sets: parseInt(rowData[`exercise${exerciseIndex}_sets`]) || 0,
          reps: parseInt(rowData[`exercise${exerciseIndex}_reps`]) || 0,
          weight: parseInt(rowData[`exercise${exerciseIndex}_weight`]) || 0,
          notes: rowData[`exercise${exerciseIndex}_notes`] || '',
        });
      }
      
      exerciseIndex++;
    }
    
    return exercises;
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
                exercises: parseExercises(rowData),
              });
            }
          }
        }
        
        setPreview(parsedData);
        setStep('preview');
      } 
      // For Excel files
      else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        const reader = new FileReader();

        reader.onload = async (e) => {
          try {
            const data = new Uint8Array(e.target?.result as ArrayBuffer);
            const workbook = XLSX.read(data, { type: 'array' });
            
            // Assume data is in the first sheet
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            
            // Convert sheet to JSON
            const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
            
            if (json.length < 2) {
              throw new Error('File seems to be empty or has no data rows');
            }
            
            // First row should be headers
            const headers = json[0] as string[];
            
            // Validate headers
            const requiredHeaders = ['client_email', 'date', 'type', 'duration'];
            const missingHeaders = requiredHeaders.filter(h => !headers.includes(h));
            
            if (missingHeaders.length > 0) {
              throw new Error(`Missing required columns: ${missingHeaders.join(', ')}`);
            }
            
            const parsedData: ImportWorkout[] = [];
            
            // Process each row (starting from row 1, as row 0 is headers)
            for (let i = 1; i < json.length; i++) {
              const row = json[i] as any[];
              
              if (!row || row.length === 0) continue;
              
              const rowData: any = {};
              
              // Map each column to its header
              headers.forEach((header, index) => {
                if (row[index] !== undefined) {
                  rowData[header] = row[index];
                }
              });
              
              // Ensure required data is present
              if (rowData.client_email && rowData.date && rowData.type && rowData.duration) {
                // Find client by email
                const client = clients.find(c => c.email === rowData.client_email);
                
                if (client) {
                  // Parse date - Excel dates might be formatted differently
                  let workoutDate: string;
                  
                  try {
                    // Try to parse Excel serial date if needed
                    if (typeof rowData.date === 'number') {
                      // Convert Excel date serial to JavaScript Date
                      const excelDate = XLSX.SSF.parse_date_code(rowData.date);
                      const jsDate = new Date(
                        excelDate.y, 
                        excelDate.m - 1, 
                        excelDate.d
                      );
                      workoutDate = jsDate.toISOString().split('T')[0];
                    } else {
                      // Regular string date
                      workoutDate = new Date(rowData.date).toISOString().split('T')[0];
                    }
                  } catch (err) {
                    console.error('Error parsing date:', err);
                    workoutDate = new Date().toISOString().split('T')[0]; // Default to today
                  }
                  
                  parsedData.push({
                    client_id: client.id,
                    client_name: client.name,
                    date: workoutDate,
                    type: rowData.type,
                    duration: parseInt(rowData.duration) || 0,
                    notes: rowData.notes || '',
                    exercises: parseExercises(rowData),
                  });
                }
              }
            }
            
            setPreview(parsedData);
            setStep('preview');
            setIsLoading(false);
          } catch (err) {
            console.error('Error parsing Excel file:', err);
            setError(`Error parsing Excel file: ${err instanceof Error ? err.message : 'Unknown error'}`);
            setIsLoading(false);
          }
        };
        
        reader.onerror = () => {
          setError('Error reading file');
          setIsLoading(false);
        };
        
        reader.readAsArrayBuffer(file);
      }
    } catch (err) {
      console.error('Error parsing file:', err);
      setError(`Error parsing file: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
          // Create workout with exercises array from parsing
          await workoutsApi.create(workout);
          successCount++;
        } catch (err) {
          console.error(`Error importing workout:`, err);
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

  const generateExcelTemplate = () => {
    // Create a new workbook
    const workbook = XLSX.utils.book_new();
    
    // Sample data with headers and one example row
    const data = [
      [
        'client_email', 'date', 'type', 'duration', 'notes',
        'exercise1_name', 'exercise1_sets', 'exercise1_reps', 'exercise1_weight', 'exercise1_notes',
        'exercise2_name', 'exercise2_sets', 'exercise2_reps', 'exercise2_weight', 'exercise2_notes'
      ],
      [
        'client@example.com', new Date().toISOString().split('T')[0], 'Strength Training', 60, 'Sample workout notes',
        'Bench Press', 3, 10, 135, 'Good form',
        'Squats', 4, 8, 185, ''
      ]
    ];
    
    // Create a worksheet
    const worksheet = XLSX.utils.aoa_to_sheet(data);
    
    // Add the worksheet to the workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Workouts');
    
    // Generate Excel file buffer
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    
    // Convert to Blob and create download link
    const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = URL.createObjectURL(blob);
    
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = 'workout_import_template.xlsx';
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
              
              <div className="mb-4">
                <button
                  onClick={generateExcelTemplate}
                  className="text-blue-600 hover:text-blue-800 hover:underline text-sm mb-2 flex items-center"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download Excel Template
                </button>
              </div>
              
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
              <p className="text-gray-600 mb-6">
                Review the workouts to be imported below. Click "Import" to add these workouts to your account.
              </p>
              
              {preview.length > 0 ? (
                <div className="border border-gray-200 rounded-md overflow-hidden mb-6">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Client
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Duration
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Exercises
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
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
                            {workout.exercises.length > 0 ? (
                              <div>
                                <span className="font-medium">{workout.exercises.length}</span> exercise{workout.exercises.length !== 1 ? 's' : ''}
                                <div className="text-xs text-gray-400 mt-1">
                                  {workout.exercises.slice(0, 2).map((ex, i) => (
                                    <div key={i}>{ex.name}</div>
                                  ))}
                                  {workout.exercises.length > 2 && (
                                    <div>+{workout.exercises.length - 2} more</div>
                                  )}
                                </div>
                              </div>
                            ) : (
                              <span className="text-gray-400">None</span>
                            )}
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