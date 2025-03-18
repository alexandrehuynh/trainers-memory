'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/lib/themeContext';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { Workout, Exercise } from '@/lib/apiClient';

interface WorkoutTemplate {
  id: string;
  name: string;
  type: string;
  exercises: Exercise[];
  createdAt: Date;
}

interface WorkoutTemplatesProps {
  onSelectTemplate: (template: WorkoutTemplate) => void;
  currentWorkout?: Workout | null;
}

export default function WorkoutTemplates({ onSelectTemplate, currentWorkout }: WorkoutTemplatesProps) {
  const { theme } = useTheme();
  const [templates, setTemplates] = useState<WorkoutTemplate[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load templates from localStorage when component mounts
    loadTemplates();
  }, []);

  const loadTemplates = () => {
    setIsLoading(true);
    try {
      const savedTemplates = localStorage.getItem('workoutTemplates');
      if (savedTemplates) {
        // Parse the saved templates and convert date strings back to Date objects
        const parsedTemplates = JSON.parse(savedTemplates);
        const templatesWithDates = parsedTemplates.map((template: WorkoutTemplate) => ({
          ...template,
          createdAt: new Date(template.createdAt)
        }));
        setTemplates(templatesWithDates);
      }
    } catch (err) {
      console.error('Error loading workout templates:', err);
      setError('Failed to load workout templates');
    } finally {
      setIsLoading(false);
    }
  };

  const saveTemplate = () => {
    if (!currentWorkout || !templateName.trim()) {
      return;
    }

    try {
      // Create a new template from the current workout
      const newTemplate: WorkoutTemplate = {
        id: crypto.randomUUID(),
        name: templateName.trim(),
        type: currentWorkout.type || 'General Workout',
        exercises: currentWorkout.exercises.map(exercise => ({
          ...exercise,
          id: crypto.randomUUID() // Generate new IDs for the template exercises
        })),
        createdAt: new Date()
      };

      // Add the new template to the list
      const updatedTemplates = [...templates, newTemplate];
      setTemplates(updatedTemplates);

      // Save to localStorage
      localStorage.setItem('workoutTemplates', JSON.stringify(updatedTemplates));

      // Reset form
      setTemplateName('');
      setShowForm(false);
    } catch (err) {
      console.error('Error saving workout template:', err);
      setError('Failed to save workout template');
    }
  };

  const deleteTemplate = (templateId: string) => {
    try {
      // Filter out the template with the given ID
      const updatedTemplates = templates.filter(template => template.id !== templateId);
      setTemplates(updatedTemplates);

      // Save the updated templates to localStorage
      localStorage.setItem('workoutTemplates', JSON.stringify(updatedTemplates));
    } catch (err) {
      console.error('Error deleting workout template:', err);
      setError('Failed to delete workout template');
    }
  };

  if (isLoading) {
    return (
      <Card>
        <div className="flex justify-center py-6">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className={`text-xl font-semibold ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'}`}>
            Workout Templates
          </h2>
          {currentWorkout && (
            <Button 
              variant="outline" 
              onClick={() => setShowForm(!showForm)}
            >
              {showForm ? 'Cancel' : 'Save as Template'}
            </Button>
          )}
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}

        {showForm && currentWorkout && (
          <div className="mb-6 p-4 border border-gray-200 rounded-md">
            <h3 className={`text-md font-medium mb-3 ${theme === 'light' ? 'text-gray-800' : 'text-gray-200'}`}>
              Save Current Workout as Template
            </h3>
            <div className="mb-4">
              <label htmlFor="template-name" className={`block text-sm font-medium ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'} mb-1`}>
                Template Name
              </label>
              <input
                type="text"
                id="template-name"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="e.g., Upper Body Strength"
                className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                  theme === 'light' ? 'bg-white text-gray-900' : 'bg-gray-800 text-white border-gray-700'
                }`}
              />
            </div>
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={saveTemplate}
                disabled={!templateName.trim()}
              >
                Save Template
              </Button>
            </div>
          </div>
        )}

        {templates.length === 0 ? (
          <div className="text-center py-8">
            <p className={`${theme === 'light' ? 'text-gray-500' : 'text-gray-400'} mb-4`}>
              No workout templates saved yet
            </p>
            {currentWorkout && (
              <Button variant="outline" onClick={() => setShowForm(true)}>
                Create Your First Template
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {templates.map((template) => (
              <div 
                key={template.id}
                className={`p-4 border rounded-md ${
                  theme === 'light' ? 'border-gray-200 hover:bg-gray-50' : 'border-gray-700 hover:bg-gray-800'
                } transition-colors`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className={`font-medium ${theme === 'light' ? 'text-gray-900' : 'text-gray-100'}`}>
                      {template.name}
                    </h3>
                    <p className={`text-sm ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
                      {template.type} • {template.exercises.length} exercises
                    </p>
                    <p className={`text-xs ${theme === 'light' ? 'text-gray-400' : 'text-gray-500'} mt-1`}>
                      Created on {template.createdAt.toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onSelectTemplate(template)}
                      className={`px-3 py-1 text-sm rounded-md ${
                        theme === 'light'
                          ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                          : 'bg-blue-900 text-blue-200 hover:bg-blue-800'
                      }`}
                    >
                      Use
                    </button>
                    <button
                      onClick={() => deleteTemplate(template.id)}
                      className={`px-2 py-1 text-sm rounded-md ${
                        theme === 'light'
                          ? 'text-red-600 hover:bg-red-50'
                          : 'text-red-400 hover:bg-red-900'
                      }`}
                    >
                      ×
                    </button>
                  </div>
                </div>
                
                {/* Preview of exercises */}
                <div className="mt-3">
                  <h4 className={`text-xs font-medium uppercase tracking-wider ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'} mb-1`}>
                    Exercises
                  </h4>
                  <div className="text-sm">
                    {template.exercises.slice(0, 3).map((exercise, index) => (
                      <span key={exercise.id} className={theme === 'light' ? 'text-gray-700' : 'text-gray-300'}>
                        {exercise.name}
                        {index < Math.min(template.exercises.length, 3) - 1 && ", "}
                      </span>
                    ))}
                    {template.exercises.length > 3 && 
                      <span className={theme === 'light' ? 'text-gray-500' : 'text-gray-400'}>
                        {" "}and {template.exercises.length - 3} more
                      </span>
                    }
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
} 