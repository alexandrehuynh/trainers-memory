"""
Injury Risk Analysis Module.

This module provides endpoints for analyzing client injury risks.
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

from .models import InjuryRiskRequest, InjuryRiskResponse

# Set up logger
logger = logging.getLogger(__name__)

# Create router - note no prefix, as this will be included by the parent router
router = APIRouter()


@router.post("/injury-risk", response_model=InjuryRiskResponse)
@handle_exceptions
async def analyze_injury_risk(
    request: InjuryRiskRequest,
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze injury risks for a client.
    
    This endpoint provides a risk assessment based on workout patterns,
    identifying potential issues and preventative measures.
    
    Args:
        request: The injury risk analysis request.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        InjuryRiskResponse: The injury risk analysis.
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
    cache_key = f"injury_risk_{request.client_id}"
    if request.focus_area:
        cache_key += f"_{request.focus_area}"
    
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
    if request.focus_area:
        prompt = f"Analyze injury risk for {request.focus_area} based on workout patterns."
    else:
        prompt = "Analyze overall injury risk based on workout patterns."
    
    # Call LLM for analysis with caching
    analysis_result = await analyze_with_openai_cached(
        prompt=prompt,
        data=workout_data,
        cache_key=cache_key,
        force_refresh=request.force_refresh
    )
    
    # Try to extract structured data from the response
    try:
        overall_risk = analysis_result.get("overall_risk", "Unknown")
        potential_issues = analysis_result.get("potential_issues", [])
        protective_factors = analysis_result.get("protective_factors", [])
        recommendations = analysis_result.get("recommendations", [])
    except (KeyError, AttributeError) as e:
        logger.error(f"Error parsing analysis result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing analysis results"
        )
    
    # Create response
    response = InjuryRiskResponse(
        client_id=request.client_id,
        timestamp=datetime.utcnow().isoformat(),
        cached=analysis_result.get("cached", False),
        overall_risk=overall_risk,
        potential_issues=potential_issues,
        protective_factors=protective_factors,
        recommendations=recommendations
    )
    
    return response


@router.get("/injury-risk/{client_id}", response_model=InjuryRiskResponse)
@handle_exceptions
async def get_injury_risk(
    client_id: str,
    focus_area: str = Query(None, description="Body area to focus on"),
    force_refresh: bool = Query(False, description="Force recalculation of analysis"),
    current_user: UserData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get injury risk analysis for a client.
    
    This is a GET alternative to the POST endpoint, useful for simple queries.
    
    Args:
        client_id: ID of the client to analyze.
        focus_area: Optional specific body area to focus on.
        force_refresh: Whether to force refresh the analysis.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        InjuryRiskResponse: The injury risk analysis.
    """
    # Create request object
    request = InjuryRiskRequest(
        client_id=client_id,
        focus_area=focus_area,
        force_refresh=force_refresh
    )
    
    # Reuse the POST endpoint logic
    return await analyze_injury_risk(request, current_user, db) 