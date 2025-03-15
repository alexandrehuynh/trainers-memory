"""
Database initialization script

This script creates the SQLite database file and runs migrations.
"""

import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from alembic.config import Config
from alembic import command
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_sqlite_db():
    """Initialize the SQLite database file"""
    try:
        db_file = "./trainers_memory.db"
        logger.info(f"Creating SQLite database file at {db_file}")
        
        # Check if file exists
        if os.path.exists(db_file):
            logger.info(f"Database file already exists at {db_file}")
            return
        
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Create empty SQLite database file
        conn = sqlite3.connect(db_file)
        conn.close()
        logger.info("SQLite database file created successfully")
        
        # Create engine and run simple test
        engine = create_engine(f"sqlite:///{db_file}")
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("SQLite connection test successful")
        
        # Run Alembic migrations
        logger.info("Running database migrations...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        
        return True
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error initializing database: {e}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    return False

if __name__ == "__main__":
    if init_sqlite_db():
        logger.info("Database initialization completed successfully")
    else:
        logger.error("Database initialization failed") 