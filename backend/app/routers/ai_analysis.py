from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from openai import OpenAI
import os
from pydantic import BaseModel, Field, UUID4
from datetime import datetime

# Import API key dependency and standard response
from ..main import get_api_key
from ..utils.response import StandardResponse

# Define models if they don't exist in a central place
class AIAnalysisRequest(BaseModel):
    client_id: str = Field(..., example="c1d2e3f4-g5h6-i7j8-k9l0-m1n2o3p4q5r6")
    query: str = Field(..., example="What are the trends in bench press performance?")

class AIAnalysisResponse(BaseModel):
    answer: str
    data: Optional[Dict[str, Any]] = None

# Create router
router = APIRouter(
    prefix="/intelligence/analysis",
    tags=["intelligence"],
    responses={404: {"description": "Not found"}},
)

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
    # Try to use environment variable first
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo if not specified
    
    # Fallback models in order of preference
    fallback_models = ["gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
    
    if model not in fallback_models:
        fallback_models.insert(0, model)  # Add user's preferred model as first choice
    
    return fallback_models

# Safely create chat completion with fallbacks
def create_chat_completion(messages, temperature=0.1, max_tokens=500):
    models = get_best_available_model()
    last_error = None
    
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
            return response
        except Exception as e:
            last_error = e
            print(f"Failed to use model {model}: {str(e)}")
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
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Analyze client workout data using natural language queries
    
    This endpoint uses OpenAI to analyze workout data and provide insights
    based on the specific query provided.
    """
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
        
        # Call OpenAI for analysis using our helper with fallbacks
        messages = [
            {"role": "system", "content": "You are a fitness analysis assistant that helps trainers understand their clients' workout data. Provide concise, actionable insights."},
            {"role": "user", "content": f"Analyze the following client workout data. Question: {request.query}"},
            {"role": "system", "content": f"Here's the client data: {str(context)}"}
        ]
        
        response = create_chat_completion(messages, temperature=0.1, max_tokens=500)
        
        # Extract and return the AI's analysis
        answer = response.choices[0].message.content
        
        return StandardResponse.success(
            data={
                "answer": answer,
                "query": request.query,
                "client_name": client_name,
                "model_used": response.model  # Include which model was actually used
            },
            message="Analysis completed successfully"
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