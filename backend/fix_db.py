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
    with engine.connect() as conn:
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
            conn.commit()
            print("Index created successfully")
        else:
            print("Index already exists")
        
        print("Database schema updated successfully")

if __name__ == "__main__":
    main() 