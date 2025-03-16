#!/usr/bin/env python
"""
Generate API Key Script

This script generates an API key for testing/development and inserts it into the database.
It should be run once to set up a test API key.

Usage:
    python generate_api_key.py [--client_id CLIENT_ID] [--key_name KEY_NAME] [--email EMAIL] [--user_id USER_ID]

Options:
    --client_id    Client ID to associate with the key (default: a test client ID)
    --key_name     Name for the API key (default: "Test API Key")
    --email        Email for the test client (default: a unique generated email)
    --user_id      User ID to associate with the key (default: a test user ID)
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
import datetime

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import after path setup
from app.db import Base
from app.db.models import APIKey, Client, User

async def create_test_api_key(client_id=None, key_name=None, email=None, user_id=None):
    """Create a test API key and insert it into the database."""
    # Set default values
    if client_id is None:
        client_id = str(uuid.uuid4())
    
    if key_name is None:
        key_name = "Test API Key"
    
    if user_id is None:
        user_id = str(uuid.uuid4())
    
    # Generate a unique email if not provided
    if email is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        email = f"test-{timestamp}@example.com"
    
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
        
        # First check if the user exists, if not create it
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if not user:
                print(f"Creating test user with ID: {user_id}")
                user = User(
                    id=user_id,
                    email=f"user-{uuid.uuid4().hex[:8]}@example.com",
                    role="trainer",
                    is_active=True,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now()
                )
                session.add(user)
                await session.commit()
                print(f"User created successfully with ID: {user_id}")
        
        # Now create the client
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
                    email=email,  # Use the provided or generated email
                    phone="555-123-4567",
                    user_id=user_id,  # Associate client with user
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now()
                )
                session.add(client)
                await session.commit()
                print(f"Client created successfully with email: {email}")
        
        # Create the API key
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
                user_id=user_id,  # Associate API key with user
                active=True,
                created_at=datetime.datetime.now(),
                last_used_at=None
            )
            session.add(api_key_obj)
            await session.commit()
            print("API key created successfully")
        
        # Clean up
        await engine.dispose()
        
        return {
            "client_id": client_id,
            "user_id": user_id,
            "api_key": api_key,
            "key_name": key_name,
            "email": email
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
    parser.add_argument('--email', help='Email for the test client')
    parser.add_argument('--user_id', help='User ID to associate with the key')
    args = parser.parse_args()
    
    print("Generating API key...")
    
    # Create the API key
    key_info = await create_test_api_key(
        client_id=args.client_id,
        key_name=args.key_name,
        email=args.email,
        user_id=args.user_id
    )
    
    # Display results
    print("\nAPI Key Generated Successfully!")
    print("==============================")
    print(f"User ID:   {key_info['user_id']}")
    print(f"Client ID: {key_info['client_id']}")
    print(f"Client Email: {key_info['email']}")
    print(f"API Key:   {key_info['api_key']}")
    print(f"Key Name:  {key_info['key_name']}")
    print("\nUse this API key in the X-API-Key header for your requests")
    print("Example:")
    print(f'curl -H "X-API-Key: {key_info["api_key"]}" http://localhost:8000/api/v1/me')

if __name__ == '__main__':
    asyncio.run(main()) 