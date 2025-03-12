from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta
import random

# Import auth and DB dependencies
from ..auth_utils import validate_api_key  # Changed to use validate_api_key consistently
from ..utils.response import StandardResponse

router = APIRouter()

@router.get("/client-progress", response_model=Dict[str, Any])
async def get_client_progress(
    client_id: uuid.UUID = Query(..., description="Client ID to get progress for"),
    time_period: str = Query("30d", description="Time period for progress (7d, 30d, 90d, all)"),
    metrics: Optional[str] = Query(None, description="Comma-separated list of metrics to include"),
    client_info: Dict[str, Any] = Depends(validate_api_key)  # Updated to use validate_api_key
):
    """
    Get client progress metrics and insights over a specified time period.
    
    Returns key progress metrics such as:
    - Workout adherence and consistency
    - Strength progress for key lifts
    - Volume progression
    - Goal achievement metrics
    
    The time_period parameter controls how far back to analyze:
    - 7d: Last 7 days
    - 30d: Last 30 days (default)
    - 90d: Last 90 days
    - all: All available data
    
    The metrics parameter can be used to request specific metrics:
    - adherence: Workout adherence and consistency
    - strength: Strength progress for key lifts
    - volume: Training volume progression
    - goals: Goal achievement metrics
    - all: All metrics (default)
    """
    try:
        # Validate time period
        valid_periods = ["7d", "30d", "90d", "all"]
        if time_period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Invalid time_period. Must be one of: {', '.join(valid_periods)}"
            )
        
        # Process metrics parameter
        all_metrics = ["adherence", "strength", "volume", "goals"]
        if not metrics or metrics.lower() == "all":
            requested_metrics = all_metrics
        else:
            requested_metrics = [m.strip() for m in metrics.lower().split(",")]
            invalid_metrics = [m for m in requested_metrics if m not in all_metrics]
            if invalid_metrics:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid metrics: {', '.join(invalid_metrics)}. Valid options are: {', '.join(all_metrics)}"
                )
        
        # This would connect to a more sophisticated progress analysis service
        # For now, return placeholder progress data
        now = datetime.now()
        
        # Convert time period to actual date
        if time_period == "7d":
            start_date = now - timedelta(days=7)
            data_points = 7
        elif time_period == "30d":
            start_date = now - timedelta(days=30)
            data_points = 4  # Weekly data points
        elif time_period == "90d":
            start_date = now - timedelta(days=90)
            data_points = 12  # Weekly data points
        else:  # all
            start_date = now - timedelta(days=180)  # For demo purposes, use 6 months
            data_points = 24  # Biweekly data points
        
        progress_data = {}
        
        # Adherence metrics
        if "adherence" in requested_metrics:
            adherence_trend = []
            planned_workouts_per_week = 4
            
            for i in range(data_points):
                if time_period == "7d":
                    # Daily data for 7d
                    point_date = start_date + timedelta(days=i)
                    completed = random.randint(0, 1)  # 0 or 1 workout per day
                    planned = 1 if point_date.weekday() < 5 else 0  # Weekday vs weekend
                else:
                    # Weekly data for longer periods
                    point_date = start_date + timedelta(weeks=i)
                    completed = random.randint(2, planned_workouts_per_week)
                    planned = planned_workouts_per_week
                
                adherence_rate = (completed / planned * 100) if planned > 0 else 100
                
                adherence_trend.append({
                    "date": point_date.strftime("%Y-%m-%d"),
                    "completed_workouts": completed,
                    "planned_workouts": planned,
                    "adherence_rate": round(adherence_rate, 1)
                })
            
            progress_data["adherence"] = {
                "overall_adherence_rate": round(sum(p["adherence_rate"] for p in adherence_trend) / len(adherence_trend), 1),
                "trend": adherence_trend,
                "insights": [
                    "Monday workouts have the highest completion rate",
                    "Friday workouts are most frequently missed",
                    "Adherence improved by 12% in the last 2 weeks"
                ]
            }
        
        # Strength progress
        if "strength" in requested_metrics:
            # Sample key lifts
            key_lifts = ["Squat", "Bench Press", "Deadlift", "Shoulder Press"]
            strength_data = {}
            
            for lift in key_lifts:
                # Generate progressive strength data with some variation
                base_weight = random.randint(60, 120)  # Base weight in kg or lbs
                progression_factor = random.uniform(1.01, 1.03)  # 1-3% improvement
                
                lift_data = []
                current_weight = base_weight
                
                for i in range(data_points):
                    # Add some variation to the progression
                    if random.random() < 0.2:  # 20% chance of a setback
                        current_weight = current_weight * 0.98  # 2% decrease
                    else:
                        current_weight = current_weight * progression_factor
                    
                    if time_period == "7d":
                        point_date = start_date + timedelta(days=i)
                    else:
                        point_date = start_date + timedelta(weeks=i)
                    
                    lift_data.append({
                        "date": point_date.strftime("%Y-%m-%d"),
                        "weight": round(current_weight, 1),
                        "reps": random.randint(5, 8),
                        "estimated_1rm": round(current_weight * (1 + (0.033 * random.randint(5, 8))), 1)
                    })
                
                strength_data[lift] = lift_data
            
            progress_data["strength"] = {
                "key_lifts": strength_data,
                "overall_strength_change": f"+{round(random.uniform(5, 15), 1)}%",
                "strongest_lift": "Deadlift",
                "needs_focus": "Shoulder Press"
            }
        
        # Volume progression
        if "volume" in requested_metrics:
            volume_trend = []
            base_volume = random.randint(8000, 12000)  # Base weekly volume in kg
            
            for i in range(data_points):
                if time_period == "7d":
                    point_date = start_date + timedelta(days=i)
                    volume = base_volume / 7 * (1 + 0.01 * i)  # Daily volume with slight progression
                else:
                    point_date = start_date + timedelta(weeks=i)
                    volume = base_volume * (1 + 0.02 * i)  # Weekly volume with 2% progression per week
                
                # Add some random variation
                volume = volume * random.uniform(0.9, 1.1)
                
                volume_trend.append({
                    "date": point_date.strftime("%Y-%m-%d"),
                    "total_volume": round(volume),
                    "primary_muscle_groups": {
                        "chest": round(volume * random.uniform(0.2, 0.3)),
                        "back": round(volume * random.uniform(0.2, 0.3)),
                        "legs": round(volume * random.uniform(0.3, 0.4)),
                        "shoulders": round(volume * random.uniform(0.1, 0.15)),
                        "arms": round(volume * random.uniform(0.05, 0.1))
                    }
                })
            
            progress_data["volume"] = {
                "volume_trend": volume_trend,
                "overall_volume_change": f"+{round(random.uniform(8, 20), 1)}%",
                "muscle_group_balance": {
                    "balanced": ["chest", "back"],
                    "increasing": ["legs"],
                    "decreasing": ["shoulders"],
                    "recommendations": "Consider increasing shoulder volume to maintain balance"
                }
            }
        
        # Goal achievement
        if "goals" in requested_metrics:
            goals = [
                {
                    "name": "Bench Press 100kg",
                    "type": "strength",
                    "target": 100,
                    "current": 92,
                    "unit": "kg",
                    "progress": 92,
                    "projected_completion": (now + timedelta(days=random.randint(14, 28))).strftime("%Y-%m-%d")
                },
                {
                    "name": "Complete 16 workouts per month",
                    "type": "consistency",
                    "target": 16,
                    "current": 12,
                    "unit": "workouts",
                    "progress": 75,
                    "projected_completion": (now + timedelta(days=random.randint(7, 14))).strftime("%Y-%m-%d")
                },
                {
                    "name": "Deadlift body weight for 5 reps",
                    "type": "strength",
                    "target": 5,
                    "current": 3,
                    "unit": "reps",
                    "progress": 60,
                    "projected_completion": (now + timedelta(days=random.randint(21, 35))).strftime("%Y-%m-%d")
                }
            ]
            
            progress_data["goals"] = {
                "active_goals": goals,
                "overall_goal_progress": f"{round(sum(g['progress'] for g in goals) / len(goals), 1)}%",
                "completed_goals": [
                    {
                        "name": "Squat 1.5x body weight",
                        "completed_date": (now - timedelta(days=random.randint(10, 30))).strftime("%Y-%m-%d")
                    }
                ],
                "recommended_new_goals": [
                    "Increase shoulder press by 10%",
                    "Achieve first pull-up",
                    "Complete 4 workouts per week for 4 consecutive weeks"
                ]
            }
        
        return StandardResponse.success(
            data={
                "client_id": str(client_id),
                "time_period": time_period,
                "analysis_date": now.strftime("%Y-%m-%d"),
                "progress_metrics": progress_data,
                "overall_assessment": "Strong progress overall with consistent improvement in key lifts",
                "recommendations": [
                    "Focus on improving overhead pressing strength",
                    "Consider adding one more workout per week to accelerate progress",
                    "Increase training volume gradually over the next month"
                ]
            },
            message="Client progress data retrieved successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving client progress: {str(e)}"
        ) 