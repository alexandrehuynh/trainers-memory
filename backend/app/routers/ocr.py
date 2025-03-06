from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List
import io
import os
from ..ocr import OCRProcessor
from ..db import create_workout_record
from ..auth import get_current_user, verify_trainer_role

router = APIRouter(
    prefix="/ocr",
    tags=["ocr"],
    responses={404: {"description": "Not found"}},
)

# Initialize OCR processor
ocr_processor = OCRProcessor(tesseract_cmd=os.getenv("TESSERACT_CMD"))

@router.post("/process")
async def process_workout_image(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    current_user=Depends(verify_trainer_role)
):
    """
    Process an image containing handwritten workout notes
    
    Args:
        file: The image file to process
        client_id: ID of the client the workout belongs to
    """
    try:
        # Read image file
        image_bytes = await file.read()
        
        # Process image with OCR
        ocr_text = ocr_processor.process_image(image_bytes)
        
        # Extract workout data from OCR text
        workout_records = ocr_processor.extract_workout_data(ocr_text, client_id)
        
        if not workout_records:
            return {
                "message": "No valid workout data could be extracted from the image. Please check the image quality or format.",
                "ocr_text": ocr_text
            }
        
        # Store workout records in database
        saved_records = []
        for record in workout_records:
            # Add created_by field
            record["created_by"] = current_user["id"]
            
            # Save to database
            result = await create_workout_record(record)
            saved_records.append(result)
        
        return {
            "message": f"Successfully processed {len(saved_records)} workout records",
            "ocr_text": ocr_text,
            "records": saved_records
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}",
        ) 