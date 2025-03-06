from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
import pandas as pd
import json
from ..models import WorkoutRecordCreate, WorkoutRecord
from ..db import create_workout_record, get_workout_records
from ..auth import get_current_user

router = APIRouter(
    prefix="/workouts",
    tags=["workouts"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=List[WorkoutRecord])
async def create_workout(workout: WorkoutRecordCreate, current_user=Depends(get_current_user)):
    """Create a new workout record"""
    try:
        # Convert Pydantic model to dict
        workout_data = workout.model_dump()
        # Add audit fields
        workout_data["created_by"] = current_user["id"]
        
        # Create workout record
        result = await create_workout_record(workout_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workout record: {str(e)}",
        )

@router.get("/client/{client_id}", response_model=List[WorkoutRecord])
async def get_client_workouts(
    client_id: str, limit: int = 100, current_user=Depends(get_current_user)
):
    """Get workout records for a specific client"""
    try:
        records = await get_workout_records(client_id, limit)
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workout records: {str(e)}",
        )

@router.post("/upload/spreadsheet")
async def upload_spreadsheet(
    file: UploadFile = File(...), current_user=Depends(get_current_user)
):
    """Upload and process a workout spreadsheet (CSV or Excel)"""
    try:
        # Check file extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be CSV or Excel format"
            )
        
        # Validate required columns
        required_columns = ['client_id', 'date', 'exercise', 'sets', 'reps', 'weight']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Process and store each record
        records = []
        for _, row in df.iterrows():
            record = {
                'client_id': row['client_id'],
                'date': pd.to_datetime(row['date']).isoformat(),
                'exercise': row['exercise'],
                'sets': int(row['sets']),
                'reps': int(row['reps']),
                'weight': float(row['weight']),
                'notes': row.get('notes', ''),
                'modifiers': row.get('modifiers', ''),
                'created_by': current_user["id"]
            }
            
            # Create workout record in database
            result = await create_workout_record(record)
            records.append(result)
            
        return {"message": f"Successfully processed {len(records)} workout records"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process spreadsheet: {str(e)}",
        ) 