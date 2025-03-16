import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
import logging
import uuid

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

# Define a simple APIKey class for testing
class APIKey:
    def __init__(self, id, key, client_id, name, active):
        self.id = id
        self.key = key
        self.client_id = client_id
        self.name = name
        self.active = active

async def get_api_key_by_key(session, key):
    """Simplified version of the AsyncAPIKeyRepository.get_by_key method."""
    try:
        # Execute a raw SQL query to get the API key
        result = await session.execute(
            text(f"SELECT id, key, client_id, name, active FROM api_keys WHERE key = :key AND active = true")
            .bindparams(key=key)
        )
        row = result.fetchone()
        
        if row:
            logger.info(f"Found API key: {row}")
            return APIKey(
                id=row[0],
                key=row[1],
                client_id=row[2],
                name=row[3],
                active=row[4]
            )
        else:
            logger.warning(f"API key not found: {key}")
            return None
    except Exception as e:
        logger.error(f"Error getting API key: {str(e)}")
        return None

async def main():
    logger.info(f"Testing API key validation with database: {ASYNC_DB_URI}")
    
    # Create async engine and session
    engine = create_async_engine(ASYNC_DB_URI)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with engine.begin() as conn:
        # Test the connection
        result = await conn.execute(text("SELECT 1"))
        logger.info(f"Connection test result: {result.fetchone()}")
    
    # Test API key validation
    async with async_session() as session:
        # Test with valid API key
        api_key = await get_api_key_by_key(session, "test_key_12345")
        if api_key:
            logger.info(f"API key validated successfully: {api_key.key}")
            logger.info(f"Client ID: {api_key.client_id}")
        else:
            logger.error("API key validation failed")
    
    logger.info("API key validation test completed")

if __name__ == "__main__":
    asyncio.run(main()) 