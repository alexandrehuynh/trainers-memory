#!/usr/bin/env python
"""
Generate API Key Script

This script generates an API key for testing/development and inserts it into the database.
It should be run once to set up a test API key.

Usage:
    python generate_api_key.py [--client_id CLIENT_ID] [--key_name KEY_NAME]

Options:
    --client_id    Client ID to associate with the key (default: a test client ID)
    --key_name     Name for the API key (default: "Test API Key")
"""

import os
import sys
import uuid
import argparse
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from dotenv import load_dotenv

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import after path setup
from app.db import Base
from app.db.models import APIKey, Client

async def create_test_api_key(client_id=None, key_name=None):
    """Create a test API key and insert it into the database."""
    # Set default values
    if client_id is None:
        client_id = str(uuid.uuid4())
    
    if key_name is None:
        key_name = "Test API Key"
    
    # Generate a random API key
    api_key = f"tmk_{uuid.uuid4().hex}"
    
    # Create database connection
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Convert the PostgreSQL URL to an async compatible version
    # Replace postgresql:// with postgresql+asyncpg://
    if DATABASE_URL.startswith('postgresql://'):
        async_database_url = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
        print(f"Converting database URL to async version: {async_database_url}")
    else:
        # If it's already using the async dialect or is another type of database
        async_database_url = DATABASE_URL
        print(f"Using database URL: {async_database_url}")

    try:
        # Create engine and session
        engine = create_async_engine(async_database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with engine.begin() as conn:
            # Create tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
        
        # First session to create the client
        async with async_session() as session:
            # Check if client exists, if not create it
            stmt = select(Client).where(Client.id == client_id)
            result = await session.execute(stmt)
            client = result.scalars().first()
            
            if not client:
                print(f"Creating test client with ID: {client_id}")
                client = Client(
                    id=client_id,
                    name="Test Client",
                    email="test@example.com",
                    phone="555-123-4567",
                    created_at=None  # Let the database set the timestamp
                )
                session.add(client)
                await session.commit()
                print("Client created successfully")
        
        # Second session to create the API key
        async with async_session() as session:
            # Verify client was created
            stmt = select(Client).where(Client.id == client_id)
            result = await session.execute(stmt)
            client = result.scalars().first()
            
            if not client:
                raise Exception(f"Failed to find client with ID: {client_id}")
            
            print(f"Creating API key for client: {client.name} (ID: {client.id})")
            
            # Create API key
            api_key_obj = APIKey(
                key=api_key,
                name=key_name,
                client_id=client_id,
                active=True,
                created_at=None,  # Let the database set the timestamp
                last_used_at=None
            )
            session.add(api_key_obj)
            await session.commit()
            print("API key created successfully")
        
        # Clean up
        await engine.dispose()
        
        return {
            "client_id": client_id,
            "api_key": api_key,
            "key_name": key_name
        }
    except Exception as e:
        print(f"Error creating API key: {str(e)}")
        print("\nTIP: Check your DATABASE_URL in .env file and make sure PostgreSQL is running")
        print("Example DATABASE_URL: postgresql://username:password@localhost:5432/trainers_memory")
        sys.exit(1)

async def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Generate a test API key.')
    parser.add_argument('--client_id', help='Client ID to associate with the key')
    parser.add_argument('--key_name', help='Name for the API key')
    args = parser.parse_args()
    
    print("Generating API key...")
    
    # Create the API key
    key_info = await create_test_api_key(
        client_id=args.client_id,
        key_name=args.key_name
    )
    
    # Display results
    print("\nAPI Key Generated Successfully!")
    print("==============================")
    print(f"Client ID: {key_info['client_id']}")
    print(f"API Key:   {key_info['api_key']}")
    print(f"Key Name:  {key_info['key_name']}")
    print("\nUse this API key in the X-API-Key header for your requests")
    print("Example:")
    print(f'curl -H "X-API-Key: {key_info["api_key"]}" http://localhost:8000/api/v1/me')

if __name__ == '__main__':
    asyncio.run(main()) 