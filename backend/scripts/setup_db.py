#!/usr/bin/env python
"""
Database setup script.

This script initializes the database, creates tables, and loads initial data.
Run this script before starting the application to ensure the database is set up correctly.

Usage:
    python scripts/setup_db.py [--create-db] [--seed]

Options:
    --create-db  Create the database if it doesn't exist (requires admin rights)
    --seed       Seed the database with initial data
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Get database connection details from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "trainers_memory")

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to PostgreSQL default database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.autocommit = True
        
        # Check if database exists
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            if cursor.fetchone():
                print(f"Database '{DB_NAME}' already exists. Skipping creation.")
                return
        
        # Create database
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
        
        print(f"Database '{DB_NAME}' created successfully.")
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)
    finally:
        conn.close()

def run_migrations():
    """Run database migrations using Alembic."""
    try:
        # Change to the backend directory
        os.chdir(Path(__file__).parent.parent)
        
        # Run Alembic migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        
        print("Migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)

def seed_database():
    """Seed the database with initial data."""
    # Add code to seed database with initial data
    try:
        # Import database models and session
        from app.db.config import SessionLocal
        from app.db.models import Client, APIKey
        import uuid
        from datetime import datetime
        
        # Create a database session
        db = SessionLocal()
        
        try:
            # Check if clients exist
            if db.query(Client).count() > 0:
                print("Database already has clients. Skipping seeding.")
                return
            
            # Create test client
            test_client = Client(
                id=uuid.uuid4(),
                name="Test Client",
                email="test@example.com",
                phone="555-123-4567",
                notes="Test client for development",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(test_client)
            db.flush()
            
            # Create API key for test client
            test_api_key = APIKey(
                id=uuid.uuid4(),
                key="test123",
                client_id=test_client.id,
                name="Test API Key",
                description="API key for testing",
                active=True,
                created_at=datetime.utcnow()
            )
            db.add(test_api_key)
            
            # Commit changes
            db.commit()
            
            print(f"Database seeded successfully with test client: {test_client.name}")
            print(f"API Key: {test_api_key.key}")
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    except Exception as e:
        print(f"Error seeding database: {e}")
        sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Database setup script")
    parser.add_argument("--create-db", action="store_true", help="Create database if it doesn't exist")
    parser.add_argument("--seed", action="store_true", help="Seed database with initial data")
    
    args = parser.parse_args()
    
    # Create database if requested
    if args.create_db:
        create_database()
    
    # Run migrations
    run_migrations()
    
    # Seed database if requested
    if args.seed:
        seed_database()
    
    print("Database setup completed successfully.")

if __name__ == "__main__":
    main() 