"""
Workout models for the API.

This module contains Pydantic models for workout data validation and serialization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

# Exercise models
class ExerciseBase(BaseModel):
    """Base model for exercise data."""
    name: str
    sets: int
    reps: int
    weight: float
    notes: Optional[str] = None

class ExerciseCreate(ExerciseBase):
    """Model for creating a new exercise."""
    pass

class ExerciseUpdate(ExerciseBase):
    """Model for updating an exercise."""
    name: Optional[str] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None

class ExerciseResponse(ExerciseBase):
    """Model for exercise response data."""
    id: str
    
    class Config:
        """Configuration for the model."""
        orm_mode = True
        from_attributes = True

# Workout models
class WorkoutBase(BaseModel):
    """Base model for workout data."""
    client_id: str
    date: str  # ISO format date (YYYY-MM-DD)
    type: str
    duration: int  # Duration in minutes
    notes: Optional[str] = None

class WorkoutCreate(WorkoutBase):
    """Model for creating a new workout."""
    exercises: List[ExerciseCreate]

class WorkoutUpdate(BaseModel):
    """Model for updating a workout."""
    client_id: Optional[str] = None
    date: Optional[str] = None  # ISO format date (YYYY-MM-DD)
    type: Optional[str] = None
    duration: Optional[int] = None  # Duration in minutes
    notes: Optional[str] = None
    exercises: Optional[List[ExerciseCreate]] = None

class WorkoutResponse(WorkoutBase):
    """Model for workout response data."""
    id: str
    client_name: str
    exercises: List[ExerciseResponse]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        """Configuration for the model."""
        orm_mode = True
        from_attributes = True 