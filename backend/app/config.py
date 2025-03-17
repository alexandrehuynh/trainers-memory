"""
Application configuration.

This module contains settings for the application.
"""

import os
from pydantic import BaseModel
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Settings(BaseModel):
    """Application settings."""
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/trainers_memory")
    
    # API settings
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS settings
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    
    # Supabase settings (optional)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

# Create settings instance
settings = Settings()

# Log configuration on startup
def log_settings():
    """Log application settings."""
    # Hide sensitive information
    safe_settings = settings.dict()
    for key in ["JWT_SECRET_KEY", "SUPABASE_KEY", "SUPABASE_JWT_SECRET"]:
        if safe_settings.get(key):
            safe_settings[key] = "***REDACTED***"
    
    logger.info(f"Application settings: {safe_settings}")

# Call log_settings on import
log_settings() 