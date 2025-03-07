from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

# Import StandardResponse from utils
from app.utils.response import StandardResponse, API_VERSION

# API title and description
API_TITLE = "Trainer's Memory API"
API_DESCRIPTION = """
An AI-powered fitness intelligence layer that gives fitness platforms the ability to understand, 
analyze, and derive insights from client workout data.
"""

# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url=f"/api/{API_VERSION}/docs",
    redoc_url=f"/api/{API_VERSION}/redoc",
    openapi_url=f"/api/{API_VERSION}/openapi.json",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
API_KEYS = {}  # In production, use a database

# Load API keys from environment variables (for development)
# Format: PREFIX_API_KEY_NAME=value (e.g., TRAINERS_MEMORY_API_KEY_ACME=12345)
for env_key, env_value in os.environ.items():
    if env_key.startswith("TRAINERS_MEMORY_API_KEY_"):
        client_name = env_key.replace("TRAINERS_MEMORY_API_KEY_", "").lower()
        API_KEYS[env_value] = {"client": client_name, "created": datetime.now().isoformat()}

# For demo purposes, create a test key if none exists
if not API_KEYS:
    test_key = "test_api_key_123456"
    API_KEYS[test_key] = {"client": "test_client", "created": datetime.now().isoformat()}

async def get_api_key(api_key: str = Security(api_key_header)) -> Dict[str, Any]:
    """Validate the API key and return client info."""
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header is missing",
            headers={"WWW-Authenticate": API_KEY_NAME},
        )
        
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": API_KEY_NAME},
        )
        
    return API_KEYS[api_key]

# Add a simple health check endpoint at root
@app.get("/")
async def root():
    return {"message": "Trainer's Memory API is running", "version": API_VERSION}

# Add a simple health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}

# Demo endpoint with authentication
@app.get(f"/api/{API_VERSION}/me", tags=["Authentication"])
async def get_my_info(client_info: Dict[str, Any] = Depends(get_api_key)):
    """Return the client information associated with the API key."""
    return StandardResponse.success(client_info)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
    )
    
    # Add API Key security scheme
    openapi_schema["components"] = {
        "securitySchemes": {
            API_KEY_NAME: {
                "type": "apiKey",
                "in": "header",
                "name": API_KEY_NAME,
                "description": "API Key Authentication",
            }
        }
    }
    
    # Apply security to all routes
    openapi_schema["security"] = [{API_KEY_NAME: []}]
    
    # Add custom schema info
    openapi_schema["info"]["contact"] = {
        "name": "Trainer's Memory Support",
        "email": "support@trainersmemory.api",
        "url": "https://trainersmemory.api/support",
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Import routers last to avoid circular imports
from app.routers import clients, workouts, intelligence, transformation, communication, analytics, coaching, content
from app.routers import ai_analysis, ocr

# Mount routers with version prefix
app.include_router(
    clients.router,
    prefix=f"/api/{API_VERSION}",
    tags=["Clients"],
)

app.include_router(
    workouts.router,
    prefix=f"/api/{API_VERSION}",
    tags=["Workouts"],
)

app.include_router(
    intelligence.router,
    prefix=f"/api/{API_VERSION}/intelligence",
    tags=["Intelligence"],
)

app.include_router(
    transformation.router,
    prefix=f"/api/{API_VERSION}/transformation",
    tags=["Transformation"],
)

app.include_router(
    communication.router,
    prefix=f"/api/{API_VERSION}/communication",
    tags=["Communication"],
)

app.include_router(
    analytics.router,
    prefix=f"/api/{API_VERSION}/analytics",
    tags=["Analytics"],
)

app.include_router(
    coaching.router,
    prefix=f"/api/{API_VERSION}/coaching",
    tags=["Coaching"],
)

app.include_router(
    content.router,
    prefix=f"/api/{API_VERSION}/content",
    tags=["Content"],
)

# Add the AI Analysis router
app.include_router(
    ai_analysis.router,
    prefix=f"/api/{API_VERSION}",
    tags=["Intelligence"],
)

# Add the OCR router
app.include_router(
    ocr.router,
    prefix=f"/api/{API_VERSION}",
    tags=["Transformation"],
)

# Entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 