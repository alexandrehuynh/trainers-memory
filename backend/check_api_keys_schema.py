import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging
import argparse

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

def check_schema(fix=False):
    """
    Check the schema of the api_keys table and optionally fix issues.
    
    Args:
        fix: If True, attempt to fix any schema issues found
    """
    logger.info(f"Checking schema of api_keys table in database: {DB_URI.replace('postgres://', 'postgresql://')}")
    engine = create_engine(DB_URI.replace("postgres://", "postgresql://"))
    
    try:
        # Create a connection
        with engine.connect() as conn:
            # Check if api_keys table exists
            logger.info("Checking if api_keys table exists...")
            table_exists = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'api_keys')"
            )).scalar()
            
            if not table_exists:
                logger.error("api_keys table does not exist!")
                return
            
            logger.info("api_keys table exists - checking schema...")
            
            # Check the schema of the api_keys table
            result = conn.execute(text(
                "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'api_keys'"
            ))
            columns = [(row[0], row[1], row[2]) for row in result.fetchall()]
            logger.info(f"Columns in api_keys table: {columns}")
            
            # Check for required columns
            required_columns = {
                'id': 'uuid',
                'key': 'character varying',
                'client_id': 'uuid',
                'name': 'character varying',
                'active': 'boolean',
                'created_at': 'timestamp without time zone',
                'user_id': 'uuid'
            }
            
            missing_columns = []
            for col_name, col_type in required_columns.items():
                col_exists = any(col[0] == col_name for col in columns)
                if not col_exists:
                    missing_columns.append((col_name, col_type))
                    logger.warning(f"Missing required column: {col_name} ({col_type})")
            
            # Check if we need to add the user_id column
            user_id_exists = any(col[0] == 'user_id' for col in columns)
            if not user_id_exists and fix:
                logger.info("Adding missing user_id column...")
                try:
                    # Add user_id column
                    conn.execute(text("ALTER TABLE api_keys ADD COLUMN user_id UUID"))
                    
                    # Add foreign key constraint
                    conn.execute(text(
                        "ALTER TABLE api_keys ADD CONSTRAINT fk_api_keys_user_id "
                        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
                    ))
                    
                    # Add index
                    conn.execute(text("CREATE INDEX ix_api_keys_user_id ON api_keys(user_id)"))
                    
                    # Update existing keys with the admin user ID
                    conn.execute(text(
                        "UPDATE api_keys SET user_id = '00000000-0000-0000-0000-000000000001' WHERE user_id IS NULL"
                    ))
                    
                    # Make user_id not nullable
                    conn.execute(text("ALTER TABLE api_keys ALTER COLUMN user_id SET NOT NULL"))
                    
                    logger.info("Successfully added user_id column to api_keys table")
                except Exception as e:
                    logger.error(f"Error adding user_id column: {str(e)}")
            
            # Check indexes on api_keys table
            logger.info("Checking indexes on api_keys table...")
            result = conn.execute(text(
                "SELECT indexname FROM pg_indexes WHERE tablename = 'api_keys'"
            ))
            indexes = [row[0] for row in result.fetchall()]
            logger.info(f"Indexes on api_keys table: {indexes}")
            
            required_indexes = [
                'api_keys_pkey',
                'ix_api_keys_key',
                'ix_api_keys_client_id',
                'ix_api_keys_user_id'
            ]
            
            for idx in required_indexes:
                if idx not in indexes:
                    logger.warning(f"Missing index: {idx}")
            
            # Check the data in the api_keys table
            logger.info("Checking data in api_keys table...")
            
            try:
                # Try to select with user_id first
                result = conn.execute(text("SELECT id, key, client_id, user_id, name, active FROM api_keys LIMIT 5"))
                rows = result.fetchall()
            except Exception:
                # Fall back to select without user_id
                logger.warning("Could not select user_id column, trying without it...")
                result = conn.execute(text("SELECT id, key, client_id, name, active FROM api_keys LIMIT 5"))
                rows = result.fetchall()
            
            if rows:
                logger.info(f"Found {len(rows)} rows in api_keys table")
                logger.info(f"Sample first row: {rows[0]}")
                logger.info(f"Column names: {result.keys()}")
                
                # Count total records
                count = conn.execute(text("SELECT COUNT(*) FROM api_keys")).scalar()
                logger.info(f"Total records in api_keys table: {count}")
                
                # Check for NULL values in important columns
                null_client_id = conn.execute(text("SELECT COUNT(*) FROM api_keys WHERE client_id IS NULL")).scalar()
                if null_client_id > 0:
                    logger.warning(f"Found {null_client_id} records with NULL client_id")
                
                if user_id_exists:
                    null_user_id = conn.execute(text("SELECT COUNT(*) FROM api_keys WHERE user_id IS NULL")).scalar()
                    if null_user_id > 0:
                        logger.warning(f"Found {null_user_id} records with NULL user_id")
                        
                        if fix:
                            logger.info("Updating records with NULL user_id...")
                            conn.execute(text(
                                "UPDATE api_keys SET user_id = '00000000-0000-0000-0000-000000000001' WHERE user_id IS NULL"
                            ))
                            logger.info("Updated NULL user_id values with default admin user")
            else:
                logger.warning("No data found in api_keys table")
            
            logger.info("Schema check completed successfully")
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Check the schema of the api_keys table and optionally fix issues.')
    parser.add_argument('--fix', action='store_true', help='Fix any schema issues found')
    args = parser.parse_args()
    
    check_schema(fix=args.fix)

if __name__ == "__main__":
    main() 