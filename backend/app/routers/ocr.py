from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from typing import List, Dict, Any, Optional
import io
import os
import uuid
from datetime import datetime
from ..ocr import OCRProcessor
from ..auth_utils import validate_api_key
from ..utils.response import StandardResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_async_db
import json
import base64
import pytesseract
from PIL import Image
import re

# Create router - remove prefix to avoid duplication with main.py's prefix
router = APIRouter()

# OCR processor will be initialized only when needed
ocr_processor = None

def get_ocr_processor():
    global ocr_processor
    if ocr_processor is None:
        tesseract_cmd = os.getenv("TESSERACT_CMD")
        ocr_processor = OCRProcessor(tesseract_cmd=tesseract_cmd)
    return ocr_processor

@router.post("/process", response_model=Dict[str, Any])
async def process_workout_image(
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None, description="ID of the client the workout belongs to"),
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Process an image containing workout notes and extract structured data.
    
    Upload an image file (JPEG, PNG) of handwritten or printed workout notes,
    and the OCR system will extract text and attempt to structure the workout data.
    
    Returns both the raw extracted text and a structured workout object that can be further edited.
    """
    # Check file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image"
        )
    
    try:
        # Read the image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Extract text using OCR
        extracted_text = pytesseract.image_to_string(image)
        
        # Process the text to extract workout structure
        structured_workout = extract_workout_from_text(extracted_text)
        
        # If client_id was provided, assign it to the workout
        if client_id:
            structured_workout["client_id"] = client_id
        
        # Return the OCR results
        return StandardResponse.success(
            data={
                "raw_text": extracted_text,
                "structured_workout": structured_workout,
                "filename": file.filename
            },
            message="Image processing completed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )

def extract_workout_from_text(text):
    """Extract structured workout data from OCR text."""
    
    # Simple patterns to identify workout components
    date_pattern = r'date:?\s*([\d/\-\.]+)'
    workout_name_pattern = r'workout:?\s*([^\n]+)'
    exercise_pattern = r'([a-zA-Z\s]+)[\s:]+(\d+)[\s\-xX]+(\d+)[\s@]*([\d\.]+)?'
    
    # Extract date
    date_match = re.search(date_pattern, text, re.IGNORECASE)
    date = date_match.group(1) if date_match else None
    
    # Extract workout name
    name_match = re.search(workout_name_pattern, text, re.IGNORECASE)
    workout_name = name_match.group(1).strip() if name_match else "Workout"
    
    # Extract exercises
    exercise_matches = re.findall(exercise_pattern, text)
    exercises = []
    
    for match in exercise_matches:
        exercise_name = match[0].strip()
        sets = int(match[1])
        reps = int(match[2])
        weight = float(match[3]) if match[3] else None
        
        exercise = {
            "name": exercise_name,
            "sets": sets,
            "reps": reps,
            "weight": weight,
            "notes": ""
        }
        exercises.append(exercise)
    
    # If no structured exercises found, try to split by lines
    if not exercises:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if any(keyword in line.lower() for keyword in ['press', 'curl', 'squat', 'bench', 'row', 'pull', 'push', 'lift']):
                exercises.append({
                    "name": line,
                    "sets": None,
                    "reps": None,
                    "weight": None,
                    "notes": ""
                })
    
    # Construct structured workout
    structured_workout = {
        "id": str(uuid.uuid4()),
        "date": date,
        "name": workout_name,
        "exercises": exercises,
        "notes": text,  # Store full OCR text as notes
        "duration_minutes": None
    }
    
    return structured_workout 