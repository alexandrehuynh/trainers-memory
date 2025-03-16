import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URI from environment
DB_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/trainers_memory")

def main():
    print(f"Connecting to database: {DB_URI.replace('postgres://', 'postgresql://')}")
    engine = create_engine(DB_URI.replace("postgres://", "postgresql://"))
    
    # Create a connection
    with engine.begin() as conn:
        # Check if users table exists
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users'"
        ))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("Creating users table...")
            conn.execute(text("""
                CREATE TABLE public.users (
                    id UUID PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    hashed_password VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'trainer',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP
                )
            """))
            conn.execute(text(
                "CREATE INDEX ix_users_email ON public.users (email)"
            ))
            
            # Insert default admin user
            conn.execute(text("""
                INSERT INTO public.users (id, email, role, is_active, created_at) 
                VALUES ('00000000-0000-0000-0000-000000000001', 'admin@trainersmemory.com', 'admin', TRUE, now())
            """))
            print("users table created successfully")
        else:
            print("users table already exists")
        
        # Check if clients table exists
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'clients'"
        ))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("Creating clients table...")
            conn.execute(text("""
                CREATE TABLE public.clients (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    phone VARCHAR(20),
                    notes TEXT,
                    api_key VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP
                )
            """))
            conn.execute(text(
                "CREATE INDEX ix_clients_email ON public.clients (email)"
            ))
            conn.execute(text(
                "CREATE INDEX ix_clients_name ON public.clients (name)"
            ))
            conn.execute(text(
                "CREATE INDEX ix_clients_user_id ON public.clients (user_id)"
            ))
            conn.execute(text(
                "CREATE UNIQUE INDEX uq_client_email_per_user ON public.clients (user_id, email)"
            ))
            print("clients table created successfully")
            
            # Insert test client
            conn.execute(text("""
                INSERT INTO public.clients (id, user_id, name, email, phone, created_at) 
                VALUES ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Test Client', 'testclient@example.com', '555-1234', now())
            """))
            print("Added test client")
        else:
            print("clients table already exists")
            
        # Check if workouts table exists
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'workouts'"
        ))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("Creating workouts table...")
            conn.execute(text("""
                CREATE TABLE public.workouts (
                    id UUID PRIMARY KEY,
                    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
                    date TIMESTAMP NOT NULL,
                    type VARCHAR(255) NOT NULL,
                    duration INTEGER NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP
                )
            """))
            conn.execute(text(
                "CREATE INDEX ix_workouts_client_id ON public.workouts (client_id)"
            ))
            conn.execute(text(
                "CREATE INDEX ix_workouts_date ON public.workouts (date)"
            ))
            print("workouts table created successfully")
        else:
            print("workouts table already exists")
            
        # Check if exercises table exists
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'exercises'"
        ))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("Creating exercises table...")
            conn.execute(text("""
                CREATE TABLE public.exercises (
                    id UUID PRIMARY KEY,
                    workout_id UUID NOT NULL REFERENCES public.workouts(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    sets INTEGER NOT NULL,
                    reps INTEGER NOT NULL,
                    weight FLOAT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP
                )
            """))
            conn.execute(text(
                "CREATE INDEX ix_exercises_workout_id ON public.exercises (workout_id)"
            ))
            print("exercises table created successfully")
        else:
            print("exercises table already exists")
            
        # Check if api_keys table exists
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'api_keys'"
        ))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("Creating api_keys table...")
            conn.execute(text("""
                CREATE TABLE public.api_keys (
                    id UUID PRIMARY KEY,
                    key VARCHAR(255) NOT NULL UNIQUE,
                    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    last_used_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """))
            conn.execute(text(
                "CREATE INDEX ix_api_keys_key ON public.api_keys (key)"
            ))
            conn.execute(text(
                "CREATE INDEX ix_api_keys_client_id ON public.api_keys (client_id)"
            ))
            conn.execute(text(
                "CREATE INDEX ix_api_keys_user_id ON public.api_keys (user_id)"
            ))
            
            # Add test API key
            conn.execute(text("""
                INSERT INTO public.api_keys (id, key, client_id, user_id, name, description, active, created_at)
                VALUES ('00000000-0000-0000-0000-000000000099', 'test_key_12345', '00000000-0000-0000-0000-000000000001', 
                '00000000-0000-0000-0000-000000000001', 'Test API Key', 'For development and testing', true, NOW())
            """))
            print("api_keys table created successfully with test key")
        else:
            print("api_keys table already exists")
        
        # Check if workout_templates table exists
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'workout_templates'"
        ))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("Creating workout_templates table...")
            conn.execute(text("""
                CREATE TABLE public.workout_templates (
                    id UUID PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    type VARCHAR(255) NOT NULL,
                    duration INTEGER NOT NULL,
                    is_system BOOLEAN NOT NULL DEFAULT FALSE,
                    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP
                )
            """))
            print("workout_templates table created successfully")
        else:
            print("workout_templates table already exists")
        
        # Check if template_exercises table exists
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'template_exercises'"
        ))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("Creating template_exercises table...")
            conn.execute(text("""
                CREATE TABLE public.template_exercises (
                    id UUID PRIMARY KEY,
                    template_id UUID NOT NULL REFERENCES public.workout_templates(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    sets INTEGER NOT NULL,
                    reps INTEGER NOT NULL,
                    weight FLOAT,
                    notes TEXT
                )
            """))
            conn.execute(text(
                "CREATE INDEX ix_template_exercises_template_id ON public.template_exercises (template_id)"
            ))
            print("template_exercises table created successfully")
        else:
            print("template_exercises table already exists")
            
            # Check if index exists on template_id column
            result = conn.execute(text(
                "SELECT 1 FROM pg_indexes WHERE indexname = 'ix_template_exercises_template_id'"
            ))
            index_exists = result.fetchone() is not None
            
            if not index_exists:
                print("Creating index on template_exercises.template_id...")
                conn.execute(text(
                    "CREATE INDEX ix_template_exercises_template_id ON public.template_exercises (template_id)"
                ))
                print("Index created successfully")
            else:
                print("Index already exists")
        
        print("Database schema updated successfully")

if __name__ == "__main__":
    main() 