"""
Intelligence module data models.

This module contains Pydantic models for the intelligence API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import date


class AnalysisRequest(BaseModel):
    """Base model for intelligence analysis requests."""
    client_id: str = Field(..., description="ID of the client to analyze")
    force_refresh: bool = Field(False, description="Force recalculation of analysis")


class ClientHistoryQueryRequest(AnalysisRequest):
    """Model for client history analysis request."""
    query: str = Field(..., min_length=3, 
                     description="Natural language query about client history",
                     example="Show me their shoulder progress over the past 3 months")


class ExerciseProgressionRequest(AnalysisRequest):
    """Model for exercise progression analysis request."""
    exercise: Optional[str] = Field(None, 
                                  description="Specific exercise to analyze, or None for overall analysis",
                                  example="Bench Press")
    time_period: Optional[str] = Field("6 months", 
                                     description="Time period to analyze",
                                     example="3 months")


class InjuryRiskRequest(AnalysisRequest):
    """Model for injury risk assessment request."""
    focus_area: Optional[str] = Field(None, 
                                   description="Body area to focus on, or None for overall assessment",
                                   example="Lower Back")


class WorkoutRecommendationRequest(AnalysisRequest):
    """Model for workout recommendation request."""
    goal: str = Field(..., 
                   description="Training goal for the recommendation",
                   example="Hypertrophy")
    available_equipment: Optional[List[str]] = Field(None, 
                                                  description="List of available equipment",
                                                  example=["Barbell", "Dumbbells", "Bench"])
    workout_duration: Optional[int] = Field(60, 
                                         description="Target workout duration in minutes",
                                         example=45)
    focus_areas: Optional[List[str]] = Field(None, 
                                          description="Body areas to focus on",
                                          example=["Chest", "Shoulders"])


class ClientInsightRequest(AnalysisRequest):
    """Model for client insight request."""
    insight_type: str = Field(..., 
                           description="Type of insight to generate",
                           example="Adherence")
    time_period: Optional[str] = Field("3 months", 
                                     description="Time period to analyze",
                                     example="1 month")


class AnalysisResponse(BaseModel):
    """Base model for intelligence analysis responses."""
    client_id: str
    timestamp: str = Field(..., description="Timestamp of analysis generation")
    cached: bool = Field(False, description="Whether this response was loaded from cache")


class ClientHistoryResponse(AnalysisResponse):
    """Model for client history analysis response."""
    query: str
    analysis: str
    data_points: List[Dict[str, Any]]
    recommendations: List[str]


class ExerciseProgressionResponse(AnalysisResponse):
    """Model for exercise progression analysis response."""
    exercise: Optional[str]
    analysis: str
    progression_rate: Optional[str]
    plateaus: List[str]
    recommendations: List[str]
    chart_data: Optional[Dict[str, Any]]


class InjuryRiskResponse(AnalysisResponse):
    """Model for injury risk assessment response."""
    overall_risk: str
    potential_issues: List[Dict[str, Any]]
    protective_factors: List[str]
    recommendations: List[str]


class WorkoutRecommendationResponse(AnalysisResponse):
    """Model for workout recommendation response."""
    goal: str
    workout_plan: Dict[str, Any]
    reasoning: str
    alternatives: List[Dict[str, Any]]


class ClientInsightResponse(AnalysisResponse):
    """Model for client insight response."""
    insight_type: str
    insights: List[Dict[str, Any]]
    summary: str
    action_items: List[str] 