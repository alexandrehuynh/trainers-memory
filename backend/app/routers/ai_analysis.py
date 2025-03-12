"""
AI Analysis Module

This module provides AI-powered analysis of client workout data using OpenAI's API.
It implements:
1. Intelligent model selection with fallbacks (gpt-4o-mini → gpt-3.5-turbo → gpt-3.5-turbo-16k)
2. Rate limiting (3 requests per minute) to comply with OpenAI's free tier limits
3. Graceful handling of rate limit errors with automatic waiting and retries
4. Status endpoint to monitor current rate limit usage
5. Redis-based caching for OpenAI responses to reduce costs and improve performance

Usage:
- POST /api/v1/intelligence/analysis/analyze - Analyze client workout data
- GET /api/v1/intelligence/analysis/rate-limit-status - Check current rate limit status
- POST /api/v1/intelligence/analysis/clear-cache - Clear the OpenAI response cache

Environment variables:
- OPENAI_API_KEY: Your OpenAI API key
- OPENAI_MODEL: (Optional) Override the default model (gpt-4o-mini)
- REDIS_URL: (Optional) Redis connection URL for caching (default: redis://localhost:6379/0)
- OPENAI_CACHE_TTL: (Optional) Cache TTL in seconds (default: 3600)
"""

import pandas as pd
# Uncomment numpy if it's actually needed elsewhere in the file
# import numpy as np
from openai import OpenAI
import os
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import time
from collections import deque
from ..auth_utils import validate_api_key
from ..utils.response import StandardResponse
from ..utils.cache.openai_cache import openai_cache
from ..utils.cache.openai_analysis import analyze_with_openai_cached
from ..utils.fitness_data.embedding_tools import get_rag_context
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_async_db, AsyncClientRepository, AsyncWorkoutRepository
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query

# Create router - remove prefix to avoid duplication with main.py's prefix
router = APIRouter()

# Define models if they don't exist in a central place
class AIAnalysisRequest(BaseModel):
    client_id: str = Field(..., example="c1d2e3f4-g5h6-i7j8-k9l0-m1n2o3p4q5r6")
    query: str = Field(..., example="What are the trends in bench press performance?")
    force_refresh: bool = Field(False, description="If true, ignore cached results and force a new API call")

class AIAnalysisResponse(BaseModel):
    answer: str
    data: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}

# For cache clearing endpoint
class CacheClearRequest(BaseModel):
    client_id: Optional[str] = Field(None, description="If provided, only clear cache for this client")

class CacheClearResponse(BaseModel):
    entries_cleared: int
    success: bool
    
    model_config = {"from_attributes": True}

# Simple rate limiter for OpenAI API
class SimpleRateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.request_timestamps = deque()
    
    def can_make_request(self):
        # Remove timestamps older than the time window
        current_time = time.time()
        while self.request_timestamps and current_time - self.request_timestamps[0] > self.time_window:
            self.request_timestamps.popleft()
        
        # Check if we're under the limit
        return len(self.request_timestamps) < self.max_requests
    
    def add_request(self):
        self.request_timestamps.append(time.time())

# Create a rate limiter instance (3 requests per minute)
rate_limiter = SimpleRateLimiter(max_requests=3, time_window=60)

# OpenAI client will be initialized only when needed
client = None

def get_openai_client():
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Return a dummy key for development if no API key is provided
            print("WARNING: No OpenAI API key found. AI features will not work properly.")
            api_key = "dummy_key_for_development"
        client = OpenAI(api_key=api_key)
    return client

# Get the best available OpenAI model
def get_best_available_model():
    # Try to use environment variable first, default to gpt-4o-mini
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Fallback models in order of preference
    fallback_models = ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
    
    if model not in fallback_models:
        fallback_models.insert(0, model)  # Add user's preferred model as first choice
    
    return fallback_models

# Safely create chat completion with fallbacks and caching
def create_chat_completion(messages, temperature=0.1, max_tokens=500, force_refresh=False):
    models = get_best_available_model()
    last_error = None
    
    # Check if the response is in cache (if not forcing refresh)
    if not force_refresh:
        for model in models:
            cached_response = openai_cache.get(messages, model)
            if cached_response:
                print(f"Using cached response for model {model}")
                return cached_response
    
    # Check if we're approaching rate limit and wait if needed
    current_time = time.time()
    # Clean up expired timestamps
    while rate_limiter.request_timestamps and current_time - rate_limiter.request_timestamps[0] > rate_limiter.time_window:
        rate_limiter.request_timestamps.popleft()
    
    # If we're at maximum capacity, wait for the oldest request to expire
    if len(rate_limiter.request_timestamps) >= rate_limiter.max_requests:
        oldest_timestamp = rate_limiter.request_timestamps[0]
        wait_time = rate_limiter.time_window - (current_time - oldest_timestamp) + 1  # Add 1 second buffer
        if wait_time > 0:
            print(f"Rate limit approached. Waiting {wait_time} seconds before making next request...")
            time.sleep(wait_time)
    
    # Try each model in sequence
    for model in models:
        try:
            print(f"Attempting to use model: {model}")
            response = get_openai_client().chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print(f"Successfully used model: {model}")
            # Record this successful request in our rate limiter
            rate_limiter.add_request()
            
            # Cache the successful response
            # Convert to a cacheable format (response object might not be serializable)
            cacheable_response = {
                "model": model,
                "choices": [
                    {
                        "message": {
                            "content": response.choices[0].message.content,
                            "role": "assistant"
                        },
                        "index": 0
                    }
                ],
                "created": int(time.time()),
                "cached": True
            }
            
            # Store in cache
            openai_cache.set(messages, model, cacheable_response)
            
            return response
        except Exception as e:
            last_error = e
            print(f"Failed to use model {model}: {str(e)}")
            
            # Check if this is a rate limit error
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                print("Rate limit exceeded. Waiting 20 seconds before trying next model...")
                time.sleep(20)  # Wait 20 seconds before trying next model
            # Continue to next model
    
    # If we've tried all models and none worked, raise the last error
    if last_error:
        raise last_error
    else:
        raise Exception("All models failed but no error was recorded")

# Helper function to get client name (duplicated from clients.py for now)
def get_client_name(client_id: str) -> str:
    # In a real implementation, you would fetch this from a database
    # This is just a mock implementation for demo purposes
    from .clients import clients_db
    if client_id in clients_db:
        return clients_db[client_id]["name"]
    return "Unknown Client"

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_client_data(
    request: AIAnalysisRequest,
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Analyze client workout data using natural language queries
    
    This endpoint uses OpenAI to analyze workout data and provide insights
    based on the specific query provided. Results are cached to improve 
    performance and reduce costs.
    """
    # Check rate limit if not using cache
    if request.force_refresh and not rate_limiter.can_make_request():
        return StandardResponse.error(
            message="Rate limit exceeded. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Add this request to the rate limiter if we're not using cache
    if request.force_refresh:
        rate_limiter.add_request()
    
    try:
        # Get client information (in production, fetch from database)
        client_name = get_client_name(request.client_id)
        
        # Get workout records (in production, fetch from database)
        from .workouts import workouts_db
        workout_records = [w for w in workouts_db.values() if w["client_id"] == request.client_id]
        
        if not workout_records:
            return StandardResponse.success(
                data={"answer": "No workout data available for this client. Please add some workout records first."},
                message="Analysis completed with no data"
            )
            
        # Create a pandas DataFrame from workout records for analysis
        df = pd.DataFrame(workout_records)
        
        # Prepare context for OpenAI
        df_stats = {}
        
        # Calculate basic stats for numerical columns
        for col in ['sets', 'reps', 'weight']:
            if col in df.columns:
                df_stats[col] = {
                    'mean': float(df[col].mean()) if not df[col].empty else 0,
                    'max': float(df[col].max()) if not df[col].empty else 0,
                    'min': float(df[col].min()) if not df[col].empty else 0
                }
                
        # Get exercise frequency if possible
        exercise_counts = {}
        if 'exercises' in df.columns:
            # This is a more complex structure, would need custom handling
            # For now, we'll just count total exercises
            exercise_counts = {"total_exercises": sum(len(w.get("exercises", [])) for w in workout_records)}
        
        # Context message for OpenAI
        context = {
            "client_name": client_name,
            "workout_stats": df_stats,
            "exercise_counts": exercise_counts,
            "workout_records": workout_records[:10]  # Limit to 10 most recent workouts
        }
        
        # Get RAG context for the query
        rag_context = get_rag_context(request.query)
        
        # Call OpenAI for analysis using our helper with fallbacks
        messages = [
            {"role": "system", "content": "You are a fitness analysis assistant that helps trainers understand their clients' workout data. Provide concise, actionable insights."},
            {"role": "system", "content": f"Here is some relevant fitness knowledge to help you provide accurate information:\n\n{rag_context}"},
            {"role": "user", "content": f"Analyze the following client workout data. Question: {request.query}"},
            {"role": "system", "content": f"Here's the client data: {str(context)}"}
        ]
        
        response = create_chat_completion(messages, temperature=0.1, max_tokens=500, force_refresh=request.force_refresh)
        
        # Extract and return the AI's analysis
        answer = response.choices[0].message.content
        
        # Check if response was from cache
        from_cache = hasattr(response, 'cached') and response.cached
        
        return StandardResponse.success(
            data={
                "answer": answer,
                "query": request.query,
                "client_name": client_name,
                "model_used": response.model,  # Include which model was actually used
                "from_cache": from_cache,
                "used_rag": True
            },
            message="Analysis completed successfully" + (" (from cache)" if from_cache else "")
        )
        
    except Exception as e:
        import traceback
        print("Error in analyze_client_data:")
        traceback.print_exc()  # Print full stack trace for debugging
        
        error_detail = str(e)
        # Add more context if it's an OpenAI API error
        if "openai" in error_detail.lower():
            error_detail = f"Error code: {getattr(e, 'status_code', 'unknown')} - {error_detail}"
        
        return StandardResponse.error(
            message=f"Analysis failed: {error_detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Add a rate limit status endpoint
@router.get("/rate-limit-status", response_model=Dict[str, Any])
async def get_rate_limit_status(
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """Get the current status of the rate limiter"""
    # Calculate remaining capacity
    current_time = time.time()
    # Remove expired timestamps
    while rate_limiter.request_timestamps and current_time - rate_limiter.request_timestamps[0] > rate_limiter.time_window:
        rate_limiter.request_timestamps.popleft()
    
    used_capacity = len(rate_limiter.request_timestamps)
    remaining_capacity = rate_limiter.max_requests - used_capacity
    
    # Calculate time until next available slot if at capacity
    time_until_reset = 0
    if used_capacity >= rate_limiter.max_requests and rate_limiter.request_timestamps:
        time_until_reset = int(rate_limiter.time_window - (current_time - rate_limiter.request_timestamps[0]))
    
    return StandardResponse.success(
        data={
            "max_requests_per_minute": rate_limiter.max_requests,
            "requests_made_in_window": used_capacity,
            "requests_remaining": remaining_capacity,
            "seconds_until_reset": time_until_reset if time_until_reset > 0 else 0,
            "window_size_seconds": rate_limiter.time_window,
            "current_openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "cache_enabled": openai_cache.enabled,
            "cache_ttl": openai_cache.default_ttl
        },
        message="Rate limit status retrieved successfully"
    )

# Add a cache clear endpoint
@router.post("/clear-cache", response_model=Dict[str, Any])
async def clear_cache(
    request: CacheClearRequest,
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """Clear the OpenAI response cache, either for a specific client or all clients"""
    try:
        if request.client_id:
            # Clear cache for specific client
            entries_cleared = openai_cache.invalidate_by_client(request.client_id)
        else:
            # Clear all cache
            entries_cleared = openai_cache.clear_all()
        
        return StandardResponse.success(
            data={
                "entries_cleared": entries_cleared,
                "success": True
            },
            message=f"Successfully cleared {entries_cleared} cache entries"
        )
    except Exception as e:
        return StandardResponse.error(
            message=f"Failed to clear cache: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/analysis/analyze", response_model=Dict[str, Any])
async def analyze_client_data(
    client_id: Optional[uuid.UUID] = Query(None, description="Client ID to analyze"),
    time_period: Optional[str] = Query("30d", description="Time period to analyze (7d, 30d, 90d, all)"),
    query: str = Query(..., min_length=5, max_length=1000, description="Analysis question or request"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze client workout data using OpenAI.
    
    Submit a natural language query about the client's workout history and get AI-powered analysis.
    
    Examples:
    - "What exercises has this client been doing most frequently?"
    - "Has the client been making progress on their bench press?"
    - "What muscle groups need more attention based on their workout history?"
    - "Suggest modifications to their routine based on their performance"
    
    The analysis will be cached for identical queries to reduce API costs and improve response times.
    """
    # Validate client exists if client_id is provided
    if client_id:
        client_repo = AsyncClientRepository(db)
        client = await client_repo.get(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
    
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
    
    # Get client workouts
    workout_repo = AsyncWorkoutRepository(db)
    
    if client_id:
        if days:
            # Calculate date threshold
            date_threshold = datetime.utcnow() - timedelta(days=days)
            workouts = await workout_repo.get_by_client_since_date(client_id, date_threshold)
        else:
            workouts = await workout_repo.get_by_client(client_id)
        
        # Prepare client info
        client_name = client.name if client else "Unknown Client"
    else:
        workouts = []
        client_name = "All Clients"
    
    # Prepare the workout data for analysis
    workout_data = []
    for workout in workouts:
        workout_dict = {
            "id": str(workout.id),
            "date": workout.date.isoformat() if workout.date else None,
            "name": workout.name,
            "notes": workout.notes,
            "duration_minutes": workout.duration_minutes,
            "exercises": workout.exercises
        }
        workout_data.append(workout_dict)
    
    # Get RAG context if available
    rag_context = get_rag_context(query, max_tokens=1000)
    
    # Prepare the data for OpenAI
    try:
        analysis_result = await analyze_with_openai_cached(
            client_name=client_name,
            workout_data=workout_data,
            query=query,
            rag_context=rag_context
        )
        
        # Return the analysis result
        return StandardResponse.success(
            data={
                "analysis": analysis_result["content"],
                "from_cache": analysis_result.get("from_cache", False),
                "used_rag": bool(rag_context)
            },
            message="Analysis completed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing client data: {str(e)}"
        )

@router.get("/analysis/rate-limit-status", response_model=Dict[str, Any])
async def get_rate_limit_status(
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Get the current rate limit status for OpenAI API usage.
    
    Returns information about:
    - Current usage
    - Rate limits
    - Remaining tokens
    - Reset time
    """
    # This would typically query a service that tracks API usage
    # For now, return placeholder data
    return StandardResponse.success(
        data={
            "usage": {
                "prompt_tokens_today": 15000,
                "completion_tokens_today": 5000,
                "total_tokens_today": 20000
            },
            "limits": {
                "tokens_per_day": 100000,
                "tokens_per_minute": 10000
            },
            "remaining": {
                "tokens_today": 80000
            },
            "reset": {
                "daily_at": "00:00:00 UTC"
            }
        },
        message="Rate limit status retrieved successfully"
    ) 