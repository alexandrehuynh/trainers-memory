from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.future import select

# Import API key dependency and standard response
from ..auth_utils import validate_api_key
from ..utils.response import StandardResponse
from ..db import AsyncWorkoutTemplateRepository, AsyncTemplateExerciseRepository, get_async_db
from ..db.models import WorkoutTemplate, TemplateExercise

# Define models
class TemplateExerciseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Bench Press")
    sets: int = Field(..., ge=1, le=100, example=3)
    reps: str = Field(None, max_length=50, example="8-12")
    rest_time: Optional[int] = Field(None, ge=0, le=600, example=60)
    notes: Optional[str] = Field(None, max_length=1000, example="Keep back flat on bench")

class TemplateExerciseCreate(TemplateExerciseBase):
    pass

class TemplateExerciseResponse(TemplateExerciseBase):
    id: str
    template_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class WorkoutTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Full Body Workout")
    description: Optional[str] = Field(None, max_length=1000, example="Complete full body workout for beginners")
    type: str = Field("strength", min_length=1, max_length=255, example="strength")
    duration: int = Field(60, ge=1, le=240, example=60)
    is_system: bool = Field(False, example=False)

class WorkoutTemplateCreate(WorkoutTemplateBase):
    pass

class WorkoutTemplateResponse(WorkoutTemplateBase):
    id: str
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    exercises: Optional[List[TemplateExerciseResponse]] = None

# Create router
router = APIRouter()

# GET /templates - List all templates
@router.get("/templates", response_model=Dict[str, Any])
async def get_templates(
    skip: int = Query(0, ge=0, description="Number of templates to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of templates to return"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a list of workout templates.
    
    - **skip**: Number of templates to skip (pagination)
    - **limit**: Maximum number of templates to return (pagination)
    """
    try:
        # Get the user_id from client_info for data isolation
        user_id = client_info.get("user_id")
        
        # Use a direct query instead of repository methods
        if user_id is not None:
            query = select(WorkoutTemplate).where(
                WorkoutTemplate.user_id == user_id
            )
        else:
            query = select(WorkoutTemplate)
            
        # Execute the query
        result = await db.execute(query.offset(skip).limit(limit))
        templates_list = result.scalars().all()
        
        # Convert database models to Pydantic models for serialization
        serialized_templates = []
        for template in templates_list:
            serialized_templates.append({
                "id": str(template.id),
                "name": template.name,
                "description": template.description or "",
                "type": template.type,
                "duration": template.duration,
                "is_system": template.is_system,
                "user_id": str(template.user_id) if template.user_id else None,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                "exercises": []  # Simplified to avoid nested async calls
            })
        
        return StandardResponse.success(
            data={"templates": serialized_templates, "total": len(serialized_templates), "skip": skip, "limit": limit},
            message="Templates retrieved successfully"
        )
    except Exception as e:
        print(f"Error in get_templates: {e}")
        return StandardResponse.error(
            message="Database error occurred",
            error=str(e),
            status_code=500
        )

# POST /templates - Create a new template
@router.post("/templates", response_model=Dict[str, Any])
async def create_template(
    template: WorkoutTemplateCreate,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new workout template."""
    try:
        # Get the user_id from client_info for data isolation
        user_id = client_info.get("user_id")
        
        # Create the new template object
        new_template = WorkoutTemplate(
            name=template.name,
            description=template.description,
            type=template.type,
            duration=template.duration,
            is_system=template.is_system,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add to session and commit
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        
        # Create the response with the appropriate data
        response_data = StandardResponse.success(
            data={
                "id": str(new_template.id),
                "name": new_template.name,
                "description": new_template.description,
                "type": new_template.type,
                "duration": new_template.duration,
                "is_system": new_template.is_system,
                "user_id": str(new_template.user_id) if new_template.user_id else None,
                "created_at": new_template.created_at.isoformat() if new_template.created_at else None,
                "exercises": []
            },
            message="Template created successfully"
        )
        
        # Return the response with the desired status code using JSONResponse
        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        # Rollback the transaction in case of an error
        await db.rollback()
        print(f"Error in create_template: {e}")
        return StandardResponse.error(
            message="Database error occurred",
            error=str(e),
            status_code=500
        )

# POST /templates/{template_id}/exercises - Add exercise to a template
@router.post("/templates/{template_id}/exercises", response_model=Dict[str, Any])
async def add_exercise_to_template(
    template_id: str = Path(..., title="The ID of the template to add an exercise to"),
    exercise: TemplateExerciseCreate = None,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """Add a new exercise to an existing workout template."""
    try:
        # Validate template_id format
        try:
            template_uuid = uuid.UUID(template_id)
        except ValueError:
            return StandardResponse.error(
                message="Invalid template ID format",
                error="The provided template ID is not a valid UUID",
                status_code=400
            )
        
        # Check if template exists and belongs to the current user
        user_id = client_info.get("user_id")
        
        # Query to find the template
        query = select(WorkoutTemplate).where(
            WorkoutTemplate.id == template_uuid
        )
        
        if user_id is not None:
            # Add user isolation
            query = query.where(
                (WorkoutTemplate.is_system == True) | (WorkoutTemplate.user_id == user_id)
            )
        
        # Execute the query
        result = await db.execute(query)
        template = result.scalars().first()
        
        if not template:
            return StandardResponse.error(
                message="Template not found",
                error="The specified template does not exist or you don't have access to it",
                status_code=404
            )
        
        # Create new exercise for the template
        new_exercise = TemplateExercise(
            template_id=template_uuid,
            name=exercise.name,
            sets=exercise.sets,
            reps=exercise.reps,
            rest_time=exercise.rest_time,
            notes=exercise.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add to session and commit
        db.add(new_exercise)
        await db.commit()
        await db.refresh(new_exercise)
        
        # Return success response
        return StandardResponse.success(
            data={
                "id": str(new_exercise.id),
                "template_id": str(new_exercise.template_id),
                "name": new_exercise.name,
                "sets": new_exercise.sets,
                "reps": new_exercise.reps,
                "rest_time": new_exercise.rest_time,
                "notes": new_exercise.notes,
                "created_at": new_exercise.created_at.isoformat() if new_exercise.created_at else None,
                "updated_at": new_exercise.updated_at.isoformat() if new_exercise.updated_at else None
            },
            message="Exercise added to template successfully"
        )
    except Exception as e:
        # Rollback the transaction in case of an error
        await db.rollback()
        print(f"Error in add_exercise_to_template: {e}")
        return StandardResponse.error(
            message="Database error occurred",
            error=str(e),
            status_code=500
        )

# GET /templates/{template_id} - Get a specific template with exercises
@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str = Path(..., title="The ID of the template to retrieve"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a specific workout template with its exercises.
    """
    try:
        # Validate template_id format
        try:
            template_uuid = uuid.UUID(template_id)
        except ValueError:
            return StandardResponse.error(
                message="Invalid template ID format",
                error="The provided template ID is not a valid UUID",
                status_code=400
            )
        
        # Get the user_id from client_info for data isolation
        user_id = client_info.get("user_id")
        
        # Query to find the template
        query = select(WorkoutTemplate).where(
            WorkoutTemplate.id == template_uuid
        )
        
        if user_id is not None:
            # Add user isolation
            query = query.where(
                (WorkoutTemplate.is_system == True) | (WorkoutTemplate.user_id == user_id)
            )
        
        # Execute the query
        result = await db.execute(query)
        template = result.scalars().first()
        
        if not template:
            return StandardResponse.error(
                message="Template not found",
                error="The specified template does not exist or you don't have access to it",
                status_code=404
            )
        
        # Query to find exercises for the template
        exercises_query = select(TemplateExercise).where(
            TemplateExercise.template_id == template_uuid
        )
        exercises_result = await db.execute(exercises_query)
        exercises_list = exercises_result.scalars().all()
        
        # Serialize exercises
        serialized_exercises = []
        for exercise in exercises_list:
            serialized_exercises.append({
                "id": str(exercise.id),
                "template_id": str(exercise.template_id),
                "name": exercise.name,
                "sets": exercise.sets,
                "reps": exercise.reps,
                "rest_time": exercise.rest_time,
                "notes": exercise.notes,
                "created_at": exercise.created_at.isoformat() if exercise.created_at else None,
                "updated_at": exercise.updated_at.isoformat() if exercise.updated_at else None
            })
        
        # Return the template with its exercises
        return StandardResponse.success(
            data={
                "id": str(template.id),
                "name": template.name,
                "description": template.description or "",
                "type": template.type,
                "duration": template.duration,
                "is_system": template.is_system,
                "user_id": str(template.user_id) if template.user_id else None,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                "exercises": serialized_exercises
            },
            message="Template retrieved successfully"
        )
    except Exception as e:
        print(f"Error in get_template: {e}")
        return StandardResponse.error(
            message="Database error occurred",
            error=str(e),
            status_code=500
        ) 