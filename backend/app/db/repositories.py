"""
Database repository classes.

This module provides repository classes for database operations,
implementing the repository pattern to abstract database access.
"""

from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from .models import Client, Workout, Exercise, APIKey

# Generic type for models
T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository for common database operations."""
    
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model
    
    def get_by_id(self, id: UUID) -> Optional[T]:
        """Get a record by its ID."""
        return self.session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination."""
        return self.session.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, data: Dict[str, Any]) -> T:
        """Create a new record."""
        db_item = self.model(**data)
        self.session.add(db_item)
        self.session.commit()
        self.session.refresh(db_item)
        return db_item
    
    def update(self, id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing record."""
        db_item = self.get_by_id(id)
        if db_item:
            for key, value in data.items():
                setattr(db_item, key, value)
            self.session.commit()
            self.session.refresh(db_item)
        return db_item
    
    def delete(self, id: UUID) -> bool:
        """Delete a record by its ID."""
        db_item = self.get_by_id(id)
        if db_item:
            self.session.delete(db_item)
            self.session.commit()
            return True
        return False

class AsyncBaseRepository(Generic[T]):
    """Async base repository for common database operations."""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get a record by its ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new record."""
        db_item = self.model(**data)
        self.session.add(db_item)
        await self.session.commit()
        await self.session.refresh(db_item)
        return db_item
    
    async def update(self, id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing record."""
        db_item = await self.get_by_id(id)
        if db_item:
            for key, value in data.items():
                setattr(db_item, key, value)
            await self.session.commit()
            await self.session.refresh(db_item)
        return db_item
    
    async def delete(self, id: UUID) -> bool:
        """Delete a record by its ID."""
        db_item = await self.get_by_id(id)
        if db_item:
            await self.session.delete(db_item)
            await self.session.commit()
            return True
        return False

class ClientRepository(BaseRepository[Client]):
    """Repository for Client model operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Client)
    
    def get_by_email(self, email: str) -> Optional[Client]:
        """Get a client by email."""
        return self.session.query(Client).filter(Client.email == email).first()
    
    def get_with_workouts(self, client_id: UUID) -> Optional[Client]:
        """Get a client with all their workouts."""
        return self.session.query(Client).filter(Client.id == client_id).first()

class AsyncClientRepository(AsyncBaseRepository[Client]):
    """Async repository for Client model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Client)
    
    async def get_by_email(self, email: str) -> Optional[Client]:
        """Get a client by email."""
        result = await self.session.execute(
            select(Client).where(Client.email == email)
        )
        return result.scalars().first()

class WorkoutRepository(BaseRepository[Workout]):
    """Repository for Workout model operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Workout)
    
    def get_by_client(self, client_id: UUID, skip: int = 0, limit: int = 100) -> List[Workout]:
        """Get all workouts for a client."""
        return (
            self.session.query(Workout)
            .filter(Workout.client_id == client_id)
            .order_by(Workout.date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_with_exercises(self, workout_id: UUID) -> Optional[Workout]:
        """Get a workout with all its exercises."""
        return self.session.query(Workout).filter(Workout.id == workout_id).first()

class AsyncWorkoutRepository(AsyncBaseRepository[Workout]):
    """Async repository for Workout model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Workout)
    
    async def get_by_client(self, client_id: UUID, skip: int = 0, limit: int = 100) -> List[Workout]:
        """Get all workouts for a client."""
        result = await self.session.execute(
            select(Workout)
            .where(Workout.client_id == client_id)
            .order_by(Workout.date.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

class ExerciseRepository(BaseRepository[Exercise]):
    """Repository for Exercise model operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Exercise)
    
    def get_by_workout(self, workout_id: UUID) -> List[Exercise]:
        """Get all exercises for a workout."""
        return (
            self.session.query(Exercise)
            .filter(Exercise.workout_id == workout_id)
            .all()
        )

class AsyncExerciseRepository(AsyncBaseRepository[Exercise]):
    """Async repository for Exercise model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Exercise)
    
    async def get_by_workout(self, workout_id: UUID) -> List[Exercise]:
        """Get all exercises for a workout."""
        result = await self.session.execute(
            select(Exercise).where(Exercise.workout_id == workout_id)
        )
        return result.scalars().all()

class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for API Key operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, APIKey)
    
    def get_by_key(self, key: str) -> Optional[APIKey]:
        """Get an API key by its value."""
        return self.session.query(APIKey).filter(APIKey.key == key, APIKey.active == True).first()
    
    def get_by_client(self, client_id: UUID) -> List[APIKey]:
        """Get all API keys for a client."""
        return self.session.query(APIKey).filter(APIKey.client_id == client_id).all()

class AsyncAPIKeyRepository(AsyncBaseRepository[APIKey]):
    """Async repository for API Key operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, APIKey)
    
    async def get_by_key(self, key: str) -> Optional[APIKey]:
        """Get an API key by its value."""
        result = await self.session.execute(
            select(
                APIKey.id,
                APIKey.key,
                APIKey.client_id,
                APIKey.name,
                APIKey.description,
                APIKey.active,
                APIKey.created_at,
                APIKey.last_used_at
            ).where(APIKey.key == key, APIKey.active == True)
        )
        return result.mappings().first()
    
    async def get_by_client(self, client_id: UUID) -> List[APIKey]:
        """Get all API keys for a client."""
        result = await self.session.execute(
            select(APIKey).where(APIKey.client_id == client_id)
        )
        return result.scalars().all() 