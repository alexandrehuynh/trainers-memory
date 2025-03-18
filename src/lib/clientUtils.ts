/**
 * Client utility functions for Trainer's Memory application
 * This file provides helper functions for client-related operations
 */

import { Client, clientsApi } from './apiClient';

/**
 * Client data structure for create/update operations
 */
interface ClientData {
  name: string;
  email: string;
  phone?: string;
  notes?: string;
}

/**
 * Validates client data for create/update operations
 * 
 * @param clientData - Client data to validate
 * @returns Validation result with success flag and any errors
 */
export function validateClientData(clientData: ClientData) {
  const errors: Record<string, string> = {};

  // Check required fields
  if (!clientData.name) {
    errors.name = "Name is required";
  }

  if (!clientData.email) {
    errors.email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(clientData.email)) {
    errors.email = "Please enter a valid email address";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

/**
 * Creates a new client with the provided data
 * @param clientData The client data to create
 * @returns A response object with success status and data or error message
 * @internal This function is used by the UI components
 */
export async function createNewClient(clientData: ClientData) {
  try {
    const { isValid, errors } = validateClientData(clientData);
    
    if (!isValid) {
      console.error('Client validation failed:', errors);
      return { success: false, error: 'Please correct the errors in the form', validationErrors: errors };
    }

    // Create client via API
    const response = await clientsApi.create(clientData);
    
    if (response) {
      console.log('Client created successfully:', response);
      return { success: true, client: response };
    } else {
      console.error('Error creating client');
      return { success: false, error: 'Failed to create client' };
    }
  } catch (error: unknown) {
    console.error('Exception creating client:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'An unknown error occurred while creating the client' 
    };
  }
}

/**
 * Updates an existing client with the provided data
 * @param clientId The ID of the client to update
 * @param clientData The updated client data
 * @returns A response object with success status and data or error message
 * @internal This function is used by the UI components
 */
export async function updateClient(clientId: string, clientData: ClientData) {
  try {
    const { isValid, errors } = validateClientData(clientData);
    
    if (!isValid) {
      console.error('Client validation failed:', errors);
      return { success: false, error: 'Please correct the errors in the form', validationErrors: errors };
    }

    // Update client via API
    const response = await clientsApi.update(clientId, clientData);
    
    if (response) {
      console.log('Client updated successfully:', response);
      return { success: true, client: response };
    } else {
      console.error('Error updating client');
      return { success: false, error: 'Failed to update client' };
    }
  } catch (error: unknown) {
    console.error('Exception updating client:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'An unknown error occurred while updating the client' 
    };
  }
} 