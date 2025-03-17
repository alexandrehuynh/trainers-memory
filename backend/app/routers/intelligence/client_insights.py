"""
Client Insights Module.

This module provides endpoints for generating insights about client progress and behavior.
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

from .models import ClientInsightRequest, ClientInsightResponse

# Set up logger
logger = logging.getLogger(__name__)

# Create router - note no prefix, as this will be included by the parent router
router = APIRouter()


@router.post("/insights", response_model=ClientInsightResponse)
@handle_exceptions
async def generate_client_insights(
    request: ClientInsightRequest,
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate insights for a client.
    
    This endpoint analyzes client data to provide behavioral insights,
    adherence patterns, and actionable recommendations.
    
    Args:
        request: The client insight request.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        ClientInsightResponse: The client insights.
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
    cache_key = f"client_insight_{request.client_id}_{request.insight_type}_{request.time_period}"
    
    # Format data for analysis
    workout_data = []
    for workout in workouts:
        workout_exercises = []
        for exercise in workout.exercises:
            workout_exercises.append({
                "name": exercise.name,
                "sets": exercise.sets,
                "reps": exercise.reps,
                "weight": exercise.weight
            })
        
        workout_data.append({
            "date": workout.date,
            "type": workout.type,
            "duration": workout.duration,
            "exercises": workout_exercises,
            "notes": workout.notes
        })
    
    # Prepare client info
    client_info = {
        "id": str(client.id),
        "name": client.name if hasattr(client, "name") else "Client",
        "since": client.created_at.isoformat() if hasattr(client, "created_at") else None
    }
    
    # Prepare prompt
    prompt = f"Generate {request.insight_type} insights for client over the past {request.time_period}"
    
    # Prepare data for LLM
    analysis_data = {
        "client_info": client_info,
        "workouts": workout_data,
        "insight_type": request.insight_type,
        "time_period": request.time_period
    }
    
    # Call LLM for analysis with caching
    analysis_result = await analyze_with_openai_cached(
        prompt=prompt,
        data=analysis_data,
        cache_key=cache_key,
        force_refresh=request.force_refresh
    )
    
    # Try to extract structured data from the response
    try:
        insights = analysis_result.get("insights", [])
        summary = analysis_result.get("summary", "No summary available")
        action_items = analysis_result.get("action_items", [])
    except (KeyError, AttributeError) as e:
        logger.error(f"Error parsing insight result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating client insights"
        )
    
    # Create response
    response = ClientInsightResponse(
        client_id=request.client_id,
        timestamp=datetime.utcnow().isoformat(),
        cached=analysis_result.get("cached", False),
        insight_type=request.insight_type,
        insights=insights,
        summary=summary,
        action_items=action_items
    )
    
    return response


@router.get("/insights/{client_id}", response_model=ClientInsightResponse)
@handle_exceptions
async def get_client_insights(
    client_id: str,
    insight_type: str = Query(..., description="Type of insight to generate (e.g., Adherence, Progress, Pattern)"),
    time_period: str = Query("3 months", description="Time period to analyze"),
    force_refresh: bool = Query(False, description="Force recalculation of insights"),
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get insights for a client.
    
    This is a GET alternative to the POST endpoint, useful for simple queries.
    
    Args:
        client_id: ID of the client to analyze.
        insight_type: Type of insight to generate.
        time_period: Time period to analyze.
        force_refresh: Whether to force refresh the insights.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        ClientInsightResponse: The client insights.
    """
    # Create request object
    request = ClientInsightRequest(
        client_id=client_id,
        insight_type=insight_type,
        time_period=time_period,
        force_refresh=force_refresh
    )
    
    # Reuse the POST endpoint logic
    return await generate_client_insights(request, current_user, db) 