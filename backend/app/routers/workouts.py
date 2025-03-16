from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, UploadFile, File
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Import API key dependency and standard response
from ..auth_utils import validate_api_key
from ..utils.response import StandardResponse
from ..db import (
    AsyncWorkoutRepository,
    AsyncExerciseRepository,
    AsyncClientRepository,
    get_async_db
)

# Set up logging
logger = logging.getLogger(__name__)

# Define models
class ExerciseBase(BaseModel):
    name: str = Field(..., min_length=1, example="Bench Press")
    sets: int = Field(..., ge=1, example=3)
    reps: int = Field(..., ge=0, example=10)
    weight: float = Field(..., ge=0, example=135.0)
    notes: Optional[str] = Field(None, example="Felt strong, could increase weight next time")

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase):
    id: str = Field(..., example="e1f2g3h4-i5j6-k7l8-m9n0-o1p2q3r4s5t6")

    model_config = {"from_attributes": True}

class WorkoutBase(BaseModel):
    client_id: str = Field(..., example="c1d2e3f4-g5h6-i7j8-k9l0-m1n2o3p4q5r6")
    date: str = Field(..., example="2023-05-15", description="ISO format date (YYYY-MM-DD)")
    type: str = Field(..., min_length=1, example="Strength Training")
    duration: int = Field(..., ge=1, description="Duration in minutes", example=60)
    notes: Optional[str] = Field(None, example="Focused on upper body. Increased weight on bench press.")

class WorkoutCreate(WorkoutBase):
    exercises: List[ExerciseCreate] = Field(..., min_items=0)

class WorkoutUpdate(BaseModel):
    client_id: Optional[str] = Field(None, example="c1d2e3f4-g5h6-i7j8-k9l0-m1n2o3p4q5r6")
    date: Optional[str] = Field(None, example="2023-05-15", description="ISO format date (YYYY-MM-DD)")
    type: Optional[str] = Field(None, min_length=1, example="Strength Training")
    duration: Optional[int] = Field(None, ge=1, description="Duration in minutes", example=60)
    notes: Optional[str] = Field(None, example="Focused on upper body. Increased weight on bench press.")
    exercises: Optional[List[ExerciseCreate]] = None

class Workout(WorkoutBase):
    id: str = Field(..., example="w1x2y3z4-a5b6-c7d8-e9f0-g1h2i3j4k5l6")
    client_name: str = Field(..., example="John Doe")
    exercises: List[Exercise] = Field(default=[])
    created_at: datetime

    model_config = {"from_attributes": True}

# Create router
router = APIRouter(
    prefix="/workouts",
    tags=["Workouts"],
    responses={404: {"description": "Not found"}},
)

# Helper function to validate date string
def is_valid_date(date_string: str) -> bool:
    try:
        # Check if the date string is in the correct format
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# GET /workouts - List all workouts
@router.get("/", response_model=Dict[str, Any])
async def get_workouts(
    skip: int = Query(0, ge=0, description="Number of workouts to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of workouts to return"),
    client_id: Optional[str] = Query(None, description="Filter workouts by client ID"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a list of workouts.
    
    - **skip**: Number of workouts to skip (pagination)
    - **limit**: Maximum number of workouts to return (pagination)
    - **client_id**: Optional filter to show only workouts for a specific client
    """
    try:
        logger.info("GET /workouts/ endpoint called")
        logger.info(f"client_info: {client_info}")
        
        workout_repo = AsyncWorkoutRepository(db)
        client_repo = AsyncClientRepository(db)
        exercise_repo = AsyncExerciseRepository(db)
        
        # Get the user_id from client_info for data isolation
        # If user_id is not available, use the client_id as a fallback
        user_id = client_info.get("user_id")
        if user_id is None:
            logger.info("No user_id in client_info, using client_id as fallback")
            # For the test API key, use a default admin user ID
            if client_info.get("api_key_id") == "00000000-0000-0000-0000-000000000099":
                user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
                logger.info(f"Using default admin user_id for test API key: {user_id}")
            else:
                # Use the client_id as a fallback
                user_id = client_info.get("client_id")
                logger.info(f"Using client_id as fallback for user_id: {user_id}")
        
        logger.info(f"user_id: {user_id}")
        
        # Get workouts (filtered by client_id if provided)
        if client_id:
            logger.info(f"Filtering by client_id: {client_id}")
            # First verify the client belongs to this user
            client = await client_repo.get_by_id(uuid.UUID(client_id), user_id=user_id)
            if not client:
                logger.warning(f"Client with ID {client_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Client with ID {client_id} not found"
                )
                
            workouts_list = await workout_repo.get_by_client(
                uuid.UUID(client_id), skip=skip, limit=limit
            )
            total_count = len(workouts_list)
        else:
            logger.info(f"Getting all workouts for user_id: {user_id}")
            workouts_list = await workout_repo.get_all(skip=skip, limit=limit, user_id=user_id)
            total_count = len(workouts_list)
        
        logger.info(f"Found {total_count} workouts")
        
        # Convert to API response format with client names
        serialized_workouts = []
        for workout in workouts_list:
            try:
                # Get client name
                client = await client_repo.get_by_id(workout.client_id, user_id=user_id)
                client_name = client.name if client else "Unknown Client"
                
                # Get exercises for this workout
                exercises = await exercise_repo.get_by_workout(workout.id)
                serialized_exercises = []
                for exercise in exercises:
                    serialized_exercises.append({
                        "id": str(exercise.id),
                        "name": exercise.name,
                        "sets": exercise.sets,
                        "reps": exercise.reps,
                        "weight": float(exercise.weight),
                        "notes": exercise.notes or ""
                    })
                
                # Format workout data
                serialized_workouts.append({
                    "id": str(workout.id),
                    "client_id": str(workout.client_id),
                    "client_name": client_name,
                    "date": workout.date.isoformat() if isinstance(workout.date, datetime) else workout.date,
                    "type": workout.type,
                    "duration": workout.duration,
                    "notes": workout.notes or "",
                    "exercises": serialized_exercises,
                    "created_at": workout.created_at.isoformat() if workout.created_at else None
                })
            except Exception as e:
                logger.error(f"Error processing workout {workout.id}: {str(e)}")
                raise
        
        # Sort by date (newest first)
        serialized_workouts.sort(key=lambda x: x["date"], reverse=True)
        
        logger.info("Successfully processed workouts")
        return StandardResponse.success(
            data={
                "workouts": serialized_workouts,
                "total": total_count,
                "skip": skip,
                "limit": limit
            },
            message="Workouts retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error in get_workouts: {str(e)}")
        raise

# GET /workouts/{workout_id} - Get a specific workout
@router.get("/{workout_id}", response_model=Dict[str, Any])
async def get_workout(
    workout_id: str = Path(..., description="The ID of the workout to retrieve"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a specific workout by ID.
    
    - **workout_id**: The unique identifier of the workout
    """
    workout_repo = AsyncWorkoutRepository(db)
    client_repo = AsyncClientRepository(db)
    exercise_repo = AsyncExerciseRepository(db)
    
    # Get the user_id from client_info for data isolation
    user_id = client_info.get("user_id")
    
    # Get workout with user isolation
    workout = await workout_repo.get_by_id(uuid.UUID(workout_id), user_id=user_id)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    # Get client name
    client = await client_repo.get_by_id(workout.client_id, user_id=user_id)
    client_name = client.name if client else "Unknown Client"
    
    # Get exercises for this workout
    exercises = await exercise_repo.get_by_workout(workout.id)
    serialized_exercises = []
    for exercise in exercises:
        serialized_exercises.append({
            "id": str(exercise.id),
            "name": exercise.name,
            "sets": exercise.sets,
            "reps": exercise.reps,
            "weight": float(exercise.weight),
            "notes": exercise.notes or ""
        })
    
    # Format workout data
    workout_data = {
        "id": str(workout.id),
        "client_id": str(workout.client_id),
        "client_name": client_name,
        "date": workout.date.isoformat() if isinstance(workout.date, datetime) else workout.date,
        "type": workout.type,
        "duration": workout.duration,
        "notes": workout.notes or "",
        "exercises": serialized_exercises,
        "created_at": workout.created_at.isoformat() if workout.created_at else None
    }
    
    return StandardResponse.success(
        data=workout_data,
        message="Workout retrieved successfully"
    )

# POST /workouts - Create a new workout
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def create_workout(
    workout: WorkoutCreate,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new workout.
    
    - **workout**: Workout data to create
    """
    workout_repo = AsyncWorkoutRepository(db)
    client_repo = AsyncClientRepository(db)
    exercise_repo = AsyncExerciseRepository(db)
    
    # Get the user_id from client_info for data isolation
    user_id = client_info.get("user_id")
    
    # Validate client exists and belongs to this user
    client = await client_repo.get_by_id(uuid.UUID(workout.client_id), user_id=user_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {workout.client_id} not found"
        )
    
    # Validate date format
    if not is_valid_date(workout.date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Create workout
    workout_data = workout.dict(exclude={"exercises"})
    workout_data["date"] = datetime.fromisoformat(workout.date)
    workout_data["created_at"] = datetime.utcnow()
    workout_data["updated_at"] = datetime.utcnow()
    
    db_workout = await workout_repo.create(workout_data)
    
    # Create exercises
    exercises_data = []
    for exercise in workout.exercises:
        exercise_data = exercise.dict()
        exercise_data["workout_id"] = db_workout.id
        exercise_data["created_at"] = datetime.utcnow()
        exercise_data["updated_at"] = datetime.utcnow()
        
        db_exercise = await exercise_repo.create(exercise_data)
        exercises_data.append({
            "id": str(db_exercise.id),
            "name": db_exercise.name,
            "sets": db_exercise.sets,
            "reps": db_exercise.reps,
            "weight": float(db_exercise.weight),
            "notes": db_exercise.notes or ""
        })
    
    # Prepare response
    response_data = {
        "id": str(db_workout.id),
        "client_id": str(db_workout.client_id),
        "client_name": client.name,
        "date": db_workout.date.isoformat(),
        "type": db_workout.type,
        "duration": db_workout.duration,
        "notes": db_workout.notes or "",
        "exercises": exercises_data,
        "created_at": db_workout.created_at.isoformat() if db_workout.created_at else None
    }
    
    return StandardResponse.success(
        data=response_data,
        message="Workout created successfully"
    )

# PUT /workouts/{workout_id} - Update a workout
@router.put("/{workout_id}", response_model=Dict[str, Any])
async def update_workout(
    workout_update: WorkoutUpdate,
    workout_id: str = Path(..., description="The ID of the workout to update"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update an existing workout.
    
    - **workout_id**: The unique identifier of the workout to update
    - **workout_update**: Workout data to update
    """
    workout_repo = AsyncWorkoutRepository(db)
    client_repo = AsyncClientRepository(db)
    exercise_repo = AsyncExerciseRepository(db)
    
    # Get the user_id from client_info for data isolation
    user_id = client_info.get("user_id")
    
    # Check if workout exists and belongs to this user
    workout = await workout_repo.get_by_id(uuid.UUID(workout_id), user_id=user_id)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    # Validate client if provided
    if workout_update.client_id:
        client = await client_repo.get_by_id(uuid.UUID(workout_update.client_id), user_id=user_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {workout_update.client_id} not found"
            )
    
    # Validate date format if provided
    if workout_update.date and not is_valid_date(workout_update.date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Update workout
    update_data = {k: v for k, v in workout_update.dict(exclude={"exercises"}).items() if v is not None}
    if "date" in update_data:
        update_data["date"] = datetime.fromisoformat(update_data["date"])
    update_data["updated_at"] = datetime.utcnow()
    
    updated_workout = await workout_repo.update(uuid.UUID(workout_id), update_data)
    
    # Update exercises if provided
    if workout_update.exercises is not None:
        # Delete existing exercises
        existing_exercises = await exercise_repo.get_by_workout(workout.id)
        for exercise in existing_exercises:
            await exercise_repo.delete(exercise.id)
        
        # Create new exercises
        exercises_data = []
        for exercise in workout_update.exercises:
            exercise_data = exercise.dict()
            exercise_data["workout_id"] = updated_workout.id
            exercise_data["created_at"] = datetime.utcnow()
            exercise_data["updated_at"] = datetime.utcnow()
            
            db_exercise = await exercise_repo.create(exercise_data)
            exercises_data.append({
                "id": str(db_exercise.id),
                "name": db_exercise.name,
                "sets": db_exercise.sets,
                "reps": db_exercise.reps,
                "weight": float(db_exercise.weight),
                "notes": db_exercise.notes or ""
            })
    else:
        # Get existing exercises
        existing_exercises = await exercise_repo.get_by_workout(workout.id)
        exercises_data = []
        for exercise in existing_exercises:
            exercises_data.append({
                "id": str(exercise.id),
                "name": exercise.name,
                "sets": exercise.sets,
                "reps": exercise.reps,
                "weight": float(exercise.weight),
                "notes": exercise.notes or ""
            })
    
    # Get client name
    client = await client_repo.get_by_id(updated_workout.client_id, user_id=user_id)
    client_name = client.name if client else "Unknown Client"
    
    # Prepare response
    response_data = {
        "id": str(updated_workout.id),
        "client_id": str(updated_workout.client_id),
        "client_name": client_name,
        "date": updated_workout.date.isoformat() if isinstance(updated_workout.date, datetime) else updated_workout.date,
        "type": updated_workout.type,
        "duration": updated_workout.duration,
        "notes": updated_workout.notes or "",
        "exercises": exercises_data,
        "created_at": updated_workout.created_at.isoformat() if updated_workout.created_at else None,
        "updated_at": updated_workout.updated_at.isoformat() if updated_workout.updated_at else None
    }
    
    return StandardResponse.success(
        data=response_data,
        message="Workout updated successfully"
    )

# DELETE /workouts/{workout_id} - Delete a workout
@router.delete("/{workout_id}", response_model=Dict[str, Any])
async def delete_workout(
    workout_id: str = Path(..., description="The ID of the workout to delete"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a workout.
    
    - **workout_id**: The unique identifier of the workout to delete
    """
    workout_repo = AsyncWorkoutRepository(db)
    
    # Get the user_id from client_info for data isolation
    user_id = client_info.get("user_id")
    
    # Check if workout exists and belongs to this user
    workout = await workout_repo.get_by_id(uuid.UUID(workout_id), user_id=user_id)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    # Delete workout (associated exercises will be deleted via cascade)
    success = await workout_repo.delete(uuid.UUID(workout_id))
    
    if success:
        return StandardResponse.success(
            data={"id": workout_id},
            message="Workout deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting workout"
        ) 