from fastapi import Depends, HTTPException, status, Security, Header
from fastapi.security import APIKeyHeader
from typing import Dict, Any, Optional
from .db import AsyncAPIKeyRepository, get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

# Define API key header
API_KEY_NAME = "X-API-Key"
API_KEY_HEADER = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Simple function to get the API key from header
async def get_api_key_header(
    x_api_key: Optional[str] = Header(None, alias=API_KEY_NAME)
) -> str:
    """Get API key from header directly.
    
    This is an alternative to using APIKeyHeader that might work better with Swagger UI.
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return x_api_key

async def get_api_key(
    api_key: str = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Validate API key and return client info.
    
    This dependency function can be used to secure routes that require API key authentication.
    It validates the API key against the database and returns the associated client information.
    
    Args:
        api_key: The API key from the X-API-Key header
        db: Database session
        
    Returns:
        Dict containing client information
        
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Get the API key repository
    key_repo = AsyncAPIKeyRepository(db)
    
    # Validate the API key
    api_key_record = await key_repo.get_by_key(api_key)
    if api_key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Return client info
    return {
        "client_id": api_key_record["client_id"],
        "api_key_id": api_key_record["id"],
        "api_key_name": api_key_record["name"]
    }

# Alternative function that uses the direct header approach
async def validate_api_key(
    api_key: str = Depends(get_api_key_header),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Alternative validation that uses the direct header approach.
    This may work better with Swagger UI in some cases.
    """
    # Get the API key repository
    key_repo = AsyncAPIKeyRepository(db)
    
    # Validate the API key
    api_key_record = await key_repo.get_by_key(api_key)
    if api_key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Return client info
    return {
        "client_id": api_key_record["client_id"],
        "api_key_id": api_key_record["id"],
        "api_key_name": api_key_record["name"]
    } 