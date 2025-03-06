# Trainer's Memory AI Assistant

A comprehensive fitness trainer AI assistant that helps trainers manage client workouts, analyze progress, and provide personalized recommendations.

## Features

1. **Multi-Format Data Ingestion**  
   - Spreadsheet parser for CSV/XLSX workout logs
   - OCR integration for handwritten notes
   - Unified data schema for workout records

2. **Voice Interface**  
   - WebSpeech API implementation for voice notes
   - Whisper API integration for voice command processing
   - Context-aware command recognition

3. **AI Analysis Engine**  
   - Natural language queries for workout data analysis
   - Progress trend detection
   - Injury pattern recognition
   - Exercise modification recommendations

4. **Security**  
   - HIPAA-compliant data storage
   - Role-based access control
   - Data encryption at rest/in transit

## Project Structure

```
trainer-memory/
├── backend/               # FastAPI backend
│   ├── app/               # Application code
│   │   ├── routers/       # API endpoints
│   │   ├── main.py        # FastAPI app
│   │   ├── models.py      # Pydantic models
│   │   ├── db.py          # Database client
│   │   ├── auth.py        # Authentication
│   │   └── ocr.py         # OCR processing
│   ├── tests/             # Test suite
│   ├── requirements.txt   # Python dependencies
│   └── schema.sql         # Database schema
├── src/                   # Next.js frontend
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   ├── lib/               # Utility functions
│   └── styles/            # CSS styles
└── public/                # Static assets
```

## Tech Stack

- **Backend**: Python (FastAPI)
- **Frontend**: Next.js
- **Database**: Supabase (PostgreSQL)
- **AI**: OpenAI APIs
- **OCR**: Tesseract
- **Voice**: Web Speech API, Whisper API

## Development Roadmap

### Phase 1: Foundation (2 weeks)
- Set up project structure
- Implement authentication
- Create database schema
- Build basic UI components

### Phase 2: Data Ingestion (2 weeks)
- Spreadsheet import functionality
- OCR processing for handwritten notes
- Workout data validation

### Phase 3: Voice Interface (2 weeks)
- Voice recording and transcription
- Voice command processing
- Voice-to-text note taking

### Phase 4: AI Analysis (3 weeks)
- Natural language query interface
- Progress visualization
- Workout recommendation system

### Phase 5: Security & Optimization (1 week)
- Security audit
- Performance optimization
- Final testing

## Cost Optimization

- Batch processing for OpenAI API calls
- Caching for frequent queries
- Optimized image processing for OCR
- Client-side speech recognition when possible

## Getting Started

### Backend Setup

See [Backend README](./backend/README.md) for detailed setup instructions.

### Frontend Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

Visit http://localhost:3000 to see the application.

## License

MIT

## Contributors

- [Your Name](https://github.com/yourusername)
