/**
 * Client utility functions for Trainer's Memory application
 * This file provides helper functions for client-related operations
 */

import { Client, clientsApi } from './apiClient';

/**
 * Validates client data for create/update operations
 * 
 * @param clientData - Client data to validate
 * @returns Validation result with success flag and any errors
 */
export function validateClientData(clientData: any): { success: boolean; errors?: string[] } {
  const errors: string[] = [];
  
  // Check required fields
  if (!clientData.name || typeof clientData.name !== 'string' || clientData.name.trim() === '') {
    errors.push('Name is required');
  } else if (clientData.name.length > 100) {
    errors.push('Name must be 100 characters or less');
  }
  
  if (!clientData.email || typeof clientData.email !== 'string' || clientData.email.trim() === '') {
    errors.push('Email is required');
  } else {
    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(clientData.email)) {
      errors.push('Email is invalid');
    } else if (clientData.email.length > 255) {
      errors.push('Email must be 255 characters or less');
    }
  }
  
  // Optional fields validation
  if (clientData.phone !== undefined && clientData.phone !== null) {
    if (typeof clientData.phone !== 'string') {
      errors.push('Phone must be a string');
    } else if (clientData.phone.length > 20) {
      errors.push('Phone must be 20 characters or less');
    }
  }
  
  if (clientData.notes !== undefined && clientData.notes !== null) {
    if (typeof clientData.notes !== 'string') {
      errors.push('Notes must be a string');
    } else if (clientData.notes.length > 1000) {
      errors.push('Notes must be 1000 characters or less');
    }
  }
  
  return {
    success: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined
  };
}

/**
 * Create a new client with proper error handling
 * 
 * @param clientData - Client data to be created
 * @returns Promise with the created client or error message
 */
export async function createNewClient(clientData: {
  name: string;
  email: string;
  phone?: string;
  notes?: string;
}): Promise<{ success: boolean; client?: Client; error?: string }> {
  try {
    // Validate required fields
    if (!clientData.name || !clientData.email) {
      return {
        success: false,
        error: 'Name and email are required.'
      };
    }

    // Log the operation (with sensitive info redacted)
    console.log('Creating new client:', {
      name: clientData.name,
      email: clientData.email.substring(0, 3) + '***@***' + clientData.email.split('@')[1],
      hasPhone: !!clientData.phone,
      hasNotes: !!clientData.notes
    });

    // Use the clientsApi to create the client
    const newClient = await clientsApi.create(clientData);

    console.log('Client created successfully with ID:', newClient.id);
    
    return {
      success: true,
      client: newClient
    };
  } catch (error: any) {
    // Enhanced error logging
    console.error('Failed to create client:', error.message);
    
    // Return a user-friendly error
    return {
      success: false,
      error: error.message || 'An unexpected error occurred while creating the client.'
    };
  }
}

/**
 * Update an existing client with proper error handling
 * 
 * @param clientId - ID of the client to update
 * @param clientData - Client data to update
 * @returns Promise with the updated client or error message
 */
export async function updateClient(
  clientId: string,
  clientData: Partial<{
    name: string;
    email: string;
    phone: string;
    notes: string;
  }>
): Promise<{ success: boolean; client?: Client; error?: string }> {
  try {
    if (!clientId) {
      return {
        success: false,
        error: 'Client ID is required for updates.'
      };
    }

    console.log(`Updating client ${clientId}`);

    // Use the clientsApi to update the client
    const updatedClient = await clientsApi.update(clientId, clientData);

    return {
      success: true,
      client: updatedClient
    };
  } catch (error: any) {
    console.error(`Failed to update client ${clientId}:`, error.message);
    
    return {
      success: false,
      error: error.message || 'An unexpected error occurred while updating the client.'
    };
  }
} 