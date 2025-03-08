"""
Database configuration and connection handling.

This module handles database connection and session management,
providing both synchronous and asynchronous access patterns.
"""

import os
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from databases import Database
from dotenv import load_dotenv

load_dotenv()

# Database URLs (sync and async)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/trainers_memory"
)
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Create database engines
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
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
        try:
            yield session
        finally:
            await session.close()

# Connect and disconnect methods for startup/shutdown events
async def connect_to_db():
    """Connect to database on app startup."""
    await database.connect()

async def disconnect_from_db():
    """Disconnect from database on app shutdown."""
    await database.disconnect() 