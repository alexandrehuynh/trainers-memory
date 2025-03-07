import uvicorn
from app.main import app
from fastapi import FastAPI

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("test_main_app:app", host="0.0.0.0", port=8000) 