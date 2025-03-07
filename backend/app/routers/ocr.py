from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Dict, Any, Optional
import io
import os
import uuid
from datetime import datetime
from ..ocr import OCRProcessor
from ..main import get_api_key
from ..utils.response import StandardResponse

router = APIRouter(
    prefix="/transformation/ocr",
    tags=["transformation"],
    responses={404: {"description": "Not found"}},
)

# Initialize OCR processor
ocr_processor = OCRProcessor(tesseract_cmd=os.getenv("TESSERACT_CMD"))

@router.post("/process", response_model=Dict[str, Any])
async def process_workout_image(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    client_info: Dict[str, Any] = Depends(get_api_key)
):
    """
    Process an image containing handwritten workout notes
    
    This endpoint uses Optical Character Recognition (OCR) to extract workout data
    from images of handwritten notes and converts them to structured workout records.
    
    Args:
        file: The image file to process
        client_id: ID of the client the workout belongs to
    """
    try:
        # Validate file type
        if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            return StandardResponse.error(
                message="Invalid file type. Only JPEG, PNG, and GIF images are supported.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        # Read image file
        image_bytes = await file.read()
        
        # Process image with OCR
        ocr_text = ocr_processor.process_image(image_bytes)
        
        # Extract workout data from OCR text
        workout_records = ocr_processor.extract_workout_data(ocr_text, client_id)
        
        if not workout_records:
            return StandardResponse.success(
                data={
                    "ocr_text": ocr_text
                },
                message="No valid workout data could be extracted from the image. Please check the image quality or format."
            )
        
        # In production, store workout records in database
        # For now, just convert to Workout objects and store in memory
        from .workouts import workouts_db, exercises_db, Workout, Exercise
        
        # Get client name
        from .clients import clients_db
        client_name = "Unknown Client"
        if client_id in clients_db:
            client_name = clients_db[client_id]["name"]
        
        # Store workout records
        saved_workouts = []
        for record in workout_records:
            # Create a workout ID
            workout_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Process exercises
            exercises = []
            for exercise_data in record.get("exercises", []):
                exercise_id = str(uuid.uuid4())
                exercise = {
                    "id": exercise_id,
                    "name": exercise_data.get("exercise", "Unknown Exercise"),
                    "sets": exercise_data.get("sets", 0),
                    "reps": exercise_data.get("reps", 0),
                    "weight": exercise_data.get("weight", 0),
                    "notes": exercise_data.get("notes", "")
                }
                exercises.append(exercise)
                exercises_db[exercise_id] = exercise
            
            # Create workout record
            workout = {
                "id": workout_id,
                "client_id": client_id,
                "client_name": client_name,
                "date": record.get("date", datetime.now().isoformat()),
                "type": record.get("type", "OCR Import"),
                "duration": record.get("duration", 60),
                "notes": f"Imported via OCR on {datetime.now().isoformat()}",
                "exercises": exercises,
                "created_at": timestamp
            }
            
            # Save to mock database
            workouts_db[workout_id] = workout
            saved_workouts.append(workout)
        
        return StandardResponse.success(
            data={
                "workouts": saved_workouts,
                "ocr_text": ocr_text,
            },
            message=f"Successfully processed {len(saved_workouts)} workout records"
        )
        
    except Exception as e:
        return StandardResponse.error(
            message=f"OCR processing failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 