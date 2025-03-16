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
from sqlalchemy import update, delete, text
from .models import User, Client, Workout, Exercise, APIKey, WorkoutTemplate, TemplateExercise
import logging

logger = logging.getLogger(__name__)

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
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalars().first()
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            await self.session.rollback()
            return None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination."""
        try:
            result = await self.session.execute(
                select(self.model).offset(skip).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            print(f"Error in get_all: {e}")
            await self.session.rollback()
            return []
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new record."""
        try:
            db_item = self.model(**data)
            self.session.add(db_item)
            await self.session.commit()
            await self.session.refresh(db_item)
            return db_item
        except Exception as e:
            print(f"Error in create: {e}")
            await self.session.rollback()
            raise
    
    async def update(self, id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing record."""
        try:
            db_item = await self.get_by_id(id)
            if db_item:
                for key, value in data.items():
                    setattr(db_item, key, value)
                await self.session.commit()
                await self.session.refresh(db_item)
            return db_item
        except Exception as e:
            print(f"Error in update: {e}")
            await self.session.rollback()
            raise
    
    async def delete(self, id: UUID) -> bool:
        """Delete a record by its ID."""
        try:
            db_item = await self.get_by_id(id)
            if db_item:
                await self.session.delete(db_item)
                await self.session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error in delete: {e}")
            await self.session.rollback()
            return False

class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.session.query(User).filter(User.email == email).first()

class AsyncUserRepository(AsyncBaseRepository[User]):
    """Async repository for User model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

class ClientRepository(BaseRepository[Client]):
    """Repository for Client model operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Client)
    
    def get_by_email(self, email: str, user_id: UUID) -> Optional[Client]:
        """Get a client by email and user ID for data isolation."""
        return self.session.query(Client).filter(Client.email == email, Client.user_id == user_id).first()
    
    def get_with_workouts(self, client_id: UUID, user_id: UUID = None) -> Optional[Client]:
        """Get a client with all their workouts."""
        query = self.session.query(Client).filter(Client.id == client_id)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.filter(Client.user_id == user_id)
            
        return query.first()
    
    def get_by_id(self, id: UUID, user_id: UUID = None) -> Optional[Client]:
        """Get a client by ID with optional user isolation."""
        query = self.session.query(Client).filter(Client.id == id)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.filter(Client.user_id == user_id)
            
        return query.first()
    
    def get_all(self, skip: int = 0, limit: int = 100, user_id: UUID = None) -> List[Client]:
        """Get all clients with pagination and optional user isolation."""
        query = self.session.query(Client)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.filter(Client.user_id == user_id)
            
        return query.offset(skip).limit(limit).all()

class AsyncClientRepository(AsyncBaseRepository[Client]):
    """Async repository for Client model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Client)
    
    async def get_by_email(self, email: str, user_id: UUID) -> Optional[Client]:
        """Get a client by email and user ID for data isolation."""
        result = await self.session.execute(
            select(Client).where(Client.email == email, Client.user_id == user_id)
        )
        return result.scalars().first()
    
    async def get_by_id(self, id: UUID, user_id: UUID = None) -> Optional[Client]:
        """Get a client by ID with optional user isolation."""
        query = select(Client).where(Client.id == id)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.where(Client.user_id == user_id)
            
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_all(self, skip: int = 0, limit: int = 100, user_id: UUID = None) -> List[Client]:
        """Get all clients with pagination and optional user isolation."""
        try:
            query = select(Client)
            
            # Apply user isolation unless user_id is None (admin bypass)
            if user_id is not None:
                query = query.where(Client.user_id == user_id)
                
            result = await self.session.execute(
                query.offset(skip).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            # Log the error
            print(f"Error in AsyncClientRepository.get_all: {e}")
            
            # Roll back the transaction to clear the error state
            await self.session.rollback()
            
            # Try a simpler query as a fallback
            try:
                # If we got here, the session was in a failed state
                # Execute a simple query to reset the session
                await self.session.execute(text("SELECT 1"))
                
                # Now retry with a simpler query
                if user_id is not None:
                    sql = text("""
                        SELECT id, name, email, phone, notes, created_at, updated_at
                        FROM clients 
                        WHERE user_id = :user_id
                        OFFSET :skip
                        LIMIT :limit
                    """).bindparams(user_id=user_id, skip=skip, limit=limit)
                else:
                    sql = text("""
                        SELECT id, name, email, phone, notes, created_at, updated_at
                        FROM clients
                        OFFSET :skip
                        LIMIT :limit
                    """).bindparams(skip=skip, limit=limit)
                
                result = await self.session.execute(sql)
                
                # Convert the rows to Client objects
                clients = []
                for row in result.fetchall():
                    client = Client()
                    client.id = row[0]
                    client.name = row[1]
                    client.email = row[2]
                    client.phone = row[3]
                    client.notes = row[4]
                    client.created_at = row[5]
                    client.updated_at = row[6]
                    clients.append(client)
                
                return clients
            except Exception as inner_e:
                print(f"Error in fallback query: {inner_e}")
                return []

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
    
    def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Workout]:
        """Get all workouts for a specific user through the client relationship."""
        return (
            self.session.query(Workout)
            .join(Client, Workout.client_id == Client.id)
            .filter(Client.user_id == user_id)
            .order_by(Workout.date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_id_for_user(self, workout_id: UUID, user_id: UUID = None) -> Optional[Workout]:
        """Get a workout by ID, ensuring it belongs to the specified user."""
        query = self.session.query(Workout).filter(Workout.id == workout_id)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.join(Client, Workout.client_id == Client.id).filter(Client.user_id == user_id)
            
        return query.first()

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
    
    async def get_all(self, skip: int = 0, limit: int = 100, user_id: UUID = None) -> List[Workout]:
        """Get all workouts with pagination and optional user isolation."""
        try:
            if user_id is not None:
                # Join with clients to filter by user_id
                result = await self.session.execute(
                    select(Workout)
                    .join(Client, Workout.client_id == Client.id)
                    .where(Client.user_id == user_id)
                    .order_by(Workout.date.desc())
                    .offset(skip)
                    .limit(limit)
                )
            else:
                # No user isolation
                result = await self.session.execute(
                    select(Workout)
                    .order_by(Workout.date.desc())
                    .offset(skip)
                    .limit(limit)
                )
            return result.scalars().all()
        except Exception as e:
            print(f"Error in get_all: {e}")
            # If there's an error, try a direct SQL query as a fallback
            try:
                if user_id is not None:
                    # Use a raw SQL query with a join
                    result = await self.session.execute(
                        text("""
                            SELECT w.* FROM workouts w
                            JOIN clients c ON w.client_id = c.id
                            WHERE c.user_id = :user_id
                            ORDER BY w.date DESC
                            LIMIT :limit OFFSET :skip
                        """).bindparams(user_id=user_id, limit=limit, skip=skip)
                    )
                else:
                    # No user isolation
                    result = await self.session.execute(
                        text("""
                            SELECT * FROM workouts
                            ORDER BY date DESC
                            LIMIT :limit OFFSET :skip
                        """).bindparams(limit=limit, skip=skip)
                    )
                
                # Convert the result to Workout objects
                workouts = []
                for row in result.fetchall():
                    workout = Workout()
                    workout.id = row[0]  # Assuming id is the first column
                    workout.client_id = row[1]  # Assuming client_id is the second column
                    workout.date = row[2]  # Assuming date is the third column
                    workout.type = row[3]  # Assuming type is the fourth column
                    workout.duration = row[4]  # Assuming duration is the fifth column
                    workout.notes = row[5]  # Assuming notes is the sixth column
                    workout.created_at = row[6]  # Assuming created_at is the seventh column
                    workout.updated_at = row[7]  # Assuming updated_at is the eighth column
                    workouts.append(workout)
                
                return workouts
            except Exception as inner_e:
                print(f"Error in fallback query: {inner_e}")
                return []
    
    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Workout]:
        """Get all workouts for a specific user through the client relationship."""
        result = await self.session.execute(
            select(Workout)
            .join(Client, Workout.client_id == Client.id)
            .where(Client.user_id == user_id)
            .order_by(Workout.date.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_id(self, id: UUID, user_id: UUID = None) -> Optional[Workout]:
        """Get a workout by ID with optional user isolation."""
        query = select(Workout).where(Workout.id == id)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.join(Client, Workout.client_id == Client.id).where(Client.user_id == user_id)
            
        result = await self.session.execute(query)
        return result.scalars().first()

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
    
    def get_by_id_for_user(self, exercise_id: UUID, user_id: UUID = None) -> Optional[Exercise]:
        """Get an exercise by ID, ensuring it belongs to the specified user."""
        query = self.session.query(Exercise).filter(Exercise.id == exercise_id)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.join(Workout, Exercise.workout_id == Workout.id)\
                  .join(Client, Workout.client_id == Client.id)\
                  .filter(Client.user_id == user_id)
            
        return query.first()

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
    
    async def get_by_id(self, id: UUID, user_id: UUID = None) -> Optional[Exercise]:
        """Get an exercise by ID with optional user isolation."""
        query = select(Exercise).where(Exercise.id == id)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.join(Workout, Exercise.workout_id == Workout.id)\
                  .join(Client, Workout.client_id == Client.id)\
                  .where(Client.user_id == user_id)
            
        result = await self.session.execute(query)
        return result.scalars().first()

class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for API Key operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, APIKey)
    
    def get_by_key(self, key: str) -> Optional[APIKey]:
        """Get an API key by its value."""
        return self.session.query(APIKey).filter(APIKey.key == key, APIKey.active == True).first()
    
    def get_by_client(self, client_id: UUID, user_id: UUID = None) -> List[APIKey]:
        """Get all API keys for a client with optional user isolation."""
        query = self.session.query(APIKey).filter(APIKey.client_id == client_id)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.filter(APIKey.user_id == user_id)
            
        return query.all()
    
    def get_all(self, skip: int = 0, limit: int = 100, user_id: UUID = None) -> List[APIKey]:
        """Get all API keys with pagination and optional user isolation."""
        query = self.session.query(APIKey)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.filter(APIKey.user_id == user_id)
            
        return query.offset(skip).limit(limit).all()

class AsyncAPIKeyRepository(AsyncBaseRepository[APIKey]):
    """Async repository for API Key operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, APIKey)
    
    async def get_by_key(self, key: str) -> Optional[APIKey]:
        """Get an API key by its value."""
        try:
            result = await self.session.execute(
                select(APIKey).where(APIKey.key == key, APIKey.active == True)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error in get_by_key using ORM: {e}")
            # If there's an error, try a direct SQL query as a fallback
            try:
                # First, try with user_id included
                try:
                    result = await self.session.execute(
                        text("SELECT id, key, client_id, user_id, name, active FROM api_keys WHERE key = :key AND active = true")
                        .bindparams(key=key)
                    )
                    row = result.fetchone()
                    
                    if row:
                        # Create a simple APIKey object with the available fields
                        api_key = APIKey()
                        api_key.id = row[0]
                        api_key.key = row[1]
                        api_key.client_id = row[2]
                        api_key.user_id = row[3]
                        api_key.name = row[4]
                        api_key.active = row[5]
                        return api_key
                except Exception as column_e:
                    logger.warning(f"Error in fallback query with user_id: {column_e}")
                    
                    # If that fails (possibly due to missing user_id column), try without user_id
                    result = await self.session.execute(
                        text("SELECT id, key, client_id, name, active FROM api_keys WHERE key = :key AND active = true")
                        .bindparams(key=key)
                    )
                    row = result.fetchone()
                    
                    if row:
                        # Create a simple APIKey object with the available fields
                        api_key = APIKey()
                        api_key.id = row[0]
                        api_key.key = row[1]
                        api_key.client_id = row[2]
                        api_key.name = row[3]
                        api_key.active = row[4]
                        # user_id is intentionally not set here as the column doesn't exist
                        return api_key
                return None
            except Exception as inner_e:
                logger.error(f"Error in all fallback queries: {inner_e}")
                return None
    
    async def get_by_client(self, client_id: UUID, user_id: UUID = None) -> List[APIKey]:
        """Get all API keys for a client with optional user isolation."""
        try:
            query = select(APIKey).where(APIKey.client_id == client_id)
            
            # Apply user isolation unless user_id is None (admin bypass)
            if user_id is not None:
                try:
                    query = query.where(APIKey.user_id == user_id)
                except Exception as e:
                    logger.warning(f"Error applying user_id filter: {e}")
                    # Continue without user_id filter if there's an error
                    
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error in get_by_client: {e}")
            return []
    
    async def get_all(self, skip: int = 0, limit: int = 100, user_id: UUID = None) -> List[APIKey]:
        """Get all API keys with pagination and optional user isolation."""
        query = select(APIKey)
        
        # Apply user isolation unless user_id is None (admin bypass)
        if user_id is not None:
            query = query.where(APIKey.user_id == user_id)
            
        result = await self.session.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()

class WorkoutTemplateRepository(BaseRepository[WorkoutTemplate]):
    """Repository for WorkoutTemplate model operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, WorkoutTemplate)
    
    def get_available_templates(self, user_id: UUID) -> List[WorkoutTemplate]:
        """Get all workout templates available to a user (system templates + user's own templates)."""
        return (
            self.session.query(WorkoutTemplate)
            .filter((WorkoutTemplate.is_system == True) | (WorkoutTemplate.user_id == user_id))
            .all()
        )
    
    def get_by_id(self, id: UUID, user_id: UUID = None) -> Optional[WorkoutTemplate]:
        """Get a template by ID with optional user isolation."""
        query = self.session.query(WorkoutTemplate).filter(WorkoutTemplate.id == id)
        
        # Apply user isolation unless user_id is None (admin bypass) but always include system templates
        if user_id is not None:
            query = query.filter((WorkoutTemplate.is_system == True) | (WorkoutTemplate.user_id == user_id))
            
        return query.first()

class AsyncWorkoutTemplateRepository(AsyncBaseRepository[WorkoutTemplate]):
    """Async repository for WorkoutTemplate model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkoutTemplate)
    
    async def get_available_templates(self, user_id: UUID) -> List[WorkoutTemplate]:
        """Get all workout templates available to a user (system templates + user's own templates)."""
        try:
            # Use a simpler query that works with async SQLAlchemy
            if user_id is not None:
                query = select(WorkoutTemplate).where(
                    WorkoutTemplate.user_id == user_id
                )
            else:
                query = select(WorkoutTemplate)
            
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Error in get_available_templates: {e}")
            await self.session.rollback()
            return []
    
    async def get_by_id(self, id: UUID, user_id: UUID = None) -> Optional[WorkoutTemplate]:
        """Get a template by ID with optional user isolation."""
        try:
            query = select(WorkoutTemplate).where(WorkoutTemplate.id == id)
            
            # Apply user isolation unless user_id is None (admin bypass) but always include system templates
            if user_id is not None:
                query = query.where(
                    (WorkoutTemplate.is_system == True) | (WorkoutTemplate.user_id == user_id)
                )
                
            result = await self.session.execute(query)
            return result.scalars().first()
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            await self.session.rollback()
            return None

class TemplateExerciseRepository(BaseRepository[TemplateExercise]):
    """Repository for TemplateExercise model operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, TemplateExercise)
    
    def get_by_template(self, template_id: UUID) -> List[TemplateExercise]:
        """Get all exercises for a template."""
        return self.session.query(TemplateExercise).filter(
            TemplateExercise.template_id == template_id
        ).all()

class AsyncTemplateExerciseRepository(AsyncBaseRepository[TemplateExercise]):
    """Async repository for TemplateExercise model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TemplateExercise)
    
    async def get_by_template(self, template_id: UUID) -> List[TemplateExercise]:
        """Get all exercises for a template."""
        try:
            stmt = select(TemplateExercise).where(TemplateExercise.template_id == template_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            print(f"Error in get_by_template: {e}")
            await self.session.rollback()
            return []
            
    async def create_for_template(self, template_id: UUID, exercise_data: Dict[str, Any]) -> TemplateExercise:
        """Create a new exercise for a template."""
        try:
            # Ensure template_id is set
            exercise_data["template_id"] = template_id
            
            # Create the new exercise
            new_exercise = TemplateExercise(**exercise_data)
            self.session.add(new_exercise)
            await self.session.commit()
            await self.session.refresh(new_exercise)
            return new_exercise
        except Exception as e:
            await self.session.rollback()
            print(f"Error in create_for_template: {e}")
            raise 