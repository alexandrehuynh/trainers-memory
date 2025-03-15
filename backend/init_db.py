"""
Database initialization script

This script creates the SQLite database file and runs migrations.
"""

import os
import sqlite3
import logging
from dotenv import load_dotenv

# Set USE_SQLITE environment variable before importing models
os.environ["USE_SQLITE"] = "True"

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from alembic.config import Config
from alembic import command
from app.db.config import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_sqlite_db():
    """Initialize the SQLite database file"""
    try:
        # Get database path from environment variable or use default
        database_url = os.getenv("SQLITE_URL", "sqlite:///./trainers_memory.db")
        
        # Extract the file path from the URL
        if "sqlite:///" in database_url:
            db_file = database_url.split("sqlite:///")[1]
        else:
            db_file = "./trainers_memory.db"
            
        logger.info(f"Database URL: {database_url}")
        logger.info(f"Creating SQLite database file at {db_file}")
        
        # Check if file exists
        if os.path.exists(db_file):
            logger.info(f"Database file already exists at {db_file}")
            return True
        
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            logger.info(f"Creating directory {db_dir}")
            os.makedirs(db_dir)
        
        # Create empty SQLite database file
        conn = sqlite3.connect(db_file)
        conn.close()
        logger.info("SQLite database file created successfully")
        
        # Create engine and run simple test
        engine = create_engine(database_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("SQLite connection test successful")
            
        # Create all tables from SQLAlchemy models
        logger.info("Creating database tables from SQLAlchemy models...")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        # Run Alembic migrations if needed
        try:
            logger.info("Running database migrations...")
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.warning(f"Error running migrations: {e}")
            logger.warning("Continuing without migrations since tables were created directly")
        
        return True
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error initializing database: {e}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Make sure USE_SQLITE is set
    os.environ["USE_SQLITE"] = "True"
    
    if init_sqlite_db():
        logger.info("Database initialization completed successfully")
    else:
        logger.error("Database initialization failed") 