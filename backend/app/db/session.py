"""
Database session management.

This module provides functions for creating and managing database sessions.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from .config import ASYNC_DATABASE_URL, AsyncSessionLocal, async_engine

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
test_async_session_factory = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def get_async_session():
    """
    Get an async database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def get_test_async_session():
    """
    Get an async test database session.
    
    Yields:
        AsyncSession: Test database session
    """
    async with test_async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_test_db():
    """
    Initialize the test database.
    
    Creates all tables in the test database.
    """
    from .base import Base
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 