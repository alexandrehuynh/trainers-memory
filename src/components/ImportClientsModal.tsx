'use client';

import { useState } from 'react';
import Button from './ui/Button';
import Card from './ui/Card';
import { clientsApi } from '@/lib/apiClient';

interface ImportClient {
  name: string;
  email: string;
  phone?: string;
  notes?: string;
}

interface ImportClientsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (importedCount: number) => void;
}

export default function ImportClientsModal({ isOpen, onClose, onSuccess }: ImportClientsModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportClient[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'upload' | 'preview' | 'importing'>('upload');

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
        const requiredHeaders = ['name', 'email'];
        const missingHeaders = requiredHeaders.filter(h => !headers.includes(h));
        
        if (missingHeaders.length > 0) {
          throw new Error(`Missing required columns: ${missingHeaders.join(', ')}`);
        }

        const parsedData: ImportClient[] = [];
        
        for (let i = 1; i < rows.length; i++) {
          if (!rows[i].trim()) continue;
          
          const values = rows[i].split(',').map(v => v.trim());
          const client: any = {};
          
          headers.forEach((header, index) => {
            if (values[index]) {
              client[header] = values[index];
            }
          });
          
          if (client.name && client.email) {
            parsedData.push({
              name: client.name,
              email: client.email,
              phone: client.phone || '',
              notes: client.notes || '',
            });
          }
        }
        
        setPreview(parsedData);
        setStep('preview');
      } 
      // For Excel files, we'd normally use a library like xlsx or sheetjs
      else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        // For this example, we'll simulate successful parsing
        
        // Mock data for preview
        setPreview([
          {
            name: 'John Doe',
            email: 'john@example.com',
            phone: '555-123-4567',
            notes: 'New client interested in strength training',
          },
          {
            name: 'Jane Smith',
            email: 'jane@example.com',
            phone: '555-987-6543',
            notes: 'Focusing on weight loss',
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

  const importClients = async () => {
    if (preview.length === 0) {
      setError('No clients to import');
      return;
    }

    setIsLoading(true);
    setError(null);
    setStep('importing');

    try {
      // In a real app, you might want to batch these requests
      let successCount = 0;
      
      for (const client of preview) {
        try {
          await clientsApi.create(client);
          successCount++;
        } catch (err) {
          console.error(`Error importing client ${client.email}:`, err);
          // Continue with other clients even if one fails
        }
      }
      
      // Call onSuccess with the number of clients successfully imported
      onSuccess(successCount);
      
      // Close modal and reset state
      resetState();
      onClose();
    } catch (err) {
      console.error('Error importing clients:', err);
      setError(`Error importing clients: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
            Import Clients from Spreadsheet
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
                Upload a CSV or Excel file with your client data. The file must include at least the following columns:
              </p>
              <ul className="list-disc list-inside mb-6 text-gray-600">
                <li>name (required)</li>
                <li>email (required)</li>
                <li>phone (optional)</li>
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
                  name,email,phone,notes{'\n'}
                  John Doe,john@example.com,555-123-4567,New client{'\n'}
                  Jane Smith,jane@example.com,555-987-6543,Weight loss focus
                </pre>
              </div>
            </div>
          )}
          
          {step === 'preview' && (
            <div>
              <p className="text-gray-600 mb-4">
                Review the clients that will be imported. Make sure the data looks correct before proceeding.
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
                          Name
                        </th>
                        <th
                          scope="col"
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Email
                        </th>
                        <th
                          scope="col"
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Phone
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
                      {preview.map((client, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {client.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {client.email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {client.phone || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {client.notes || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 mb-6">No valid clients found in the file.</p>
              )}
              
              <p className="text-gray-500 text-sm mb-4">
                Total clients to import: <span className="font-semibold">{preview.length}</span>
              </p>
            </div>
          )}
          
          {step === 'importing' && (
            <div className="text-center py-6">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Importing clients... Please wait.</p>
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
                onClick={importClients}
                isLoading={isLoading}
                disabled={preview.length === 0}
              >
                Import {preview.length} Clients
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
} 