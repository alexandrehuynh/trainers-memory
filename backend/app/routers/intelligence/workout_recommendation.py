"""
Workout Recommendation Module.

This module provides endpoints for generating personalized workout recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.dependencies.auth import get_current_user
from app.utils.auth_service import UserData
from app.utils.error_handlers import handle_exceptions, NotFoundError, BadRequestError
from app.db import get_async_db, AsyncClientRepository, AsyncWorkoutRepository
from app.utils.cache.openai_analysis import analyze_with_openai_cached

from .models import WorkoutRecommendationRequest, WorkoutRecommendationResponse

# Set up logger
logger = logging.getLogger(__name__)

# Create router - note no prefix, as this will be included by the parent router
router = APIRouter()


@router.post("/recommendations", response_model=WorkoutRecommendationResponse)
@handle_exceptions
async def generate_workout_recommendation(
    request: WorkoutRecommendationRequest,
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate a personalized workout recommendation.
    
    This endpoint creates tailored workout plans based on client history,
    goals, available equipment, and focus areas.
    
    Args:
        request: The workout recommendation request.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        WorkoutRecommendationResponse: The workout recommendation.
    """
    # Verify client exists
    client_repo = AsyncClientRepository(db)
    client = await client_repo.get_by_id(request.client_id)
    if not client:
        raise NotFoundError("Client", request.client_id)
    
    # Get previous workouts for the client (for context)
    workout_repo = AsyncWorkoutRepository(db)
    workouts = await workout_repo.get_by_client_id(request.client_id)
    
    # Prepare cache key
    cache_key = f"workout_recommendation_{request.client_id}_{request.goal}"
    if request.focus_areas:
        cache_key += f"_{','.join(request.focus_areas)}"
    if request.workout_duration:
        cache_key += f"_{request.workout_duration}min"
    
    # Format previous workout data for analysis context
    workout_history = []
    for workout in workouts:
        workout_exercises = []
        for exercise in workout.exercises:
            workout_exercises.append({
                "name": exercise.name,
                "sets": exercise.sets,
                "reps": exercise.reps,
                "weight": exercise.weight
            })
        
        workout_history.append({
            "date": workout.date,
            "type": workout.type,
            "exercises": workout_exercises
        })
    
    # Prepare prompt and data for LLM
    prompt = f"Generate a {request.goal} workout"
    if request.focus_areas:
        prompt += f" focusing on {', '.join(request.focus_areas)}"
    if request.workout_duration:
        prompt += f" with duration of {request.workout_duration} minutes"
    
    # Include equipment constraints if provided
    equipment_info = ""
    if request.available_equipment:
        equipment_info = f"Available equipment: {', '.join(request.available_equipment)}"
    
    # Prepare data for LLM
    analysis_data = {
        "client_info": {
            "id": request.client_id,
            "name": client.name if hasattr(client, "name") else "Client"
        },
        "request": {
            "goal": request.goal,
            "focus_areas": request.focus_areas,
            "available_equipment": request.available_equipment,
            "workout_duration": request.workout_duration
        },
        "workout_history": workout_history[:10]  # Limit to recent workouts
    }
    
    # Call LLM for analysis with caching
    analysis_result = await analyze_with_openai_cached(
        prompt=prompt,
        data=analysis_data,
        context=equipment_info,
        cache_key=cache_key,
        force_refresh=request.force_refresh
    )
    
    # Try to extract structured data from the response
    try:
        workout_plan = analysis_result.get("workout_plan", {})
        reasoning = analysis_result.get("reasoning", "")
        alternatives = analysis_result.get("alternatives", [])
    except (KeyError, AttributeError) as e:
        logger.error(f"Error parsing recommendation result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating workout recommendation"
        )
    
    # Create response
    response = WorkoutRecommendationResponse(
        client_id=request.client_id,
        timestamp=datetime.utcnow().isoformat(),
        cached=analysis_result.get("cached", False),
        goal=request.goal,
        workout_plan=workout_plan,
        reasoning=reasoning,
        alternatives=alternatives
    )
    
    return response


@router.get("/recommendations/{client_id}", response_model=WorkoutRecommendationResponse)
@handle_exceptions
async def get_workout_recommendation(
    client_id: str,
    goal: str = Query(..., description="Training goal (e.g. Strength, Hypertrophy)"),
    focus_areas: str = Query(None, description="Comma-separated list of body areas to focus on"),
    available_equipment: str = Query(None, description="Comma-separated list of available equipment"),
    workout_duration: int = Query(60, description="Target workout duration in minutes"),
    force_refresh: bool = Query(False, description="Force recalculation of recommendation"),
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a workout recommendation for a client.
    
    This is a GET alternative to the POST endpoint, useful for simple queries.
    
    Args:
        client_id: ID of the client to generate recommendation for.
        goal: Training goal for the recommendation.
        focus_areas: Optional comma-separated list of body areas to focus on.
        available_equipment: Optional comma-separated list of available equipment.
        workout_duration: Target workout duration in minutes.
        force_refresh: Whether to force refresh the recommendation.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        WorkoutRecommendationResponse: The workout recommendation.
    """
    # Parse comma-separated lists into proper arrays
    focus_areas_list = None
    if focus_areas:
        focus_areas_list = [area.strip() for area in focus_areas.split(",")]
    
    equipment_list = None
    if available_equipment:
        equipment_list = [item.strip() for item in available_equipment.split(",")]
    
    # Create request object
    request = WorkoutRecommendationRequest(
        client_id=client_id,
        goal=goal,
        focus_areas=focus_areas_list,
        available_equipment=equipment_list,
        workout_duration=workout_duration,
        force_refresh=force_refresh
    )
    
    # Reuse the POST endpoint logic
    return await generate_workout_recommendation(request, current_user, db) 