from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, UploadFile, File, Form, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..auth_utils import validate_api_key
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_async_db
from ..utils.response import StandardResponse
import json

# Create router
router = APIRouter()

class TextToDataRequest(BaseModel):
    text: str = Field(..., min_length=3, example="Bench press: 3 sets of 10 reps at 135lbs. Felt strong today.")

@router.post("/notes-to-data", response_model=Dict[str, Any])
async def convert_notes_to_structured_data(
    notes: str = Body(..., description="Raw workout notes to convert to structured data"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Convert raw workout notes to structured workout data.
    
    Submit unstructured workout notes and receive a structured workout object that can be edited or saved.
    The system attempts to identify exercises, sets, reps, weights, and other workout parameters.
    """
    try:
        # This would call a more sophisticated service in a real application
        # For now, return a simple extraction
        structured_data = {
            "date": None,  # Would be extracted if present in notes
            "name": "Workout from Notes",
            "exercises": [],
            "notes": notes,
            "duration_minutes": None
        }
        
        # Very simple exercise extraction - would be more sophisticated in real app
        lines = notes.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Very simple heuristic - assumes exercises have keywords
            exercise_keywords = ['press', 'curl', 'squat', 'bench', 'row', 'pull', 'push', 'lift', 'deadlift']
            if any(keyword in line.lower() for keyword in exercise_keywords):
                structured_data["exercises"].append({
                    "name": line,
                    "sets": None,
                    "reps": None,
                    "weight": None,
                    "notes": ""
                })
        
        return StandardResponse.success(
            data=structured_data,
            message="Notes processed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing notes: {str(e)}"
        )

@router.post("/voice-to-data", response_model=Dict[str, Any])
async def convert_voice_to_structured_data(
    audio_file: Optional[UploadFile] = File(None),
    audio_base64: Optional[str] = Form(None),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Convert voice recording to structured workout data.
    
    Upload an audio file (MP3, WAV, M4A) or base64-encoded audio data of a voice recording
    describing a workout, and receive a structured workout object.
    
    The system first transcribes the audio to text, then extracts structured data from the transcription.
    """
    if not audio_file and not audio_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either audio_file or audio_base64 must be provided"
        )
    
    try:
        # This would call a speech-to-text service and then process the text
        # For demonstration, return a placeholder response
        structured_data = {
            "transcription": "This is where the transcribed audio would appear.",
            "structured_workout": {
                "date": None,
                "name": "Workout from Voice",
                "exercises": [
                    {
                        "name": "Example Exercise",
                        "sets": 3,
                        "reps": 10,
                        "weight": 100,
                        "notes": ""
                    }
                ],
                "notes": "Voice recording processed on " + str(json.dumps(client_info)),
                "duration_minutes": 45
            }
        }
        
        return StandardResponse.success(
            data=structured_data,
            message="Voice recording processed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice recording: {str(e)}"
        ) 