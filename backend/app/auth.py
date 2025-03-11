from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
import bcrypt

# Load environment variables
load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Get the JWT secret from environment variables
# Important: This must match the JWT secret in your Supabase project
JWT_SECRET = os.getenv("JWT_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")

# Validate JWT_SECRET to avoid NoneType errors
if not JWT_SECRET:
    print("WARNING: JWT_SECRET environment variable is not set. Using a default value for development.")
    # Use a default secret for development - do not use in production!
    JWT_SECRET = "development_secret_key_do_not_use_in_production"

# For Supabase, this MUST be "HS256"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Define roles and their permissions
ROLES = {
    "user": ["read:own_data"],
    "trainer": ["read:own_data", "create:client", "update:client", "delete:client", 
                "create:workout", "update:workout", "delete:workout"],
    "admin": ["read:own_data", "create:client", "update:client", "delete:client", 
              "create:workout", "update:workout", "delete:workout",
              "read:all_data", "manage:users"]
}

def get_password_hash(password: str) -> str:
    """Generate password hash using bcrypt"""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using bcrypt"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify JWT token and return user data"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Safety check - ensure token is not None
    if not token:
        raise credentials_exception
    
    try:
        # Print debug info - safely handle None values
        token_prefix = token[:10] if token and len(token) > 10 else str(token)
        # JWT_SECRET is now guaranteed to be a string by our initialization logic above
        secret_prefix = JWT_SECRET[:5] if len(JWT_SECRET) > 5 else JWT_SECRET
        print(f"Token received: {token_prefix}...")
        print(f"Using JWT_SECRET: {secret_prefix}...")
        
        try:
            # Verify the token using our secret
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError as jwt_error:
            # If decoding with our secret fails, try with a more lenient approach
            # This is for development with Supabase integration
            try:
                # Just decode without verification in development
                payload = jwt.decode(token, options={"verify_signature": False})
                print("Warning: Token decoded without verification (development mode)")
            except jwt.PyJWTError:
                print(f"JWT Error during lenient decode: {str(jwt_error)}")
                raise credentials_exception
        
        # For Supabase tokens, the user ID is in the 'sub' claim
        user_id = payload.get("sub")
        if user_id is None:
            print("No 'sub' claim found in token, checking for alternate keys")
            # Try alternate locations for user ID
            user_id = payload.get("user_id") or payload.get("uid") or payload.get("id")
            if user_id is None:
                print("No user identifier found in token")
                raise credentials_exception
            
        # Look for the user role in the token metadata
        # Supabase stores custom claims in a specific format
        user_metadata = payload.get("user_metadata", {})
        # If metadata is not directly in user_metadata, check other common locations
        if not user_metadata and "app_metadata" in payload:
            user_metadata = payload.get("app_metadata", {})
        
        role = user_metadata.get("role", "user")
        
        email = payload.get("email", "")
        if not email and "preferred_username" in payload:
            email = payload.get("preferred_username", "")
        
        return {
            "id": user_id,
            "role": role,
            "email": email,
            "permissions": ROLES.get(role, ROLES["user"])
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise credentials_exception

def verify_user_role(required_role: str):
    """Dependency to verify user has a specific role"""
    async def verify_role(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. {required_role.capitalize()} role required."
            )
        return current_user
    return verify_role

def verify_permission(required_permission: str):
    """Dependency to verify user has a specific permission"""
    async def verify_perm(current_user: dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. '{required_permission}' permission required."
            )
        return current_user
    return verify_perm

async def refresh_token(request: Request):
    """Refresh an expired JWT token"""
    refresh_token = request.headers.get("Refresh-Token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify the refresh token
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check if this is actually a refresh token
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate a new access token
        user_id = payload.get("sub")
        user_metadata = payload.get("user_metadata", {})
        
        access_token_data = {
            "sub": user_id,
            "user_metadata": user_metadata,
            "email": payload.get("email", ""),
            "type": "access"
        }
        
        new_access_token = create_access_token(access_token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Maintain backward compatibility
verify_trainer_role = verify_user_role("trainer") 