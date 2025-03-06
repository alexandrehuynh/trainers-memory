from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from ..models import ClientCreate, Client
from ..db import supabase
from ..auth import get_current_user, verify_trainer_role

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    responses={404: {"description": "Not found"}},
)

# Helper functions for database operations
async def get_client_by_id(client_id: str, trainer_id: str):
    """Get client by ID, ensuring it belongs to the trainer"""
    response = (
        supabase.table("clients")
        .select("*")
        .eq("id", client_id)
        .eq("trainer_id", trainer_id)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None

async def get_clients_by_trainer(trainer_id: str, limit: int = 100):
    """Get all clients for a trainer"""
    response = (
        supabase.table("clients")
        .select("*")
        .eq("trainer_id", trainer_id)
        .limit(limit)
        .execute()
    )
    return response.data

async def create_client(client_data: dict):
    """Create a new client"""
    response = supabase.table("clients").insert(client_data).execute()
    return response.data

async def update_client(client_id: str, client_data: dict):
    """Update an existing client"""
    response = (
        supabase.table("clients")
        .update(client_data)
        .eq("id", client_id)
        .execute()
    )
    return response.data

async def delete_client(client_id: str):
    """Delete a client"""
    response = (
        supabase.table("clients")
        .delete()
        .eq("id", client_id)
        .execute()
    )
    return response.data

# API Endpoints
@router.post("/", response_model=List[Client])
async def create_new_client(client: ClientCreate, current_user=Depends(verify_trainer_role)):
    """Create a new client for the trainer"""
    try:
        # Convert Pydantic model to dict
        client_data = client.model_dump()
        
        # Add trainer_id
        client_data["trainer_id"] = current_user["id"]
        
        # Create client
        result = await create_client(client_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}",
        )

@router.get("/", response_model=List[Client])
async def get_all_clients(limit: int = 100, current_user=Depends(verify_trainer_role)):
    """Get all clients for the trainer"""
    try:
        clients = await get_clients_by_trainer(current_user["id"], limit)
        return clients
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve clients: {str(e)}",
        )

@router.get("/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user=Depends(verify_trainer_role)):
    """Get a specific client by ID"""
    try:
        client = await get_client_by_id(client_id, current_user["id"])
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found",
            )
        return client
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client: {str(e)}",
        )

@router.put("/{client_id}", response_model=List[Client])
async def update_client_info(client_id: str, client: ClientCreate, current_user=Depends(verify_trainer_role)):
    """Update a client's information"""
    try:
        # Check if client exists and belongs to this trainer
        existing_client = await get_client_by_id(client_id, current_user["id"])
        if not existing_client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found",
            )
        
        # Convert Pydantic model to dict
        client_data = client.model_dump()
        
        # Update client
        result = await update_client(client_id, client_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client: {str(e)}",
        )

@router.delete("/{client_id}", response_model=List[Client])
async def delete_client_record(client_id: str, current_user=Depends(verify_trainer_role)):
    """Delete a client"""
    try:
        # Check if client exists and belongs to this trainer
        existing_client = await get_client_by_id(client_id, current_user["id"])
        if not existing_client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found",
            )
        
        # Delete client
        result = await delete_client(client_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete client: {str(e)}",
        )
