from fastapi import FastAPI, Depends, HTTPException, Security, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

# Import StandardResponse from utils
from app.utils.response import StandardResponse, API_VERSION

# Import database components
from app.db import connect_to_db, disconnect_from_db, AsyncAPIKeyRepository, get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

# Import authentication utilities
from app.auth import get_current_user, refresh_token, verify_user_role, verify_permission

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
print("Loading API keys from environment variables...")
for env_key, env_value in os.environ.items():
    if env_key.startswith("TRAINERS_MEMORY_API_KEY_"):
        client_name = env_key.replace("TRAINERS_MEMORY_API_KEY_", "").lower()
        API_KEYS[env_value] = {"client": client_name, "created": datetime.now().isoformat()}
        print(f"Loaded API key for client: {client_name} with key: {env_value[:4]}...")

# For demo purposes, create a test key if none exists
if not API_KEYS:
    print("No API keys found in environment, creating a test key...")
    test_key = "test_key_12345"
    API_KEYS[test_key] = {"client": "test", "created": datetime.now().isoformat()}
    print(f"Created test API key: {test_key}")

print(f"Available API Keys: {list(API_KEYS.keys())}")
print(f"Total API keys loaded: {len(API_KEYS)}")

async def get_api_key(
    request: Request, 
    api_key_header_value: Optional[str] = Header(None, alias=API_KEY_NAME),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Validate the API key and return client info."""
    print(f"API Key from header: {api_key_header_value}")
    
    # Debug request headers
    print("All request headers:")
    for name, value in request.headers.items():
        if name.lower() != "authorization":  # Don't show auth in logs
            print(f"  {name}: {value}")
    
    # Check for API key in header with case-insensitive match
    api_key = api_key_header_value
    if not api_key:
        for k, v in request.headers.items():
            if k.lower() == API_KEY_NAME.lower():
                api_key = v
                print(f"Found API key in headers with different case: {k}")
                break
    
    if not api_key:
        print("API Key is None or not found in headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header is missing",
            headers={"WWW-Authenticate": API_KEY_NAME},
        )
    
    # Check if key exists in database
    api_key_repo = AsyncAPIKeyRepository(db)
    api_key_record = await api_key_repo.get_by_key(api_key)
    
    # Fall back to environment variables during development/migration
    client_info = None
    if not api_key_record and api_key in API_KEYS:
        print(f"API key found in environment variables: {api_key}")
        client_info = API_KEYS[api_key]
    elif api_key_record:
        print(f"API key found in database: {api_key}")
        # Update last used timestamp
        await api_key_repo.update(api_key_record.id, {"last_used_at": datetime.utcnow()})
        # Return client info
        client_info = {
            "client_id": str(api_key_record.client_id),
            "key_id": str(api_key_record.id),
            "name": api_key_record.name,
            "created": api_key_record.created_at.isoformat()
        }
    
    if not client_info:
        print(f"API Key {api_key} is not valid")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": API_KEY_NAME},
        )
    
    print(f"API Key {api_key} is valid")
    return client_info

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

# Test endpoint without authentication
@app.get("/api/v1/test-auth", tags=["Authentication"])
async def test_auth(request: Request):
    """Test endpoint for API key authentication without requiring it."""
    # Print all headers for debugging
    print("Debug headers in test-auth endpoint:")
    headers_dict = {}
    for name, value in request.headers.items():
        if name.lower() != "authorization":  # Don't show auth data
            print(f"  {name}: {value}")
            headers_dict[name] = value
    
    # Check for API key in any of the headers
    api_key = None
    for name, value in request.headers.items():
        if name.lower() == API_KEY_NAME.lower():
            api_key = value
            break
    
    return {
        "message": "Test authentication endpoint",
        "api_key_found": api_key is not None,
        "api_key_length": len(api_key) if api_key else 0,
        "api_key_valid": api_key in API_KEYS if api_key else False,
        "api_key_name_checking": API_KEY_NAME,
        "headers": headers_dict,
        "available_keys": list(API_KEYS.keys())
    }

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
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
        
    openapi_schema["components"]["securitySchemes"] = {
        API_KEY_NAME: {
            "type": "apiKey",
            "in": "header",
            "name": API_KEY_NAME,
            "description": "API Key Authentication",
        }
    }
    
    # Make sure the schemas section exists
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
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

# Register startup and shutdown events
@app.on_event("startup")
async def startup():
    """Run startup tasks."""
    print("Starting up the application...")
    await connect_to_db()
    print("Connected to database")

@app.on_event("shutdown")
async def shutdown():
    """Run shutdown tasks."""
    print("Shutting down the application...")
    await disconnect_from_db()
    print("Disconnected from database")

# Entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 