from fastapi import FastAPI, Depends, HTTPException, Security, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader
from typing import Optional, List, Dict, Any
import os
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Import StandardResponse from utils
from app.utils.response import StandardResponse, API_VERSION

# Import database components
from app.db import connect_to_db, disconnect_from_db, AsyncAPIKeyRepository, get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

# Import authentication utilities
from app.auth import get_current_user, refresh_token, verify_user_role, verify_permission
from app.auth_utils import get_api_key, validate_api_key, API_KEY_NAME

# Import routers
from app.routers import clients, workouts, intelligence, transformation, communication, analytics, coaching, content
from app.routers import ai_analysis, ocr, nutrition

# Load environment variables
load_dotenv()

# Create the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to database
    print("Starting up API server...")
    await connect_to_db()
    yield
    # Shutdown: Disconnect from database
    print("Shutting down API server...")
    await disconnect_from_db()

# Create FastAPI app with lifespan
app = FastAPI(
    title="Trainer's Memory API",
    description="API for personal trainers to manage clients and workouts",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost:3000",     # Next.js frontend
    "http://127.0.0.1:3000",     # Alternative localhost
    "http://localhost:8000",     # FastAPI backend (for docs)
    "http://127.0.0.1:8000",     # Alternative localhost
    # Add any other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # 24 hours
)

# Add API key authentication scheme
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Add a simple health check endpoint at root
@app.get("/")
async def root():
    return {"message": "Trainer's Memory API is running", "version": API_VERSION}

# Add a simple health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}

# Demo endpoint with authentication - using the alternative validation method for better Swagger UI compatibility
@app.get(f"/api/{API_VERSION}/me", tags=["Authentication"])
async def get_my_info(client_info: Dict[str, Any] = Depends(validate_api_key)):
    """Return the client information associated with the API key."""
    return StandardResponse.success(client_info)

# Add token refresh endpoint
@app.post(f"/api/{API_VERSION}/auth/refresh", tags=["Authentication"])
async def refresh_jwt_token(request: Request):
    """Refresh an expired JWT token using a valid refresh token.
    
    The refresh token must be provided in the Refresh-Token header.
    """
    try:
        result = await refresh_token(request)
        return StandardResponse.success(result)
    except HTTPException as e:
        return StandardResponse.error(e.detail, e.status_code)

# Add user role information endpoint
@app.get(f"/api/{API_VERSION}/auth/user", tags=["Authentication"])
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """Get the current user's information and permissions."""
    return StandardResponse.success({
        "user_id": current_user.get("id"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "permissions": current_user.get("permissions", [])
    })

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Trainer's Memory API",
        version=API_VERSION,
        description="API for personal trainers to manage clients and workouts",
        routes=app.routes,
    )
    
    # Add security scheme for API key
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
        
    # Define security scheme
    openapi_schema["components"]["securitySchemes"] = {
        API_KEY_NAME: {
            "type": "apiKey",
            "in": "header",
            "name": API_KEY_NAME,
            "description": "API Key Authentication. Enter API key as-is without any prefix.",
        }
    }
    
    # Apply security to ALL operations explicitly
    # This ensures every endpoint requires the API key
    if "paths" in openapi_schema:
        for path_key, path in openapi_schema["paths"].items():
            for operation_key, operation in path.items():
                if "security" not in operation:
                    operation["security"] = [{API_KEY_NAME: []}]
    
    # Also keep the global security definition
    openapi_schema["security"] = [{API_KEY_NAME: []}]
    
    # Make sure the schemas section exists
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
    # Add custom schema info
    openapi_schema["info"]["contact"] = {
        "name": "Trainer's Memory Support",
        "email": "support@trainersmemory.api",
        "url": "https://trainersmemory.api/support",
    }
    
    # Update API documentation with markdown formatting
    openapi_schema["info"]["description"] = """
## API for personal trainers to manage clients and workouts

### Authentication
All endpoints require an API key to be provided in the `X-API-Key` header.

#### Testing with Swagger UI
1. Click the "Authorize" button at the top
2. Enter your API key **exactly as-is** (e.g., `tmk_40af9844458144dc9ba5f5859c8b0f01`)
3. Click "Authorize" and then "Close"
4. Now you can test the endpoints

#### Testing with cURL
```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/api/v1/me
```

### Available Endpoints
- `/api/v1/clients` - Client management
- `/api/v1/workouts` - Workout tracking and management
- `/api/v1/intelligence` - AI-powered analytics and insights
- `/api/v1/transformation` - Data transformation services
- `/api/v1/communication` - Client communication tools
- `/api/v1/analytics` - Business analytics
- `/api/v1/coaching` - AI coaching assistance
- `/api/v1/content` - Content generation
- `/api/v1/nutrition` - Meal plans and nutrition analysis
"""
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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

app.include_router(
    nutrition.router,
    prefix=f"/api/{API_VERSION}/nutrition",
    tags=["Nutrition"],
)

# Entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 