"""
Progress Analysis Module.

This module provides endpoints for analyzing client exercise progression.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.dependencies.auth import get_current_user
from app.utils.auth_service import UserData
from app.utils.error_handlers import handle_exceptions, NotFoundError, BadRequestError
from app.db import get_async_db, AsyncClientRepository, AsyncWorkoutRepository
from app.utils.cache.openai_analysis import analyze_with_openai_cached

from .models import ExerciseProgressionRequest, ExerciseProgressionResponse

# Set up logger
logger = logging.getLogger(__name__)

# Create router - note no prefix, as this will be included by the parent router
router = APIRouter()


@router.post("/progression", response_model=ExerciseProgressionResponse)
@handle_exceptions
async def analyze_progression(
    request: ExerciseProgressionRequest,
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze exercise progression for a client.
    
    This endpoint provides detailed analysis of a client's progression on a specific exercise,
    or overall progression across all exercises if no specific exercise is provided.
    
    Args:
        request: The progression analysis request.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        ExerciseProgressionResponse: The progression analysis.
    """
    # Verify client exists
    client_repo = AsyncClientRepository(db)
    client = await client_repo.get_by_id(request.client_id)
    if not client:
        raise NotFoundError("Client", request.client_id)
    
    # Get workouts for the client
    workout_repo = AsyncWorkoutRepository(db)
    workouts = await workout_repo.get_by_client_id(request.client_id)
    
    if not workouts:
        raise BadRequestError(f"No workout data found for client {request.client_id}")
    
    # Prepare cache key
    cache_key = f"progression_{request.client_id}"
    if request.exercise:
        cache_key += f"_{request.exercise}"
    cache_key += f"_{request.time_period}"
    
    # Format data for analysis
    workout_data = []
    for workout in workouts:
        for exercise in workout.exercises:
            workout_data.append({
                "date": workout.date,
                "exercise": exercise.name,
                "sets": exercise.sets,
                "reps": exercise.reps,
                "weight": exercise.weight,
                "notes": exercise.notes
            })
    
    # Prepare prompt
    if request.exercise:
        prompt = f"Analyze progression for {request.exercise} over the past {request.time_period}."
    else:
        prompt = f"Analyze overall exercise progression over the past {request.time_period}."
    
    # Call LLM for analysis with caching
    analysis_result = await analyze_with_openai_cached(
        prompt=prompt,
        data=workout_data,
        cache_key=cache_key,
        force_refresh=request.force_refresh
    )
    
    # Try to extract structured data from the response
    try:
        if request.exercise:
            progression_rate = analysis_result.get("progression_rate", "Not available")
            plateaus = analysis_result.get("plateaus", [])
            recommendations = analysis_result.get("recommendations", [])
            analysis = analysis_result.get("analysis", "No analysis available")
            chart_data = analysis_result.get("chart_data")
        else:
            progression_rate = None
            plateaus = analysis_result.get("plateaus", [])
            recommendations = analysis_result.get("recommendations", [])
            analysis = analysis_result.get("overall_analysis", "No analysis available")
            chart_data = analysis_result.get("chart_data")
    except (KeyError, AttributeError) as e:
        logger.error(f"Error parsing analysis result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing analysis results"
        )
    
    # Create response
    response = ExerciseProgressionResponse(
        client_id=request.client_id,
        timestamp=datetime.utcnow().isoformat(),
        cached=analysis_result.get("cached", False),
        exercise=request.exercise,
        analysis=analysis,
        progression_rate=progression_rate,
        plateaus=plateaus,
        recommendations=recommendations,
        chart_data=chart_data
    )
    
    return response


@router.get("/progression/{client_id}", response_model=ExerciseProgressionResponse)
@handle_exceptions
async def get_progression(
    client_id: str,
    exercise: str = Query(None, description="Specific exercise to analyze"),
    time_period: str = Query("6 months", description="Time period to analyze"),
    force_refresh: bool = Query(False, description="Force recalculation of analysis"),
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get exercise progression analysis for a client.
    
    This is a GET alternative to the POST endpoint, useful for simple queries.
    
    Args:
        client_id: ID of the client to analyze.
        exercise: Optional specific exercise to analyze.
        time_period: Time period to analyze.
        force_refresh: Whether to force refresh the analysis.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        ExerciseProgressionResponse: The progression analysis.
    """
    # Create request object
    request = ExerciseProgressionRequest(
        client_id=client_id,
        exercise=exercise,
        time_period=time_period,
        force_refresh=force_refresh
    )
    
    # Reuse the POST endpoint logic
    return await analyze_progression(request, current_user, db) 