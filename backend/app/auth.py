from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Get the JWT secret from environment variables
# Important: This must match the JWT secret in your Supabase project
JWT_SECRET = os.getenv("JWT_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")

# For Supabase, this MUST be "HS256"
JWT_ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify JWT token and return user data"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Print debug info
        print(f"Token received: {token[:10]}...")
        print(f"Using JWT_SECRET: {JWT_SECRET[:5]}...")
        
        # Verify the token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # For Supabase tokens, the user ID is in the 'sub' claim
        user_id = payload.get("sub")
        if user_id is None:
            print("No 'sub' claim found in token")
            raise credentials_exception
            
        # Look for the user role in the token metadata
        # Supabase stores custom claims in a specific format
        user_metadata = payload.get("user_metadata", {})
        role = user_metadata.get("role", "user")
        
        return {
            "id": user_id,
            "role": role,
            "email": payload.get("email", ""),
        }
        
    except jwt.PyJWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise credentials_exception

def verify_trainer_role(current_user: dict = Depends(get_current_user)):
    """Verify user has trainer role"""
    if current_user.get("role") != "trainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Trainer role required."
        )
    return current_user 