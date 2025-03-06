from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
import jwt
from datetime import datetime, timedelta
from .db import supabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Secret key (should match Supabase JWT secret)
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify JWT token and return user data"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Get user data from Supabase
        response = supabase.auth.admin.get_user_by_id(user_id)
        user = response.user
        
        if user is None:
            raise credentials_exception
            
        return {
            "id": user.id,
            "email": user.email,
            "role": user.user_metadata.get("role", "user") if user.user_metadata else "user"
        }
        
    except jwt.PyJWTError:
        raise credentials_exception

def verify_trainer_role(current_user: dict = Depends(get_current_user)):
    """Verify user has trainer role"""
    if current_user.get("role") != "trainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Trainer role required."
        )
    return current_user 