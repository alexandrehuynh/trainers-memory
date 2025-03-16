"""
Fix the missing user_id column in the clients table.

This script adds the user_id column to the clients table if it doesn't exist,
and sets all existing clients to be owned by the admin user.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import uuid

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
    """Main function to fix the database schema."""
    print(f"Connecting to database: {PG_URL.split('@')[1] if '@' in PG_URL else PG_URL}")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(PG_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users')")
        users_exists = cursor.fetchone()[0]
        
        # Create users table if it doesn't exist
        if not users_exists:
            print("Creating users table...")
            cursor.execute("""
                CREATE TABLE public.users (
                    id UUID PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    hashed_password VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'trainer',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE
                )
            """)
            
            # Create index on email
            cursor.execute("CREATE INDEX ix_users_email ON public.users (email)")
            
            # Add admin user
            admin_id = "00000000-0000-0000-0000-000000000001"
            cursor.execute("""
                INSERT INTO public.users (id, email, role, is_active, created_at)
                VALUES (%s, 'admin@trainersmemory.com', 'admin', TRUE, NOW())
            """, (admin_id,))
            
            print("Created users table and added admin user")
        else:
            # Get admin user ID
            cursor.execute("SELECT id FROM public.users WHERE role = 'admin' LIMIT 1")
            result = cursor.fetchone()
            admin_id = result[0] if result else uuid.uuid4()
            print(f"Using admin user ID: {admin_id}")
        
        # Check if user_id column exists in clients table
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'clients' AND column_name = 'user_id')")
        user_id_exists = cursor.fetchone()[0]
        
        if not user_id_exists:
            print("Adding user_id column to clients table...")
            
            # Add user_id column
            cursor.execute("ALTER TABLE public.clients ADD COLUMN user_id UUID")
            
            # Create index
            cursor.execute("CREATE INDEX ix_clients_user_id ON public.clients (user_id)")
            
            # Set all existing clients to admin user
            cursor.execute("UPDATE public.clients SET user_id = %s", (admin_id,))
            
            # Make user_id not nullable
            cursor.execute("ALTER TABLE public.clients ALTER COLUMN user_id SET NOT NULL")
            
            # Add foreign key constraint
            cursor.execute("""
                ALTER TABLE public.clients
                ADD CONSTRAINT fk_clients_user_id
                FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
            """)
            
            # Add unique constraint for email per user
            cursor.execute("""
                ALTER TABLE public.clients
                ADD CONSTRAINT uq_client_email_per_user
                UNIQUE (user_id, email)
            """)
            
            print("Successfully added user_id column to clients table")
        else:
            print("user_id column already exists in clients table")
        
        # Check if user_id column exists in api_keys table
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'user_id')")
        api_key_user_id_exists = cursor.fetchone()[0]
        
        if not api_key_user_id_exists:
            print("Adding user_id column to api_keys table...")
            
            # Add user_id column
            cursor.execute("ALTER TABLE public.api_keys ADD COLUMN user_id UUID")
            
            # Create index
            cursor.execute("CREATE INDEX ix_api_keys_user_id ON public.api_keys (user_id)")
            
            # Set all existing API keys to admin user
            cursor.execute("UPDATE public.api_keys SET user_id = %s", (admin_id,))
            
            # Make user_id not nullable
            cursor.execute("ALTER TABLE public.api_keys ALTER COLUMN user_id SET NOT NULL")
            
            # Add foreign key constraint
            cursor.execute("""
                ALTER TABLE public.api_keys
                ADD CONSTRAINT fk_api_keys_user_id
                FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
            """)
            
            print("Successfully added user_id column to api_keys table")
        else:
            print("user_id column already exists in api_keys table")
        
        # Update alembic_version table to mark the migration as applied
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version')")
        alembic_exists = cursor.fetchone()[0]
        
        if alembic_exists:
            cursor.execute("SELECT version_num FROM public.alembic_version")
            current_version = cursor.fetchone()[0]
            
            if current_version == '062832f6fa7c':
                print("Updating alembic_version to mark user isolation migration as applied...")
                cursor.execute("UPDATE public.alembic_version SET version_num = 'f2b1c25117bf'")
                print("Successfully updated alembic_version")
            else:
                print(f"Current alembic version is {current_version}, not updating")
        
        print("Database schema fix completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 