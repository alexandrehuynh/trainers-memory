import os
from sqlalchemy import create_engine, text
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

def main():
    logger.info(f"Testing connection to database: {DB_URI.replace('postgres://', 'postgresql://')}")
    engine = create_engine(DB_URI.replace("postgres://", "postgresql://"))
    
    try:
        # Create a connection
        with engine.connect() as conn:
            # Test the connection
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Connection test result: {result.fetchone()}")
            
            # Check what tables exist
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Tables in database: {tables}")
            
            # Check if api_keys table exists and has data
            if 'api_keys' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM api_keys"))
                count = result.fetchone()[0]
                logger.info(f"Number of API keys: {count}")
                
                # Check the test API key
                result = conn.execute(text("SELECT * FROM api_keys WHERE key = 'test_key_12345'"))
                row = result.fetchone()
                if row:
                    logger.info(f"Found test API key: {row}")
                else:
                    logger.warning("Test API key not found")
            else:
                logger.warning("api_keys table does not exist")
            
            logger.info("Database connection test completed successfully")
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")

if __name__ == "__main__":
    main() 