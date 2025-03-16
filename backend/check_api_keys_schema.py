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
    logger.info(f"Checking schema of api_keys table in database: {DB_URI.replace('postgres://', 'postgresql://')}")
    engine = create_engine(DB_URI.replace("postgres://", "postgresql://"))
    
    try:
        # Create a connection
        with engine.connect() as conn:
            # Check the schema of the api_keys table
            result = conn.execute(text(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'api_keys'"
            ))
            columns = [(row[0], row[1]) for row in result.fetchall()]
            logger.info(f"Columns in api_keys table: {columns}")
            
            # Check the data in the api_keys table
            result = conn.execute(text("SELECT * FROM api_keys LIMIT 1"))
            row = result.fetchone()
            if row:
                logger.info(f"Sample row from api_keys table: {row}")
                logger.info(f"Column names: {result.keys()}")
            else:
                logger.warning("No data found in api_keys table")
            
            logger.info("Schema check completed successfully")
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")

if __name__ == "__main__":
    main() 