"""
Authentication API endpoints.

This module contains the API endpoints for authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Header, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
import logging
from datetime import datetime, timedelta
import uuid

from ..db import get_async_db, AsyncAPIKeyRepository
from app.models.user import UserCreate, UserResponse
from ..db.models import User, APIKey
from ..utils.auth_service import auth_service, UserData
from ..dependencies.auth import get_current_user, get_api_key_user
from ..utils.password import verify_password, get_password_hash
from ..utils.response import StandardResponse
from ..utils.error_handlers import handle_exceptions, AuthError, NotFoundError

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

# Authentication models
class UserLogin(BaseModel):
    """Model for user login data."""
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    """Model for user registration data."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str

class Token(BaseModel):
    """Model for token response."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserData

class MigrateApiKeyRequest(BaseModel):
    """Model for API key migration."""
    api_key: str

class CreateApiKeyRequest(BaseModel):
    """Model for creating a new API key."""
    name: str
    client_id: str
    description: Optional[str] = None
    expires_in_days: Optional[int] = None

class ApiKeyResponse(BaseModel):
    """Model for API key response."""
    id: str
    name: str
    key: str
    client_id: str
    user_id: str
    description: Optional[str] = None
    active: bool
    created_at: str
    expires_at: Optional[str] = None

class PasswordResetRequest(BaseModel):
    """Model for requesting a password reset."""
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    """Model for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8)

class ResetPasswordRequest(BaseModel):
    """Model for resetting password with token."""
    token: str
    new_password: str = Field(..., min_length=8)

class CheckTokenRequest(BaseModel):
    """Model for token validation request."""
    token: str

@router.post("/login", response_model=Token)
@handle_exceptions
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Login endpoint.
    
    Authenticates a user and returns JWT tokens.
    """
    # Query the user by email
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalars().first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.password):
        raise AuthError("Incorrect email or password")
    
    # Check if user is active
    if hasattr(user, 'is_active') and not user.is_active:
        raise AuthError("User account is inactive")
    
    # Create tokens using the AuthService
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role if hasattr(user, 'role') else None,
    }
    
    # Access token with shorter expiration
    access_token = auth_service.create_access_token(token_data)
    
    # Refresh token with longer expiration
    refresh_token = auth_service.create_refresh_token(token_data)
    
    # Create user data for response
    user_data = UserData(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role if hasattr(user, 'role') else None,
        is_admin=user.role == "admin" if hasattr(user, 'role') else False
    )
    
    # Return token response
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": auth_service.access_token_expire_minutes * 60,
        "user": user_data
    }

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register endpoint.
    
    Creates a new user and returns JWT tokens.
    """
    try:
        # Check if user already exists
        query = select(User).where(User.email == user_data.email)
        result = await db.execute(query)
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            id=uuid.uuid4(),
            email=user_data.email,
            password=hashed_password,
            name=user_data.name,
            is_active=True,
            is_admin=False,
            role="user",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Create tokens
        token_data = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
        }
        
        # Access token with shorter expiration
        access_token = auth_service.create_access_token(token_data)
        
        # Refresh token with longer expiration
        refresh_token = auth_service.create_refresh_token(token_data)
        
        # Return token response
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": auth_service.access_token_expire_minutes * 60,
            "user": UserData(
                user_id=str(new_user.id),
                email=new_user.email,
                name=new_user.name,
                role="user",
                is_admin=False
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
@handle_exceptions
async def refresh(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh token endpoint.
    
    Uses a refresh token to generate a new access token.
    """
    try:
        # Validate the refresh token
        payload = auth_service.validate_token(refresh_token, token_type="refresh")
        
        # Get user ID from token
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise AuthError("Invalid refresh token")
        
        # Verify user exists
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise NotFoundError("User", user_id)
        
        # Create new tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role if hasattr(user, 'role') else None,
        }
        
        # Create new access token
        new_access_token = auth_service.create_access_token(token_data)
        
        # Create new refresh token
        new_refresh_token = auth_service.create_refresh_token(token_data)
        
        # Create user data for response
        user_data = UserData(
            user_id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role if hasattr(user, 'role') else None,
            is_admin=user.role == "admin" if hasattr(user, 'role') else False
        )
        
        # Return token response
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": auth_service.access_token_expire_minutes * 60,
            "user": user_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise AuthError(f"Error refreshing token: {str(e)}")

@router.post("/migrate-api-key", response_model=Token)
async def migrate_api_key(
    request: MigrateApiKeyRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Migrate from API key to JWT tokens.
    
    Validates an API key and returns JWT tokens for the associated user.
    """
    try:
        # Get API key repository
        api_key_repo = AsyncAPIKeyRepository(db)
        
        # Validate API key
        api_key_record = await api_key_repo.get_by_key(request.api_key)
        if not api_key_record:
            logger.warning(f"Invalid API key during migration")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        # Check if API key is expired
        if hasattr(api_key_record, 'expires_at') and api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            logger.warning(f"Expired API key during migration")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        # Get user associated with the API key
        user_id = api_key_record.user_id
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            logger.warning(f"User not found for API key")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User associated with this API key not found"
            )
        
        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
        }
        
        # Generate tokens
        access_token = auth_service.create_access_token(token_data)
        refresh_token = auth_service.create_refresh_token(token_data)
        
        # Update last_used_at timestamp
        if hasattr(api_key_record, 'last_used_at'):
            await api_key_repo.update(api_key_record.id, {"last_used_at": datetime.utcnow()})
        
        # Return token response
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": auth_service.access_token_expire_minutes * 60,
            "user": UserData(
                user_id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role if hasattr(user, 'role') else "user",
                is_admin=user.is_admin if hasattr(user, 'is_admin') else False
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key migration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API key migration error: {str(e)}"
        )

@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    request: CreateApiKeyRequest,
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new API key for the current user.
    """
    try:
        # Generate a new API key
        api_key = f"tmk_{uuid.uuid4().hex}"
        
        # Calculate expiration if provided
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        
        # Create API key record
        api_key_record = APIKey(
            id=uuid.uuid4(),
            key=api_key,
            name=request.name,
            description=request.description,
            client_id=request.client_id,  # Client this key belongs to
            user_id=current_user.user_id,  # User who created this key
            active=True,
            created_at=datetime.utcnow(),
            last_used_at=None,
            expires_at=expires_at
        )
        
        # Save to database
        db.add(api_key_record)
        await db.commit()
        await db.refresh(api_key_record)
        
        # Return response
        return {
            "id": str(api_key_record.id),
            "name": api_key_record.name,
            "key": api_key_record.key,  # Include the key in the response
            "client_id": str(api_key_record.client_id),
            "user_id": str(api_key_record.user_id),
            "description": api_key_record.description,
            "active": api_key_record.active,
            "created_at": api_key_record.created_at.isoformat(),
            "expires_at": api_key_record.expires_at.isoformat() if api_key_record.expires_at else None
        }
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating API key: {str(e)}"
        )

@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all API keys for the current user.
    """
    try:
        # Query API keys for the current user
        query = select(APIKey).where(APIKey.user_id == current_user.user_id)
        result = await db.execute(query)
        api_keys = result.scalars().all()
        
        # Format response
        response = []
        for key in api_keys:
            response.append({
                "id": str(key.id),
                "name": key.name,
                "key": key.key[:8] + "..." + key.key[-4:],  # Mask the key
                "client_id": str(key.client_id),
                "user_id": str(key.user_id),
                "description": key.description,
                "active": key.active,
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None
            })
        
        return response
    except Exception as e:
        logger.error(f"Error retrieving API keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving API keys: {str(e)}"
        )

@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: str,
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete an API key belonging to the current user.
    """
    try:
        # Get API key repository
        api_key_repo = AsyncAPIKeyRepository(db)
        
        # Check if API key exists and belongs to user
        api_key = await api_key_repo.get_by_id(api_key_id, current_user.user_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key with ID {api_key_id} not found or doesn't belong to you"
            )
        
        # Delete the API key
        success = await api_key_repo.delete(api_key_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete API key {api_key_id}"
            )
        
        # Return no content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting API key: {str(e)}"
        )

@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Request a password reset.
    
    This endpoint sends a password reset email with a token.
    """
    try:
        # Find user by email
        query = select(User).where(User.email == request.email)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            # Don't reveal that the email doesn't exist
            # Just return success to prevent email enumeration attacks
            logger.info(f"Password reset requested for non-existent email: {request.email}")
            return
        
        # Create password reset token
        reset_token = auth_service.create_password_reset_token(str(user.id))
        
        # In a real application, you would send an email with the reset token
        # For this example, we'll just log it
        logger.info(f"Password reset token for {user.email}: {reset_token}")
        
        # Return no content (success)
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}")
        # Don't reveal errors to prevent email enumeration
        # Just return success
        return

@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Reset a password using a reset token.
    """
    try:
        # Verify the reset token
        user_id = auth_service.verify_password_reset_token(request.token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Find the user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash the new password
        hashed_password = get_password_hash(request.new_password)
        
        # Update the user's password
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(password=hashed_password, updated_at=datetime.utcnow())
        )
        await db.execute(stmt)
        await db.commit()
        
        # Return success message
        return {"message": "Password has been reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting password"
        )

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Change the current user's password.
    """
    try:
        # Find the user
        query = select(User).where(User.id == current_user.user_id)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(request.current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash the new password
        hashed_password = get_password_hash(request.new_password)
        
        # Update the user's password
        stmt = (
            update(User)
            .where(User.id == current_user.user_id)
            .values(password=hashed_password, updated_at=datetime.utcnow())
        )
        await db.execute(stmt)
        await db.commit()
        
        # Return success message
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get information about the current user.
    """
    try:
        # Find the user
        query = select(User).where(User.id == current_user.user_id)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return user info (excluding password)
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_admin=user.is_admin if hasattr(user, 'is_admin') else False,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )

@router.post("/debug-token")
async def debug_token(token: str = Body(...)):
    """
    Debug a JWT token without validating it.
    This is a diagnostic endpoint to help identify token issues.
    
    Args:
        token: The JWT token to debug
        
    Returns:
        Information about the token structure and claims
    """
    try:
        # Check basic structure
        parts = token.split('.')
        if len(parts) != 3:
            return StandardResponse.error(
                "Invalid JWT format - not a 3-part token", 
                status_code=400
            )
        
        # Decode header and payload (without verification)
        import base64
        import json
        
        # Decode header
        header_b64 = parts[0]
        # Add padding if needed
        padding_needed = len(header_b64) % 4
        if padding_needed:
            header_b64 += '=' * (4 - padding_needed)
            
        try:
            header_bytes = base64.b64decode(header_b64)
            header = json.loads(header_bytes.decode('utf-8'))
        except Exception as e:
            header = {"error": f"Could not decode header: {str(e)}"}
            
        # Decode payload
        payload_b64 = parts[1]
        # Add padding if needed
        padding_needed = len(payload_b64) % 4
        if padding_needed:
            payload_b64 += '=' * (4 - padding_needed)
            
        try:
            payload_bytes = base64.b64decode(payload_b64)
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            # Calculate and format expiration time
            if "exp" in payload:
                from datetime import datetime
                exp_timestamp = payload["exp"]
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                payload["exp_formatted"] = exp_datetime.isoformat()
                payload["exp_status"] = "Expired" if datetime.now() > exp_datetime else "Valid"
                
            # Check issued at time
            if "iat" in payload:
                iat_timestamp = payload["iat"]
                iat_datetime = datetime.fromtimestamp(iat_timestamp)
                payload["iat_formatted"] = iat_datetime.isoformat()
        except Exception as e:
            payload = {"error": f"Could not decode payload: {str(e)}"}
        
        # Try different validation approaches
        from app.auth_utils import JWT_SECRET, SUPABASE_JWT_SECRET, JWT_ALGORITHM
        validation_results = []
        
        # Method 1: Standard JWT decoding
        try:
            import jwt
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            validation_results.append({"method": "JWT_SECRET", "status": "success"})
        except Exception as e:
            validation_results.append({"method": "JWT_SECRET", "status": "failed", "error": str(e)})
        
        # Method 2: Supabase JWT secret
        try:
            import jwt
            decoded = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[JWT_ALGORITHM])
            validation_results.append({"method": "SUPABASE_JWT_SECRET", "status": "success"})
        except Exception as e:
            validation_results.append({"method": "SUPABASE_JWT_SECRET", "status": "failed", "error": str(e)})
            
        # Method 3: Raw binary Supabase JWT secret
        try:
            import jwt
            import base64
            padded_secret = SUPABASE_JWT_SECRET
            if len(padded_secret) % 4 != 0:
                padded_secret += '=' * (4 - len(padded_secret) % 4)
                
            jwt_secret_bytes = base64.b64decode(padded_secret)
            decoded = jwt.decode(token, jwt_secret_bytes, algorithms=[JWT_ALGORITHM])
            validation_results.append({"method": "RAW_BINARY_SUPABASE_JWT_SECRET", "status": "success"})
        except Exception as e:
            validation_results.append({"method": "RAW_BINARY_SUPABASE_JWT_SECRET", "status": "failed", "error": str(e)})
            
        return StandardResponse.success({
            "token_structure": {
                "parts": len(parts),
                "header": header,
                "payload": payload,
                "signature_length": len(parts[2])
            },
            "validation_results": validation_results
        })
    except Exception as e:
        return StandardResponse.error(f"Error analyzing token: {str(e)}", status_code=500)

@router.post("/check-token")
async def check_token_validity(token_data: CheckTokenRequest = Body(...)):
    """
    Check if a token is valid without requiring authentication.
    
    This endpoint allows clients to check if their token is still valid
    without making an authenticated request that might fail.
    
    Args:
        token_data: The request containing the JWT token to check
        
    Returns:
        A response indicating if the token is valid
    """
    token = token_data.token
    
    # Log token first few chars for debugging (only in development)
    if token and len(token) > 10:
        logger.debug(f"Checking token validity, token starts with: {token[:10]}...")
    else:
        logger.warning("Invalid token format received")
        return StandardResponse.success(
            {"valid": False, "reason": "Invalid token format"},
            message="Token validation failed"
        )
    
    # Try to validate the token
    try:
        # First try to validate as a Supabase token
        try:
            payload = auth_service.validate_supabase_token(token)
            logger.info("Supabase token validation succeeded")
            return StandardResponse.success(
                {"valid": True, "type": "supabase"},
                message="Token validation completed"
            )
        except HTTPException:
            # If Supabase validation fails, try as a regular JWT
            payload = auth_service.validate_token(token)
            logger.info("JWT token validation succeeded")
            return StandardResponse.success(
                {"valid": True, "type": "jwt"},
                message="Token validation completed"
            )
    except HTTPException as e:
        logger.warning(f"Token validation failed: {e.detail}")
        return StandardResponse.success(
            {"valid": False, "reason": e.detail},
            message="Token validation failed"
        )
    except Exception as e:
        logger.error(f"Error in token validation: {str(e)}")
        return StandardResponse.success(
            {"valid": False, "reason": "Internal validation error"},
            message="Token validation failed"
        ) 