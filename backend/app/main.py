from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Trainer's Memory API",
    description="API for the Trainer's Memory fitness coaching assistant",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from .routers import workouts, ocr, ai_analysis

# Include routers
app.include_router(workouts.router)
app.include_router(ocr.router)
app.include_router(ai_analysis.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Trainer's Memory API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 