"""
Script to set up a test API key in the database.

This script creates a test API key that can be used for local development
and testing without requiring a real API key.
"""

import asyncio
import os
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URI from environment
DB_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/trainers_memory")
ASYNC_DB_URI = DB_URI.replace("postgresql://", "postgresql+asyncpg://")

# Define constants for the test data
TEST_API_KEY = "test_key_12345"
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_CLIENT_ID = "00000000-0000-0000-0000-000000000001"
TEST_API_KEY_ID = "00000000-0000-0000-0000-000000000099"

async def setup_test_api_key():
    """Set up a test API key in the database."""
    logger.info(f"Setting up test API key with database: {ASYNC_DB_URI}")
    
    # Create async engine and session
    engine = create_async_engine(ASYNC_DB_URI)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with engine.begin() as conn:
        # Test the connection
        result = await conn.execute(text("SELECT 1"))
        logger.info(f"Connection test result: {result.fetchone()}")
    
    # First, check if we need to create a test user
    async with async_session() as session:
        # Check if the test user exists
        user_query = text("""
            SELECT id FROM users WHERE id = :user_id
        """).bindparams(user_id=TEST_USER_ID)
        
        result = await session.execute(user_query)
        test_user = result.fetchone()
        
        if not test_user:
            logger.info("Creating test user...")
            # Create a test user
            create_user = text("""
                INSERT INTO users (id, email, first_name, last_name, role, created_at, updated_at)
                VALUES (:id, :email, :first_name, :last_name, :role, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """).bindparams(
                id=TEST_USER_ID,
                email="test@trainersmemory.api",
                first_name="Test",
                last_name="User",
                role="admin"
            )
            await session.execute(create_user)
            await session.commit()
            logger.info("Test user created successfully.")
        else:
            logger.info("Test user already exists.")
    
    # Next, check if we need to create a test client
    async with async_session() as session:
        # Check if the test client exists
        client_query = text("""
            SELECT id FROM clients WHERE id = :client_id
        """).bindparams(client_id=TEST_CLIENT_ID)
        
        result = await session.execute(client_query)
        test_client = result.fetchone()
        
        if not test_client:
            logger.info("Creating test client...")
            # Create a test client
            create_client = text("""
                INSERT INTO clients (id, name, email, phone, notes, user_id, created_at, updated_at)
                VALUES (:id, :name, :email, :phone, :notes, :user_id, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """).bindparams(
                id=TEST_CLIENT_ID,
                name="Test Client",
                email="testclient@example.com",
                phone="555-123-4567",
                notes="Test client for development",
                user_id=TEST_USER_ID
            )
            await session.execute(create_client)
            await session.commit()
            logger.info("Test client created successfully.")
        else:
            logger.info("Test client already exists.")
    
    # Finally, set up the test API key
    async with async_session() as session:
        # Check if the test API key exists
        api_key_query = text("""
            SELECT id FROM api_keys WHERE key = :key
        """).bindparams(key=TEST_API_KEY)
        
        result = await session.execute(api_key_query)
        existing_key = result.fetchone()
        
        if not existing_key:
            logger.info("Creating test API key...")
            # Create the test API key
            create_api_key = text("""
                INSERT INTO api_keys (id, key, client_id, user_id, name, description, active, created_at)
                VALUES (:id, :key, :client_id, :user_id, :name, :description, :active, NOW())
                ON CONFLICT (key) DO UPDATE SET
                    client_id = :client_id,
                    user_id = :user_id,
                    name = :name,
                    description = :description,
                    active = :active
            """).bindparams(
                id=TEST_API_KEY_ID,
                key=TEST_API_KEY,
                client_id=TEST_CLIENT_ID,
                user_id=TEST_USER_ID,
                name="Test API Key",
                description="API key for local development and testing",
                active=True
            )
            await session.execute(create_api_key)
            await session.commit()
            logger.info("Test API key created/updated successfully.")
        else:
            logger.info("Test API key already exists.")
    
    logger.info("Test API key setup completed.")

if __name__ == "__main__":
    asyncio.run(setup_test_api_key()) 