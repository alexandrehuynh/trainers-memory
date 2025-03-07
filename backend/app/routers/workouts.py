from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, UploadFile, File
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Import API key dependency and standard response
from ..main import get_api_key
from ..utils.response import StandardResponse

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
    tags=["workouts"],
    responses={404: {"description": "Not found"}},
)

# In-memory data store (replace with database in production)
workouts_db = {}
exercises_db = {}

# Helper function to get client name
def get_client_name(client_id: str) -> str:
    # In a real implementation, you would fetch this from a database
    # This is just a mock implementation for demo purposes
    from .clients import clients_db
    if client_id in clients_db:
        return clients_db[client_id]["name"]
    return "Unknown Client"

# Helper function to validate date string
def is_valid_date(date_string: str) -> bool:
    try:
        # Check if the date string is in the correct format
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# GET /workouts - List all workouts
@router.get("/workouts", response_model=Dict[str, Any])
async def get_workouts(
    skip: int = Query(0, ge=0, description="Number of workouts to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of workouts to return"),
    client_id: Optional[str] = Query(None, description="Filter workouts by client ID"),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Retrieve a list of workouts.
    
    - **skip**: Number of workouts to skip (pagination)
    - **limit**: Maximum number of workouts to return (pagination)
    - **client_id**: Optional filter to show only workouts for a specific client
    """
    # Filter workouts if client_id is provided
    if client_id:
        filtered_workouts = [w for w in workouts_db.values() if w["client_id"] == client_id]
    else:
        filtered_workouts = list(workouts_db.values())
    
    # Sort by date (newest first)
    sorted_workouts = sorted(filtered_workouts, key=lambda x: x["date"], reverse=True)
    
    # Paginate
    paginated_workouts = sorted_workouts[skip:skip+limit]
    
    return StandardResponse.success(
        data={
            "workouts": paginated_workouts,
            "total": len(filtered_workouts),
            "skip": skip,
            "limit": limit
        },
        message="Workouts retrieved successfully"
    )

# GET /workouts/{workout_id} - Get a specific workout
@router.get("/workouts/{workout_id}", response_model=Dict[str, Any])
async def get_workout(
    workout_id: str = Path(..., description="The ID of the workout to retrieve"),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Retrieve a specific workout by ID.
    
    - **workout_id**: The unique identifier of the workout
    """
    if workout_id not in workouts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    return StandardResponse.success(
        data=workouts_db[workout_id],
        message="Workout retrieved successfully"
    )

# POST /workouts - Create a new workout
@router.post("/workouts", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_workout(
    workout: WorkoutCreate,
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Create a new workout.
    
    - **workout**: Workout data to create
    """
    # Validate date format
    if not is_valid_date(workout.date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD format."
        )
    
    # Generate a unique ID
    workout_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    # Create exercises
    exercises = []
    for exercise_data in workout.exercises:
        exercise_id = str(uuid.uuid4())
        exercise = Exercise(
            id=exercise_id,
            **exercise_data.model_dump()
        )
        exercises.append(exercise.model_dump())
        exercises_db[exercise_id] = exercise.model_dump()
    
    # Get client name
    client_name = get_client_name(workout.client_id)
    
    # Create the workout record
    new_workout = Workout(
        id=workout_id,
        client_name=client_name,
        created_at=timestamp,
        exercises=exercises,
        **workout.model_dump(exclude={"exercises"})
    )
    
    # Store in our mock database
    workouts_db[workout_id] = new_workout.model_dump()
    
    return StandardResponse.success(
        data=new_workout.model_dump(),
        message="Workout created successfully"
    )

# PUT /workouts/{workout_id} - Update a workout
@router.put("/workouts/{workout_id}", response_model=Dict[str, Any])
async def update_workout(
    workout_update: WorkoutUpdate,
    workout_id: str = Path(..., description="The ID of the workout to update"),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Update an existing workout.
    
    - **workout_id**: The unique identifier of the workout to update
    - **workout_update**: Workout data to update
    """
    if workout_id not in workouts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    # Validate date format if provided
    if workout_update.date and not is_valid_date(workout_update.date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD format."
        )
    
    # Get existing workout
    existing_workout = workouts_db[workout_id]
    
    # Update fields that are provided
    update_data = workout_update.model_dump(exclude_unset=True)
    
    # Handle exercises separately if provided
    if "exercises" in update_data:
        exercises = update_data.pop("exercises")
        updated_exercises = []
        
        for exercise_data in exercises:
            exercise_id = str(uuid.uuid4())
            exercise = Exercise(
                id=exercise_id,
                **exercise_data
            )
            updated_exercises.append(exercise.model_dump())
            exercises_db[exercise_id] = exercise.model_dump()
        
        existing_workout["exercises"] = updated_exercises
    
    # Update client name if client_id is changed
    if "client_id" in update_data:
        existing_workout["client_name"] = get_client_name(update_data["client_id"])
    
    # Update other fields
    for field, value in update_data.items():
        existing_workout[field] = value
    
    # Save the updated workout
    workouts_db[workout_id] = existing_workout
    
    return StandardResponse.success(
        data=existing_workout,
        message="Workout updated successfully"
    )

# DELETE /workouts/{workout_id} - Delete a workout
@router.delete("/workouts/{workout_id}", response_model=Dict[str, Any])
async def delete_workout(
    workout_id: str = Path(..., description="The ID of the workout to delete"),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Delete a workout.
    
    - **workout_id**: The unique identifier of the workout to delete
    """
    if workout_id not in workouts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    # Get the workout to be deleted
    workout = workouts_db[workout_id]
    
    # Remove the workout
    deleted_workout = workouts_db.pop(workout_id)
    
    # Remove associated exercises
    for exercise in workout["exercises"]:
        if exercise["id"] in exercises_db:
            exercises_db.pop(exercise["id"])
    
    return StandardResponse.success(
        data={"id": workout_id},
        message="Workout deleted successfully"
    ) 