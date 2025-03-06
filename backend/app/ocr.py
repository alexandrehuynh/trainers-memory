import pytesseract
from PIL import Image
import io
import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

class OCRProcessor:
    """Process images of handwritten workout notes using OCR"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """Initialize OCR processor with optional path to Tesseract executable"""
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def process_image(self, image_bytes: bytes) -> str:
        """Extract text from image using Tesseract OCR"""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract text from image
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def extract_workout_data(self, ocr_text: str, client_id: str) -> List[Dict[str, Any]]:
        """
        Parse OCR text into structured workout data
        
        Example expected format:
        Date: 2023-03-15
        Exercise: Bench Press
        Sets: 3, Reps: 8-10, Weight: 185lbs
        Notes: Good form on first 2 sets
        
        Exercise: Incline DB Press
        Sets: 3, Reps: 10, Weight: 65lbs
        
        etc.
        """
        workout_records = []
        
        # Split text into workout sections
        workout_sections = re.split(r'\n\s*\n', ocr_text)
        
        current_date = None
        
        for section in workout_sections:
            # Skip empty sections
            if not section.strip():
                continue
                
            # Parse section
            lines = section.strip().split('\n')
            
            # Extract workout data
            workout_data = {
                'client_id': client_id,
                'date': current_date,
                'exercise': None,
                'sets': None,
                'reps': None,
                'weight': None,
                'notes': None,
                'modifiers': None
            }
            
            for line in lines:
                line = line.strip()
                
                # Check for date
                date_match = re.search(r'date:?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{2,4})', line, re.IGNORECASE)
                if date_match:
                    try:
                        # Try to parse date in different formats
                        date_str = date_match.group(1)
                        
                        # Handle different date formats
                        if '-' in date_str:
                            current_date = pd.to_datetime(date_str, format='%Y-%m-%d').isoformat()
                        else:
                            current_date = pd.to_datetime(date_str, format='%m/%d/%Y').isoformat()
                        
                        workout_data['date'] = current_date
                        continue
                    except:
                        # If date parsing fails, use current date
                        current_date = datetime.now().isoformat()
                        workout_data['date'] = current_date
                        continue
                
                # Check for exercise
                exercise_match = re.search(r'exercise:?\s*(.+)', line, re.IGNORECASE)
                if exercise_match:
                    workout_data['exercise'] = exercise_match.group(1).strip()
                    continue
                
                # Check for sets
                sets_match = re.search(r'sets:?\s*(\d+)', line, re.IGNORECASE)
                if sets_match:
                    workout_data['sets'] = int(sets_match.group(1))
                    
                    # Check if reps is on the same line
                    reps_match = re.search(r'reps:?\s*(\d+(?:-\d+)?)', line, re.IGNORECASE)
                    if reps_match:
                        reps = reps_match.group(1)
                        # If range (e.g., 8-10), take the average
                        if '-' in reps:
                            min_reps, max_reps = map(int, reps.split('-'))
                            workout_data['reps'] = (min_reps + max_reps) // 2
                        else:
                            workout_data['reps'] = int(reps)
                    
                    # Check if weight is on the same line
                    weight_match = re.search(r'weight:?\s*(\d+(?:\.\d+)?)\s*(?:lbs?|kg)?', line, re.IGNORECASE)
                    if weight_match:
                        workout_data['weight'] = float(weight_match.group(1))
                    
                    continue
                
                # Check for reps (if not found on sets line)
                if workout_data['reps'] is None:
                    reps_match = re.search(r'reps:?\s*(\d+(?:-\d+)?)', line, re.IGNORECASE)
                    if reps_match:
                        reps = reps_match.group(1)
                        if '-' in reps:
                            min_reps, max_reps = map(int, reps.split('-'))
                            workout_data['reps'] = (min_reps + max_reps) // 2
                        else:
                            workout_data['reps'] = int(reps)
                        continue
                
                # Check for weight (if not found on sets line)
                if workout_data['weight'] is None:
                    weight_match = re.search(r'weight:?\s*(\d+(?:\.\d+)?)\s*(?:lbs?|kg)?', line, re.IGNORECASE)
                    if weight_match:
                        workout_data['weight'] = float(weight_match.group(1))
                        continue
                
                # Check for notes
                notes_match = re.search(r'notes:?\s*(.+)', line, re.IGNORECASE)
                if notes_match:
                    workout_data['notes'] = notes_match.group(1).strip()
                    continue
                
                # Check for modifiers
                modifiers_match = re.search(r'modifiers:?\s*(.+)', line, re.IGNORECASE)
                if modifiers_match:
                    workout_data['modifiers'] = modifiers_match.group(1).strip()
                    continue
            
            # If we have a valid exercise record with required fields, add it
            if (workout_data['exercise'] and 
                workout_data['sets'] is not None and 
                workout_data['reps'] is not None and 
                workout_data['weight'] is not None):
                
                # Set date to current date if not specified
                if not workout_data['date']:
                    workout_data['date'] = datetime.now().isoformat()
                
                workout_records.append(workout_data)
        
        return workout_records 