"""
Authentication service module.

This module provides a unified service for handling all authentication-related operations.
"""

import os
import time
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException, status
from typing import Optional, Dict, Any, Union
import logging
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import User, APIKey
from app.config import settings
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# User data model for authenticated users
class UserData(BaseModel):
    """Data model for authenticated user information."""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None
    exp: Optional[int] = None
    is_admin: bool = False


class AuthService:
    """
    Unified authentication service class.
    
    This class handles all aspects of authentication including token generation,
    validation, and API key management.
    """
    
    def __init__(self):
        """Initialize the authentication service with configuration settings."""
        self.jwt_secret = os.environ.get("JWT_SECRET_KEY", settings.JWT_SECRET_KEY)
        self.jwt_algorithm = os.environ.get("JWT_ALGORITHM", settings.JWT_ALGORITHM)
        self.access_token_expire_minutes = int(os.environ.get(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        ))
        self.refresh_token_expire_days = 30  # 30 days for refresh tokens
        self.reset_token_expire_minutes = 15  # 15 minutes for password reset tokens
        
        # Supabase JWT configuration
        self.supabase_jwt_secret = os.environ.get("SUPABASE_JWT_SECRET", settings.SUPABASE_JWT_SECRET)
        if not self.supabase_jwt_secret and settings.SUPABASE_JWT_SECRET:
            logger.info("Using Supabase JWT secret from settings")
            self.supabase_jwt_secret = settings.SUPABASE_JWT_SECRET
        elif not self.supabase_jwt_secret:
            logger.warning("SUPABASE_JWT_SECRET not set. Using JWT_SECRET_KEY as fallback.")
            self.supabase_jwt_secret = self.jwt_secret
            
        # Log configuration (without exposing secrets)
        logger.info(f"JWT settings: ALGORITHM={self.jwt_algorithm}, TOKEN_EXPIRE_MINUTES={self.access_token_expire_minutes}")
        logger.info(f"JWT secret length: {len(self.jwt_secret)} characters")
        logger.info(f"Supabase JWT secret length: {len(self.supabase_jwt_secret) if self.supabase_jwt_secret else 0} characters")
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create a new JWT access token.
        
        Args:
            data: The data to encode in the token.
            
        Returns:
            The encoded JWT token string.
        """
        to_encode = data.copy()
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire.timestamp()})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a new JWT refresh token with longer expiration.
        
        Args:
            data: The data to encode in the token.
            
        Returns:
            The encoded JWT refresh token string.
        """
        to_encode = data.copy()
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire.timestamp(), "token_type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt
    
    def create_password_reset_token(self, user_id: str) -> str:
        """
        Create a password reset token.
        
        Args:
            user_id: The ID of the user requesting password reset.
            
        Returns:
            A JWT token for password reset.
        """
        expires_delta = timedelta(minutes=self.reset_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": user_id,
            "exp": expire.timestamp(),
            "token_type": "reset",
        }
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """
        Verify a password reset token.
        
        Args:
            token: The password reset token to verify.
            
        Returns:
            The user ID if the token is valid, None otherwise.
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Verify token type
            if payload.get("token_type") != "reset":
                logger.warning("Token is not a reset token")
                return None
            
            # Check expiration
            if "exp" in payload:
                expiration = datetime.fromtimestamp(payload["exp"])
                if datetime.utcnow() > expiration:
                    logger.warning("Reset token has expired")
                    return None
            
            # Get user ID
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Reset token missing user ID")
                return None
            
            return user_id
            
        except ExpiredSignatureError:
            logger.warning("Reset token has expired")
            return None
        except PyJWTError as e:
            logger.warning(f"Invalid reset token: {str(e)}")
            return None
    
    def decode_token(self, token: str, verify_signature: bool = True) -> Dict[str, Any]:
        """
        Decode a JWT token without validation.
        
        Args:
            token: The token to decode.
            verify_signature: Whether to verify the token signature.
            
        Returns:
            The decoded token payload.
            
        Raises:
            jwt.PyJWTError: If the token is invalid.
        """
        return jwt.decode(
            token, 
            self.jwt_secret if verify_signature else "", 
            algorithms=[self.jwt_algorithm],
            options={"verify_signature": verify_signature}
        )
    
    def validate_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Validate a JWT token and return its payload if valid.
        
        Args:
            token: The token to validate.
            token_type: The expected token type ('access' or 'refresh').
            
        Returns:
            The decoded token payload if valid.
            
        Raises:
            HTTPException: If the token is invalid or expired.
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check token type if specified in payload
            if "token_type" in payload and payload["token_type"] != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type} token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Check if token is expired
            if "exp" in payload:
                expiration = datetime.fromtimestamp(payload["exp"])
                if datetime.utcnow() > expiration:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
            return payload
            
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def validate_supabase_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a Supabase JWT token.
        
        Args:
            token: The Supabase token to validate.
            
        Returns:
            The decoded token payload if valid.
            
        Raises:
            HTTPException: If the token is invalid or expired.
        """
        if not self.supabase_jwt_secret:
            logger.error("SUPABASE_JWT_SECRET not configured. Cannot validate Supabase tokens.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server authentication configuration error",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Supabase JWTs are signed with HS256
            # Important: jwt.decode will verify the signature by default
            logger.debug(f"Attempting to validate Supabase token (first 10 chars): {token[:10] if token else 'None'}...")
            
            # First try with standard options
            try:
                payload = jwt.decode(
                    token, 
                    self.supabase_jwt_secret, 
                    algorithms=["HS256"],
                    options={"verify_signature": True}
                )
                logger.info("Supabase token validated successfully")
                return payload
            except PyJWTError as e:
                # Try with more lenient options if standard validation fails
                logger.warning(f"Standard Supabase token validation failed: {str(e)}. Trying with leeway...")
                
                # Add leeway for clock skew
                payload = jwt.decode(
                    token, 
                    self.supabase_jwt_secret, 
                    algorithms=["HS256"],
                    options={"verify_signature": True},
                    leeway=30  # 30 seconds of leeway for clock skew
                )
                logger.info("Supabase token validated with leeway")
                return payload
            
        except ExpiredSignatureError:
            logger.warning("Supabase token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except PyJWTError as e:
            logger.error(f"Could not validate Supabase token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def validate_api_key(self, api_key: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Validate an API key and return the associated user data.
        
        Args:
            api_key: The API key to validate.
            db: Database session.
            
        Returns:
            Dictionary containing user and API key information.
            
        Raises:
            HTTPException: If the API key is invalid, expired, or inactive.
        """
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is missing",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        # Query for the API key
        stmt = select(APIKey).where(APIKey.key == api_key)
        result = await db.execute(stmt)
        db_api_key = result.scalars().first()
        
        if not db_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        # Check if the API key is active
        if not db_api_key.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is inactive",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        # Check if the API key is expired
        if db_api_key.expires_at and datetime.utcnow() > db_api_key.expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        # Get the associated user
        stmt = select(User).where(User.id == db_api_key.user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key associated with invalid user",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        # Return user and API key information
        return {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_admin": user.role == "admin",
            "api_key_id": str(db_api_key.id),
            "client_id": str(db_api_key.client_id) if db_api_key.client_id else None
        }
    
    def extract_token_from_authorization(self, authorization: str) -> str:
        """
        Extract the token from the Authorization header.
        
        Args:
            authorization: The Authorization header value.
            
        Returns:
            The extracted token.
            
        Raises:
            HTTPException: If the Authorization header is invalid.
        """
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Use 'Bearer {token}'",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return parts[1]


# Create a singleton instance of the auth service
auth_service = AuthService() 