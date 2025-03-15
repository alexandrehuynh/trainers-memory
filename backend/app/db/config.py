"""
Database configuration and connection handling.

This module handles database connection and session management,
providing both synchronous and asynchronous access patterns.
"""

import os
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from databases import Database
from dotenv import load_dotenv
from functools import lru_cache
import getpass

load_dotenv()

# PostgreSQL configuration
# Check for a full DATABASE_URL first (common in deployment environments like Render)
PG_URL = os.getenv("DATABASE_URL")
if not PG_URL:
    # If no DATABASE_URL is provided, build from components
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "trainers_memory")
    # Use your system username as the default instead of 'postgres'
    current_user = getpass.getuser()
    DB_USER = os.getenv("DB_USER", current_user)
    DB_PASS = os.getenv("DB_PASS", "")  # Empty password as default
    PG_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Derive the async URL from standard PostgreSQL URL
ASYNC_PG_URL = PG_URL.replace("postgresql://", "postgresql+asyncpg://")

# Print for debugging
# Mask password in logs for security
masked_url = PG_URL
if ":" in PG_URL and "@" in PG_URL:
    parts = PG_URL.split("@")
    credentials = parts[0].split(":")
    if len(credentials) > 1:
        masked_url = f"{credentials[0]}:******@{parts[1]}"
print(f"Using PostgreSQL connection: {masked_url}")

# Set the database URLs
DATABASE_URL = PG_URL
ASYNC_DATABASE_URL = ASYNC_PG_URL

# Create database engines
engine = create_engine(DATABASE_URL)
async_engine = create_async_engine(ASYNC_DATABASE_URL)

# Create session factories
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    future=True  # Use the SQLAlchemy 2.0 API
)

AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    future=True,  # Use the SQLAlchemy 2.0 API
    expire_on_commit=False  # Prevents errors when accessing attributes after commit
)

# Initialize database connection
database = Database(ASYNC_DATABASE_URL)

# Base class for SQLAlchemy models
Base = declarative_base()

# SQLAlchemy convention for naming constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)

# Dependency functions for FastAPI
@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get a synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        yield session

# Connect and disconnect methods for startup/shutdown events
@lru_cache
def database():
    """Get a database connection."""
    return {"engine": engine, "async_engine": async_engine}

async def connect_to_db():
    """Connect to database on app startup."""
    print("Connecting to PostgreSQL database...")
    
    try:
        # Test connection by making a simple query
        conn = await database()["async_engine"].connect()
        
        # Test a simple query to see if the database is working
        await conn.execute("SELECT 1")
        print("PostgreSQL connection test successful")
        
        # Create tables if they don't exist yet
        from app.db.models import Client, Workout, Exercise, APIKey
        
        # Use create_all to create tables that don't exist yet
        # This is safe to call even if tables already exist
        print("Ensuring database tables exist...")
        Base.metadata.create_all(bind=engine)
        print("Database tables verified/created")
        
    except Exception as e:
        print(f"PostgreSQL connection error: {str(e)}")
        raise  # Re-raise the exception to fail startup

async def disconnect_from_db():
    """Disconnect from database on app shutdown."""
    print("Disconnecting from database...")
    
    try:
        # Dispose the async engine
        await database()["async_engine"].dispose()
        print("Disposed PostgreSQL connection pool")
    except Exception as e:
        print(f"Error disconnecting from PostgreSQL: {str(e)}")
    
    # Always dispose the sync engine to be safe
    engine.dispose()
    print("Disconnected from database") 