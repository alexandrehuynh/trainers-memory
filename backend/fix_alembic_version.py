"""
Fix the alembic_version table to mark all migrations as applied.

This script updates the alembic_version table to the latest migration version.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "trainers_memory")
DB_USER = os.getenv("DB_USER", os.getenv("USER", "postgres"))
DB_PASS = os.getenv("DB_PASS", "")

# Full connection string
PG_URL = os.getenv("DATABASE_URL")
if not PG_URL:
    PG_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def main():
    """Main function to fix the alembic_version table."""
    print(f"Connecting to database: {PG_URL.split('@')[1] if '@' in PG_URL else PG_URL}")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(PG_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if alembic_version table exists
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version')")
        alembic_exists = cursor.fetchone()[0]
        
        if alembic_exists:
            # Update alembic_version to the latest migration
            print("Updating alembic_version to the latest migration...")
            cursor.execute("UPDATE public.alembic_version SET version_num = '6163696ad6f4'")
            print("Successfully updated alembic_version to the latest migration")
        else:
            print("alembic_version table does not exist")
        
        print("Alembic version fix completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 