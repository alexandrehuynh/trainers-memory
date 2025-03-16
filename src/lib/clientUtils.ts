/**
 * Client utility functions for Trainer's Memory application
 * This file provides helper functions for client-related operations
 */

import { Client, clientsApi } from './apiClient';

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