from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid

# Import API key dependency and standard response
from ..main import get_api_key
from ..utils.response import StandardResponse

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
    id: str = Field(..., example="c1d2e3f4-g5h6-i7j8-k9l0-m1n2o3p4q5r6")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

# Create router
router = APIRouter()

# In-memory data store (replace with database in production)
clients_db = {}

# GET /clients - List all clients
@router.get("/clients", response_model=Dict[str, Any])
async def get_clients(
    skip: int = Query(0, ge=0, description="Number of clients to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of clients to return"),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Retrieve a list of clients.
    
    - **skip**: Number of clients to skip (pagination)
    - **limit**: Maximum number of clients to return (pagination)
    """
    clients_list = list(clients_db.values())
    paginated_clients = clients_list[skip:skip+limit]
    
    return StandardResponse.success(
        data={
            "clients": paginated_clients,
            "total": len(clients_db),
            "skip": skip,
            "limit": limit
        },
        message="Clients retrieved successfully"
    )

# GET /clients/{client_id} - Get a specific client
@router.get("/clients/{client_id}", response_model=Dict[str, Any])
async def get_client(
    client_id: str = Path(..., description="The ID of the client to retrieve"),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Retrieve a specific client by ID.
    
    - **client_id**: The unique identifier of the client
    """
    if client_id not in clients_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found"
        )
    
    return StandardResponse.success(
        data=clients_db[client_id],
        message="Client retrieved successfully"
    )

# POST /clients - Create a new client
@router.post("/clients", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_client(
    client: ClientCreate,
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Create a new client.
    
    - **client**: Client data to create
    """
    # Generate a unique ID
    client_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    # Create the client record
    new_client = Client(
        id=client_id,
        created_at=timestamp,
        **client.model_dump()
    )
    
    # Store in our mock database
    clients_db[client_id] = new_client.model_dump()
    
    return StandardResponse.success(
        data=new_client.model_dump(),
        message="Client created successfully"
    )

# PUT /clients/{client_id} - Update a client
@router.put("/clients/{client_id}", response_model=Dict[str, Any])
async def update_client(
    client_update: ClientUpdate,
    client_id: str = Path(..., description="The ID of the client to update"),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Update an existing client.
    
    - **client_id**: The unique identifier of the client to update
    - **client_update**: Client data to update
    """
    if client_id not in clients_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found"
        )
    
    # Get existing client
    existing_client = clients_db[client_id]
    
    # Update fields that are provided
    update_data = client_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        existing_client[field] = value
    
    # Update the timestamp
    existing_client["updated_at"] = datetime.now()
    
    # Save the updated client
    clients_db[client_id] = existing_client
    
    return StandardResponse.success(
        data=existing_client,
        message="Client updated successfully"
    )

# DELETE /clients/{client_id} - Delete a client
@router.delete("/clients/{client_id}", response_model=Dict[str, Any])
async def delete_client(
    client_id: str = Path(..., description="The ID of the client to delete"),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Delete a client.
    
    - **client_id**: The unique identifier of the client to delete
    """
    if client_id not in clients_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found"
        )
    
    # Remove the client
    deleted_client = clients_db.pop(client_id)
    
    return StandardResponse.success(
        data={"id": client_id},
        message="Client deleted successfully"
    )
