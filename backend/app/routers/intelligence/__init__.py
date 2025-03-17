"""
Intelligence API module.

This package contains routers for AI-powered analysis and insights.
"""

from fastapi import APIRouter

from .progress_analysis import router as progress_router
from .injury_risk import router as injury_router
from .workout_recommendation import router as recommendation_router
from .client_insights import router as insights_router
from .models import *

# Create a combined router
router = APIRouter(
    prefix="/intelligence",
    tags=["intelligence"],
    responses={401: {"description": "Unauthorized"}}
)

# Include sub-routers
router.include_router(progress_router)
router.include_router(injury_router)
router.include_router(recommendation_router)
router.include_router(insights_router) 