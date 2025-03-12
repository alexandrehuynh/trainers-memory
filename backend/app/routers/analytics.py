from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth_utils import validate_api_key
from ..utils.response import StandardResponse
from ..db import get_async_db, AsyncClientRepository, AsyncWorkoutRepository

# Create router
router = APIRouter()

@router.get("/business-intelligence", response_model=Dict[str, Any])
async def get_business_intelligence(
    time_period: str = Query("30d", description="Time period for analysis (7d, 30d, 90d, all)"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get business intelligence metrics and insights.
    
    Returns key metrics about your training business, including:
    - Client acquisition and retention
    - Workout frequency and engagement
    - Popular exercises and training types
    - Revenue metrics (if available)
    """
    # Convert time period to days
    days = None
    if time_period != "all":
        if time_period == "7d":
            days = 7
        elif time_period == "30d":
            days = 30
        elif time_period == "90d":
            days = 90
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time_period. Must be one of: 7d, 30d, 90d, all"
            )
    
    try:
        # Get repositories
        client_repo = AsyncClientRepository(db)
        workout_repo = AsyncWorkoutRepository(db)
        
        # Calculate date threshold
        date_threshold = None
        if days:
            date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Get clients
        clients = await client_repo.get_all()
        
        # Count new clients in period
        new_clients_count = 0
        if date_threshold:
            for client in clients:
                if client.created_at and client.created_at >= date_threshold:
                    new_clients_count += 1
        
        # Get workouts in period
        workouts = []
        if date_threshold:
            # This would need to be implemented in the repository
            workouts = await workout_repo.get_all_since_date(date_threshold)
        else:
            workouts = await workout_repo.get_all()
        
        # Calculate metrics
        total_clients = len(clients)
        total_workouts = len(workouts)
        avg_workouts_per_client = total_workouts / total_clients if total_clients > 0 else 0
        
        # Return the analytics data
        return StandardResponse.success(
            data={
                "client_metrics": {
                    "total_clients": total_clients,
                    "new_clients": new_clients_count,
                    "active_clients": total_clients  # This would need more logic to determine active status
                },
                "workout_metrics": {
                    "total_workouts": total_workouts,
                    "avg_workouts_per_client": round(avg_workouts_per_client, 2),
                    "avg_duration_minutes": 45  # Placeholder - would calculate from actual data
                },
                "popular_exercises": [
                    {"name": "Bench Press", "count": 45},
                    {"name": "Squats", "count": 40},
                    {"name": "Deadlifts", "count": 35}
                ],  # Placeholder - would calculate from actual data
                "revenue_metrics": {
                    "estimated_monthly": total_clients * 200,  # Placeholder calculation
                    "revenue_per_client": 200  # Placeholder
                }
            },
            message="Business intelligence metrics retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving business intelligence: {str(e)}"
        )

@router.get("/client-retention", response_model=Dict[str, Any])
async def get_client_retention_analytics(
    time_period: str = Query("90d", description="Time period for analysis (30d, 90d, 180d, 365d)"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get client retention analytics.
    
    Returns detailed metrics about client retention, including:
    - Overall retention rate
    - Retention by client segment
    - Churn prediction
    - Recommendations for improving retention
    """
    # Convert time period to days
    days = None
    if time_period == "30d":
        days = 30
    elif time_period == "90d":
        days = 90
    elif time_period == "180d":
        days = 180
    elif time_period == "365d":
        days = 365
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time_period. Must be one of: 30d, 90d, 180d, 365d"
        )
    
    try:
        # Calculate date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # This would query actual retention data in a real application
        # For now, return placeholder data
        return StandardResponse.success(
            data={
                "overall_retention": {
                    "rate": 0.85,  # 85% retention rate
                    "compared_to_previous": 0.05  # 5% improvement
                },
                "retention_by_segment": [
                    {"segment": "New clients (< 3 months)", "rate": 0.75},
                    {"segment": "Regular clients (3-12 months)", "rate": 0.85},
                    {"segment": "Long-term clients (> 12 months)", "rate": 0.95}
                ],
                "churn_prediction": {
                    "at_risk_clients": 3,
                    "predicted_churn_rate": 0.15
                },
                "recommendations": [
                    "Increase session frequency for new clients",
                    "Follow up with clients who miss scheduled sessions",
                    "Implement a referral program to increase client engagement"
                ]
            },
            message="Client retention analytics retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving client retention analytics: {str(e)}"
        ) 