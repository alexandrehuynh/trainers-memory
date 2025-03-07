import pytesseract
from PIL import Image
import io
import re
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
        
        current_date = datetime.now().isoformat()
        workout_type = "Strength Training"  # Default type
        workout_duration = 60  # Default duration in minutes
        exercises = []
        
        # First pass: look for global workout attributes (date, type, duration)
        for section in workout_sections:
            if not section.strip():
                continue
                
            lines = section.strip().split('\n')
            
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
                            # Ensure proper ISO format (YYYY-MM-DD)
                            parts = date_str.split('-')
                            if len(parts) == 3:
                                year, month, day = parts
                                # Add leading zeros if needed
                                if len(month) == 1:
                                    month = f"0{month}"
                                if len(day) == 1:
                                    day = f"0{day}"
                                current_date = f"{year}-{month}-{day}"
                        else:
                            # Handle MM/DD/YYYY format
                            parts = date_str.split('/')
                            if len(parts) == 3:
                                month, day, year = parts
                                # Add leading zeros if needed
                                if len(month) == 1:
                                    month = f"0{month}"
                                if len(day) == 1:
                                    day = f"0{day}"
                                # Handle 2-digit years
                                if len(year) == 2:
                                    year = f"20{year}"
                                current_date = f"{year}-{month}-{day}"
                    except:
                        # If date parsing fails, use current date
                        current_date = datetime.now().isoformat().split('T')[0]
                        
                # Check for workout type
                type_match = re.search(r'type:?\s*(.+)', line, re.IGNORECASE)
                if type_match:
                    workout_type = type_match.group(1).strip()
                    
                # Check for duration
                duration_match = re.search(r'duration:?\s*(\d+)', line, re.IGNORECASE)
                if duration_match:
                    workout_duration = int(duration_match.group(1))
        
        # Second pass: extract exercises
        current_exercise = None
        
        for section in workout_sections:
            if not section.strip():
                continue
                
            lines = section.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Check for exercise
                exercise_match = re.search(r'exercise:?\s*(.+)', line, re.IGNORECASE)
                if exercise_match:
                    # If we were processing an exercise, add it to the list
                    if current_exercise:
                        exercises.append(current_exercise)
                        
                    # Start a new exercise
                    current_exercise = {
                        'name': exercise_match.group(1).strip(),
                        'sets': None,
                        'reps': None,
                        'weight': None,
                        'notes': None
                    }
                    continue
                
                # If no current exercise, skip
                if not current_exercise:
                    continue
                
                # Check for sets
                sets_match = re.search(r'sets:?\s*(\d+)', line, re.IGNORECASE)
                if sets_match:
                    current_exercise['sets'] = int(sets_match.group(1))
                    
                    # Check if reps is on the same line
                    reps_match = re.search(r'reps:?\s*(\d+(?:-\d+)?)', line, re.IGNORECASE)
                    if reps_match:
                        reps = reps_match.group(1)
                        # If range (e.g., 8-10), take the average
                        if '-' in reps:
                            min_reps, max_reps = map(int, reps.split('-'))
                            current_exercise['reps'] = (min_reps + max_reps) // 2
                        else:
                            current_exercise['reps'] = int(reps)
                    
                    # Check if weight is on the same line
                    weight_match = re.search(r'weight:?\s*(\d+(?:\.\d+)?)\s*(?:lbs?|kg)?', line, re.IGNORECASE)
                    if weight_match:
                        current_exercise['weight'] = float(weight_match.group(1))
                    
                    continue
                
                # Check for reps (if not found on sets line)
                if current_exercise['reps'] is None:
                    reps_match = re.search(r'reps:?\s*(\d+(?:-\d+)?)', line, re.IGNORECASE)
                    if reps_match:
                        reps = reps_match.group(1)
                        if '-' in reps:
                            min_reps, max_reps = map(int, reps.split('-'))
                            current_exercise['reps'] = (min_reps + max_reps) // 2
                        else:
                            current_exercise['reps'] = int(reps)
                        continue
                
                # Check for weight (if not found on sets line)
                if current_exercise['weight'] is None:
                    weight_match = re.search(r'weight:?\s*(\d+(?:\.\d+)?)\s*(?:lbs?|kg)?', line, re.IGNORECASE)
                    if weight_match:
                        current_exercise['weight'] = float(weight_match.group(1))
                        continue
                
                # Check for notes
                notes_match = re.search(r'notes:?\s*(.+)', line, re.IGNORECASE)
                if notes_match:
                    current_exercise['notes'] = notes_match.group(1).strip()
                    continue
        
        # Add the last exercise if present
        if current_exercise:
            exercises.append(current_exercise)
            
        # Create a workout record if we have valid exercises
        if exercises:
            # Set defaults for missing values in exercises
            for exercise in exercises:
                if exercise['sets'] is None:
                    exercise['sets'] = 1
                if exercise['reps'] is None:
                    exercise['reps'] = 10
                if exercise['weight'] is None:
                    exercise['weight'] = 0
            
            workout_record = {
                'client_id': client_id,
                'date': current_date,
                'type': workout_type,
                'duration': workout_duration,
                'exercises': exercises,
                'notes': f"Generated from OCR on {datetime.now().isoformat()}"
            }
            
            workout_records.append(workout_record)
        
        return workout_records 