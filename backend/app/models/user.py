"""
User models for the API.

This module contains Pydantic models for user data validation and serialization.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base Pydantic model for user data."""
    email: EmailStr
    name: str

class UserCreate(UserBase):
    """Pydantic model for creating a user."""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Pydantic model for updating a user."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_admin: Optional[bool] = None

class UserResponse(UserBase):
    """Pydantic model for user response data."""
    id: str
    is_admin: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        """Configuration for the model."""
        orm_mode = True
        from_attributes = True 