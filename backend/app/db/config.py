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

load_dotenv()

# Check if we're in development mode and should use SQLite
USE_SQLITE = os.getenv("USE_SQLITE", "False").lower() in ("true", "1", "t")

if USE_SQLITE:
    # SQLite configuration (for development)
    DATABASE_URL = "sqlite:///./test.db"
    ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
else:
    # PostgreSQL configuration (for production)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "trainers_memory")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASS", "postgres")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create database engines
if USE_SQLITE:
    # SQLite doesn't support some PostgreSQL-specific arguments
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        future=True,
    )
else:
    # PostgreSQL configuration
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
    await database()["async_engine"].connect()
    print("Connected to database")

async def disconnect_from_db():
    """Disconnect from database on app shutdown."""
    await database()["async_engine"].disconnect()
    engine.dispose()
    await database.disconnect() 