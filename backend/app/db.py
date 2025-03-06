import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Missing Supabase environment variables. Please check your .env file."
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Helper functions for database operations
async def get_client_by_id(client_id: str):
    """Get client data by ID"""
    response = supabase.table("clients").select("*").eq("id", client_id).execute()
    if response.data:
        return response.data[0]
    return None

async def get_workout_records(client_id: str, limit: int = 100):
    """Get workout records for a specific client"""
    response = (
        supabase.table("workout_records")
        .select("*")
        .eq("client_id", client_id)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data

async def create_workout_record(record_data: dict):
    """Create a new workout record"""
    response = supabase.table("workout_records").insert(record_data).execute()
    return response.data 