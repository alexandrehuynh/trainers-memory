from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import pandas as pd
import numpy as np
from openai import OpenAI
import os
from ..models import AIAnalysisRequest, AIAnalysisResponse
from ..db import get_workout_records, get_client_by_id
from ..auth import get_current_user, verify_trainer_role

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    dependencies=[Depends(verify_trainer_role)],  # Require trainer role for all endpoints
    responses={404: {"description": "Not found"}},
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/", response_model=AIAnalysisResponse)
async def analyze_client_data(request: AIAnalysisRequest, current_user=Depends(get_current_user)):
    """Analyze client workout data using natural language queries"""
    try:
        # Get client information
        client_data = await get_client_by_id(request.client_id)
        if not client_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {request.client_id} not found",
            )
            
        # Get workout records
        workout_records = await get_workout_records(request.client_id, limit=500)
        
        if not workout_records:
            return AIAnalysisResponse(
                answer="No workout data available for this client. Please add some workout records first."
            )
            
        # Create a pandas DataFrame from workout records for analysis
        df = pd.DataFrame(workout_records)
        
        # Prepare context for OpenAI
        df_stats = {}
        
        # Calculate basic stats for numerical columns
        for col in ['sets', 'reps', 'weight']:
            if col in df.columns:
                df_stats[col] = {
                    'mean': float(df[col].mean()),
                    'max': float(df[col].max()),
                    'min': float(df[col].min())
                }
                
        # Get exercise frequency
        exercise_counts = df['exercise'].value_counts().to_dict()
        
        # Prepare workout history summary
        workout_history = df.to_dict(orient='records')
        
        # Context message for OpenAI
        context = {
            "client_name": client_data.get("name", "Unknown"),
            "workout_stats": df_stats,
            "exercise_frequency": exercise_counts,
            "workout_history": workout_history[:50]  # Limit to 50 most recent workouts
        }
        
        # Function calling with OpenAI
        response = client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for best analysis
            messages=[
                {"role": "system", "content": "You are a fitness analysis assistant that helps trainers understand their clients' workout data. Provide concise, actionable insights."},
                {"role": "user", "content": f"Analyze the following client workout data. Question: {request.query}"},
                {"role": "system", "content": f"Here's the client data: {str(context)}"}
            ],
            temperature=0.1,  # Low temperature for more factual responses
            max_tokens=500,   # Limit response length
        )
        
        # Extract and return the AI's analysis
        answer = response.choices[0].message.content
        
        return AIAnalysisResponse(
            answer=answer,
            data={"client_name": client_data.get("name"), "query": request.query}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        ) 