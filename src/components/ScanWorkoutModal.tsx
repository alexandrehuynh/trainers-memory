'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import Button from './ui/Button';
import Card from './ui/Card';
import { Client, clientsApi, ocrApi, OCRResult } from '@/lib/apiClient';
import { useTheme } from '@/lib/themeContext';

interface ScanWorkoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (count: number) => void;
  clientId?: string; // Optional: if provided, will only scan for this client
}

export default function ScanWorkoutModal({ isOpen, onClose, onSuccess, clientId }: ScanWorkoutModalProps) {
  const { theme } = useTheme();
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string>(clientId || '');
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [step, setStep] = useState<'upload' | 'processing' | 'review' | 'saving'>('upload');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize component
  useEffect(() => {
    if (isOpen) {
      fetchClients();
      if (clientId) {
        setSelectedClientId(clientId);
      }
    } else {
      // Reset state when modal closes
      resetState();
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

  const resetState = () => {
    setFile(null);
    setPreviewUrl(null);
    setOcrResult(null);
    setError(null);
    setStep('upload');
    setIsLoading(false);

    // Clear the file input value
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) {
      return;
    }

    // Check if it's an image file
    if (!selectedFile.type.startsWith('image/')) {
      setError('Please upload an image file (JPEG, PNG, etc.)');
      return;
    }

    // Create preview URL
    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);
    setFile(selectedFile);
    setError(null);
  };

  const processImage = async () => {
    if (!file) {
      setError('Please select an image to process');
      return;
    }

    if (!selectedClientId) {
      setError('Please select a client');
      return;
    }

    setIsLoading(true);
    setError(null);
    setStep('processing');

    try {
      const result = await ocrApi.processImage(file, selectedClientId);
      setOcrResult(result);
      setStep('review');
    } catch (err) {
      console.error('Error processing image with OCR:', err);
      setError(`OCR processing failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setStep('upload');
    } finally {
      setIsLoading(false);
    }
  };

  const saveWorkouts = async () => {
    if (!ocrResult || !selectedClientId) {
      setError('No OCR results to save');
      return;
    }

    setIsLoading(true);
    setError(null);
    setStep('saving');

    try {
      const result = await ocrApi.saveOCRResults(
        selectedClientId,
        ocrResult.workout_records
      );

      if (result.success) {
        onSuccess(result.count);
        resetState();
        onClose();
      } else {
        throw new Error('Failed to save workouts');
      }
    } catch (err) {
      console.error('Error saving OCR results:', err);
      setError(`Failed to save workouts: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setStep('review');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  // Helper function to format date from OCR
  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch (e) {
      return dateStr;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Scan Workout Document
          </h3>
        </div>
        
        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-800 rounded-md">
              {error}
            </div>
          )}
          
          {step === 'upload' && (
            <div className="space-y-6">
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
                  <option value="">Select a client</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Workout Document
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-md p-6 flex flex-col items-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                    aria-hidden="true"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="mt-4 flex text-sm text-gray-600">
                    <label
                      htmlFor="file-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                    >
                      <span>Upload a file</span>
                      <input
                        id="file-upload"
                        name="file-upload"
                        type="file"
                        ref={fileInputRef}
                        className="sr-only"
                        accept="image/*"
                        onChange={handleFileChange}
                      />
                    </label>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    PNG, JPG, GIF up to 10MB
                  </p>
                </div>
              </div>
              
              {previewUrl && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Preview</h4>
                  <div className="relative h-64 w-full overflow-hidden rounded-md border border-gray-300">
                    <Image
                      src={previewUrl}
                      alt="Document preview"
                      fill
                      style={{ objectFit: 'contain' }}
                    />
                  </div>
                </div>
              )}
              
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <h4 className="text-md font-medium text-blue-800 mb-2">Tips for best results:</h4>
                <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
                  <li>Ensure the handwriting is clear and readable</li>
                  <li>Good lighting and a high-resolution image will improve accuracy</li>
                  <li>Avoid shadows across the document</li>
                  <li>Include workout date, exercises, sets, reps and weights in the document</li>
                </ul>
              </div>
            </div>
          )}
          
          {step === 'processing' && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Processing your document</h3>
              <p className="text-gray-500">
                We're using OCR to extract workout data from your image. This may take a moment.
              </p>
            </div>
          )}
          
          {step === 'review' && ocrResult && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">Original Document</h4>
                  {previewUrl && (
                    <div className="relative h-64 w-full overflow-hidden rounded-md border border-gray-300">
                      <Image
                        src={previewUrl}
                        alt="Document preview"
                        fill
                        style={{ objectFit: 'contain' }}
                      />
                    </div>
                  )}
                  
                  <div className="mt-4">
                    <h4 className="text-md font-medium text-gray-700 mb-2">Extracted Text</h4>
                    <pre className="p-3 bg-gray-50 rounded-md border border-gray-200 text-xs text-gray-700 whitespace-pre-wrap h-40 overflow-y-auto">
                      {ocrResult.ocr_text}
                    </pre>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">
                    Detected Workouts ({ocrResult.workout_records.length})
                  </h4>
                  
                  {ocrResult.workout_records.length > 0 ? (
                    <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                      {ocrResult.workout_records.map((workout, index) => (
                        <div key={index} className="border border-gray-200 rounded-md p-4">
                          <div className="grid grid-cols-2 mb-2">
                            <div>
                              <span className="text-xs text-gray-500">Date</span>
                              <p className="font-medium">{formatDate(workout.date)}</p>
                            </div>
                            <div>
                              <span className="text-xs text-gray-500">Type</span>
                              <p className="font-medium">{workout.type}</p>
                            </div>
                          </div>
                          <div className="mb-2">
                            <span className="text-xs text-gray-500">Duration</span>
                            <p className="font-medium">{workout.duration} minutes</p>
                          </div>
                          
                          {workout.exercises.length > 0 && (
                            <div>
                              <span className="text-xs text-gray-500">Exercises</span>
                              <div className="mt-1 border-t border-gray-100">
                                {workout.exercises.map((exercise, exIndex) => (
                                  <div key={exIndex} className="py-2 flex flex-wrap">
                                    <div className="w-full font-medium text-sm">
                                      {exercise.name}
                                    </div>
                                    <div className="text-xs text-gray-600 flex space-x-3 mt-1">
                                      <span>{exercise.sets} sets</span>
                                      <span>{exercise.reps} reps</span>
                                      <span>{exercise.weight} lbs</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-6 text-center border border-gray-200 rounded-md">
                      <p className="text-gray-500">No workouts detected</p>
                    </div>
                  )}
                </div>
              </div>
              
              {ocrResult.workout_records.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                  <h4 className="text-md font-medium text-yellow-800 mb-2">Review Carefully</h4>
                  <p className="text-sm text-yellow-700">
                    Please review the extracted workout data before saving. OCR technology can sometimes misinterpret handwritten text.
                    You'll be able to edit these workouts after saving if needed.
                  </p>
                </div>
              )}
            </div>
          )}
          
          {step === 'saving' && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Saving Workouts</h3>
              <p className="text-gray-500">
                Adding the detected workouts to your database...
              </p>
            </div>
          )}
        </div>
        
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <Button
            variant="outline"
            onClick={() => {
              if (step === 'review') {
                setStep('upload');
              } else {
                resetState();
                onClose();
              }
            }}
            disabled={isLoading || step === 'processing' || step === 'saving'}
          >
            {step === 'review' ? 'Back' : 'Cancel'}
          </Button>
          
          {step === 'upload' && (
            <Button
              variant="primary"
              onClick={processImage}
              disabled={!file || !selectedClientId || isLoading}
            >
              Process Document
            </Button>
          )}
          
          {step === 'review' && ocrResult && (
            <Button
              variant="primary"
              onClick={saveWorkouts}
              disabled={ocrResult.workout_records.length === 0 || isLoading}
            >
              Save {ocrResult.workout_records.length} Workout{ocrResult.workout_records.length !== 1 ? 's' : ''}
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
} 