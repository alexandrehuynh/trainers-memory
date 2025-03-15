from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse

# Import API key dependency and standard response
from ..auth_utils import validate_api_key
from ..utils.response import StandardResponse
from ..db import AsyncClientRepository, get_async_db

# Define models
class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="John Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    phone: Optional[str] = Field(None, min_length=5, max_length=20, example="555-123-4567")
    notes: Optional[str] = Field(None, max_length=1000, example="New client interested in strength training")

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, example="John Doe")
    email: Optional[EmailStr] = Field(None, example="john.doe@example.com")
    phone: Optional[str] = Field(None, min_length=5, max_length=20, example="555-123-4567")
    notes: Optional[str] = Field(None, max_length=1000, example="New client interested in strength training")

class Client(ClientBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ClientResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str = ""
    notes: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Create router
router = APIRouter()

# GET /clients - List all clients
@router.get("/clients", response_model=Dict[str, Any])
async def get_clients(
    skip: int = Query(0, ge=0, description="Number of clients to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of clients to return"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a list of clients.
    
    - **skip**: Number of clients to skip (pagination)
    - **limit**: Maximum number of clients to return (pagination)
    """
    client_repo = AsyncClientRepository(db)
    clients_list = await client_repo.get_all(skip=skip, limit=limit)
    
    # Convert database models to Pydantic models for serialization
    serialized_clients = []
    for client in clients_list:
        serialized_clients.append({
            "id": str(client.id),
            "name": client.name,
            "email": client.email,
            "phone": client.phone or "",
            "notes": client.notes or "",
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None
        })
    
    return StandardResponse.success(
        data={"clients": serialized_clients, "total": len(serialized_clients), "skip": skip, "limit": limit},
        message="Clients retrieved successfully"
    )

# GET /clients/{client_id} - Get a specific client
@router.get("/clients/{client_id}", response_model=Dict[str, Any])
async def get_client(
    client_id: uuid.UUID = Path(..., description="The ID of the client to retrieve"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a specific client by ID.
    
    - **client_id**: UUID of the client to retrieve
    """
    client_repo = AsyncClientRepository(db)
    client = await client_repo.get_by_id(client_id)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found"
        )
    
    # Convert to dictionary for serialization
    client_data = {
        "id": str(client.id),
        "name": client.name,
        "email": client.email,
        "phone": client.phone or "",
        "notes": client.notes or "",
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "updated_at": client.updated_at.isoformat() if client.updated_at else None
    }
    
    return StandardResponse.success(
        data=client_data,
        message="Client retrieved successfully"
    )

# POST /clients - Create a new client
@router.post("/clients", response_model=Dict[str, Any])
async def create_client(
    client: ClientCreate,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new client."""
    client_repo = AsyncClientRepository(db)
    
    # Check if client with this email already exists
    existing_client = await client_repo.get_by_email(client.email)
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Client with email {client.email} already exists"
        )
    
    # Create client
    client_data = client.dict()
    client_data["created_at"] = datetime.utcnow()
    client_data["updated_at"] = datetime.utcnow()
    
    db_client = await client_repo.create(client_data)
    
    # Create the response with the appropriate data
    response_data = StandardResponse.success(
        data={
            "id": str(db_client.id),
            "name": db_client.name,
            "email": db_client.email,
            "phone": db_client.phone,
            "notes": db_client.notes,
            "created_at": db_client.created_at.isoformat() if db_client.created_at else None
        },
        message="Client created successfully"
    )
    
    # Return the response with the desired status code using JSONResponse
    return JSONResponse(
        content=response_data,
        status_code=status.HTTP_201_CREATED
    )

# PUT /clients/{client_id} - Update a client
@router.put("/clients/{client_id}", response_model=Dict[str, Any])
async def update_client(
    client_id: uuid.UUID,
    client_update: ClientUpdate,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a client by ID."""
    client_repo = AsyncClientRepository(db)
    
    # Check if client exists
    client = await client_repo.get_by_id(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found"
        )
    
    # Check if email is being updated to one that already exists
    if client_update.email and client_update.email != client.email:
        existing_client = await client_repo.get_by_email(client_update.email)
        if existing_client and existing_client.id != client_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Client with email {client_update.email} already exists"
            )
    
    # Update client
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    updated_client = await client_repo.update(client_id, update_data)
    
    # Convert to dictionary for serialization
    client_data = {
        "id": str(updated_client.id),
        "name": updated_client.name,
        "email": updated_client.email,
        "phone": updated_client.phone or "",
        "notes": updated_client.notes or "",
        "created_at": updated_client.created_at.isoformat() if updated_client.created_at else None,
        "updated_at": updated_client.updated_at.isoformat() if updated_client.updated_at else None
    }
    
    return StandardResponse.success(
        data=client_data,
        message="Client updated successfully"
    )

# DELETE /clients/{client_id} - Delete a client
@router.delete("/clients/{client_id}", response_model=Dict[str, Any])
async def delete_client(
    client_id: uuid.UUID,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a client by ID."""
    client_repo = AsyncClientRepository(db)
    
    # Check if client exists
    client = await client_repo.get_by_id(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found"
        )
    
    # Delete client
    await client_repo.delete(client_id)
    
    return StandardResponse.success(
        message="Client deleted successfully"
    )
    
# Add a new endpoint to search clients by name
@router.get("/clients/search-by-name", response_model=Dict[str, Any])
async def search_clients_by_name(
    name: str = Query(..., min_length=1, description="Name to search for"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search for clients by name.
    
    - **name**: Name or partial name to search for
    """
    client_repo = AsyncClientRepository(db)
    # Add a method in AsyncClientRepository to search by name
    clients = await client_repo.search_by_name(name)
    
    # Convert to serializable format
    serialized_clients = []
    for client in clients:
        serialized_clients.append({
            "id": str(client.id),
            "name": client.name,
            "email": client.email,
            "phone": client.phone or "",
            "notes": client.notes or "",
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None
        })
    
    return StandardResponse.success(
        data={"clients": serialized_clients, "total": len(serialized_clients)},
        message="Clients found successfully"
    )
