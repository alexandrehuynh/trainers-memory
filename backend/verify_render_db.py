#!/usr/bin/env python
"""
Render PostgreSQL Connection Verification Script

This script verifies the connection to the Render PostgreSQL database
and displays information about the database schema.

Usage:
    python verify_render_db.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check environment and database settings
logger.info("Checking environment configuration:")
logger.info(f"- NODE_ENV: {os.environ.get('NODE_ENV', 'not set')}")
logger.info(f"- RENDER: {os.environ.get('RENDER', 'not set')}")
logger.info(f"- DATABASE_URL set: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")

# Get database URI - explicitly use the Render database
RENDER_DB_URI = "postgresql://trainers_memory_db_user:xDWN1zAK0WzWKJzj0rSSb3q9CMgQpBjm@dpg-cvadma7noe9s73f7ojag-a/trainers_memory_db"
LOCAL_DB_URI = "postgresql://postgres:postgres@localhost:5432/trainers_memory"

def test_database_connection(uri, label):
    """Test connection to a specific database URI"""
    logger.info(f"\nTesting connection to {label} database...")
    
    # Mask password in logs
    masked_uri = uri
    if ":" in uri and "@" in uri:
        parts = uri.split("@")
        credentials = parts[0].split(":")
        if len(credentials) > 1:
            masked_uri = f"{credentials[0]}:******@{parts[1]}"
    logger.info(f"Database URI: {masked_uri}")
    
    try:
        # Create engine and connect
        engine = create_engine(uri.replace("postgres://", "postgresql://"))
        inspector = inspect(engine)
        
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT 1 AS test"))
            test_result = result.fetchone()[0]
            logger.info(f"Connection test result: {test_result}")
            
            # Get database schema info
            logger.info("Database tables:")
            tables = inspector.get_table_names()
            for table in tables:
                logger.info(f"- {table}")
                
            # Check for critical tables
            critical_tables = ['clients', 'workouts', 'exercises', 'api_keys']
            missing_tables = [table for table in critical_tables if table not in tables]
            
            if missing_tables:
                logger.warning(f"Missing critical tables: {', '.join(missing_tables)}")
            else:
                logger.info("All critical tables present")
                
            # Check api_keys table if it exists
            if 'api_keys' in tables:
                columns = [col['name'] for col in inspector.get_columns('api_keys')]
                logger.info(f"API Keys columns: {', '.join(columns)}")
                
                # Check for required columns
                required_columns = ['id', 'key', 'user_id', 'name', 'expires_at']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    logger.warning(f"API Keys table missing columns: {', '.join(missing_columns)}")
                else:
                    logger.info("API Keys table has all required columns")
                
                # Check for test key
                result = conn.execute(text("SELECT COUNT(*) FROM api_keys WHERE key = 'test_key_12345'"))
                count = result.fetchone()[0]
                logger.info(f"Test API key present: {'Yes' if count > 0 else 'No'}")
            
        return True
        
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return False

def main():
    """Main function to test database connections"""
    # Test Render database
    render_result = test_database_connection(RENDER_DB_URI, "Render")
    
    # Test local database for comparison
    local_result = test_database_connection(LOCAL_DB_URI, "local")
    
    # Summary
    logger.info("\nConnection Test Summary:")
    logger.info(f"- Render database: {'SUCCESS' if render_result else 'FAILED'}")
    logger.info(f"- Local database: {'SUCCESS' if local_result else 'FAILED'}")
    
    if render_result:
        logger.info("\nYour application should be able to connect to the Render database successfully.")
        logger.info("Make sure your DATABASE_URL environment variable is set correctly in your Render dashboard.")
    else:
        logger.error("\nUnable to connect to the Render database!")
        logger.error("Check your database credentials and network connectivity.")
    
    return 0 if render_result else 1

if __name__ == "__main__":
    sys.exit(main()) 