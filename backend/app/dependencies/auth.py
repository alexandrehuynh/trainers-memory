"""
Authentication dependencies for FastAPI.

This module provides dependency functions for authentication in FastAPI applications.
"""

from fastapi import Depends, Header, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.utils.auth_service import auth_service, UserData
from app.db import get_async_db

# Set up logger
logger = logging.getLogger(__name__)

# Security scheme for JWT Bearer tokens
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> UserData:
    """
    Dependency to get the current user from JWT token.
    
    Args:
        credentials: The HTTP Authorization credentials.
        db: Database session.
        
    Returns:
        UserData object containing user information.
        
    Raises:
        HTTPException: If the credentials are invalid.
    """
    try:
        payload = auth_service.validate_token(credentials.credentials)
        
        # Get role from the most appropriate place
        # First check user_metadata.role (Supabase custom role), then top-level role
        role = None
        if "user_metadata" in payload and payload["user_metadata"] and "role" in payload["user_metadata"]:
            role = payload["user_metadata"]["role"]
            logger.debug(f"Using role from user_metadata: {role}")
        else:
            role = payload.get("role")
            logger.debug(f"Using top-level role: {role}")
            
        # If role is 'authenticated' from Supabase but user_metadata has a more specific role, use that
        if role == "authenticated" and "user_metadata" in payload and payload["user_metadata"] and "role" in payload["user_metadata"]:
            role = payload["user_metadata"]["role"]
            logger.info(f"Overriding 'authenticated' role with user_metadata.role: {role}")
        
        # Ensure a valid role exists
        if not role or role == "authenticated":
            logger.warning(f"User {payload.get('sub') or payload.get('user_id')} has no specific role assigned")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No specific role assigned to user. Please contact an administrator.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create user data from payload
        user_data = UserData(
            user_id=payload.get("sub") or payload.get("user_id"),
            email=payload.get("email"),
            name=payload.get("name"),
            role=role,
            tenant_id=payload.get("tenant_id"),
            exp=payload.get("exp"),
            is_admin=role == "admin"
        )
        
        return user_data
    except HTTPException as e:
        # Re-raise HTTPException directly
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: UserData = Depends(get_current_user)
) -> UserData:
    """
    Dependency to get the current active user.
    This could be extended with additional checks like account status.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        UserData object if the user is active.
        
    Raises:
        HTTPException: If the user is inactive.
    """
    # Here you could add additional checks
    # For example, checking if the user is disabled in the database
    return current_user

async def get_api_key_user(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Dependency to get the user from API key.
    
    Args:
        api_key: The API key from header.
        db: Database session.
        
    Returns:
        Dictionary containing user and API key information.
        
    Raises:
        HTTPException: If the API key is invalid.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Validate the API key and get user data
    return await auth_service.validate_api_key(api_key, db)

async def get_user_from_token_or_api_key(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Flexible dependency that tries to authenticate via JWT token first,
    then falls back to API key if token is not present.
    
    Args:
        request: The request object.
        authorization: The Authorization header.
        x_api_key: The API key header.
        db: Database session.
        
    Returns:
        Dictionary containing user information.
        
    Raises:
        HTTPException: If authentication fails.
    """
    # Try JWT token first if available
    if authorization:
        try:
            token = auth_service.extract_token_from_authorization(authorization)
            payload = auth_service.validate_token(token)
            
            # Get role from the most appropriate place
            # First check user_metadata.role (Supabase custom role), then top-level role
            role = None
            if "user_metadata" in payload and payload["user_metadata"] and "role" in payload["user_metadata"]:
                role = payload["user_metadata"]["role"]
                logger.debug(f"Using role from user_metadata: {role}")
            else:
                role = payload.get("role")
                logger.debug(f"Using top-level role: {role}")
                
            # If role is 'authenticated' from Supabase but user_metadata has a more specific role, use that
            if role == "authenticated" and "user_metadata" in payload and payload["user_metadata"] and "role" in payload["user_metadata"]:
                role = payload["user_metadata"]["role"]
                logger.info(f"Overriding 'authenticated' role with user_metadata.role: {role}")
            
            # Ensure a valid role exists
            if not role or role == "authenticated":
                logger.warning(f"User {payload.get('sub') or payload.get('user_id')} has no specific role assigned")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No specific role assigned to user. Please contact an administrator.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return {
                "user_id": payload.get("sub") or payload.get("user_id"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": role,
                "is_admin": role == "admin",
                "auth_type": "jwt"
            }
        except HTTPException:
            # If JWT validation fails, try API key next
            pass
    
    # Try API key if JWT failed or wasn't provided
    if x_api_key:
        try:
            user_data = await auth_service.validate_api_key(x_api_key, db)
            user_data["auth_type"] = "api_key"
            return user_data
        except HTTPException:
            # If API key validation fails, continue to final error
            pass
    
    # If we get here, both auth methods failed or weren't provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer, APIKey"},
    ) 