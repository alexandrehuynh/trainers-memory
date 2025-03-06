# Trainer's Memory - Backend API

This is the FastAPI backend for Trainer's Memory, a fitness trainer AI assistant.

## Features

- Multi-format data ingestion (spreadsheets, OCR for handwritten notes)
- Voice transcription and analysis
- AI-powered workout analysis
- Client management
- Secure authentication with Supabase

## Setup Instructions

### Prerequisites

- Python 3.9+
- Tesseract OCR (for handwritten note processing)
- Supabase account
- OpenAI API key

### Installation

1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a .env file in the backend directory with the following content:
   ```
   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   JWT_SECRET=your_jwt_secret
   
   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key
   
   # Tesseract Configuration (optional)
   TESSERACT_CMD=/usr/local/bin/tesseract  # Path to Tesseract executable
   ```

4. Set up the database by running the SQL commands in `schema.sql` in your Supabase project SQL editor.

### Running the API

Start the development server:
```bash
python run.py
```

The API will be available at http://localhost:8000. You can access the Swagger documentation at http://localhost:8000/docs.

## API Endpoints

### Health Check
- GET `/health` - Check if the API is running

### Workouts
- POST `/workouts/` - Create a new workout record
- GET `/workouts/client/{client_id}` - Get workout records for a specific client
- POST `/workouts/upload/spreadsheet` - Upload and process a workout spreadsheet

### OCR
- POST `/ocr/process` - Process an image containing handwritten workout notes

### AI Analysis
- POST `/analysis/` - Analyze client workout data using natural language queries

## Security

- JWT authentication with Supabase Auth
- Role-based access control
- HIPAA-compliant data handling

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
``` 