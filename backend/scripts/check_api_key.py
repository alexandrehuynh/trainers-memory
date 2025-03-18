#!/usr/bin/env python
"""
Check API Key Script

This script validates an API key by directly accessing the database.
It's useful for troubleshooting authentication issues.

Usage:
    python check_api_key.py [API_KEY]
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import after path setup
from app.db.config import AsyncSessionLocal
from app.db.repositories import AsyncAPIKeyRepository

async def validate_api_key(api_key: str) -> bool:
    """Validate an API key directly against the database."""
    print(f"Validating API key: {api_key}")
    
    async with AsyncSessionLocal() as session:
        repo = AsyncAPIKeyRepository(session)
        result = await repo.get_by_key(api_key)
        
        if result:
            print("\n✅ API Key is VALID!")
            print("Details:")
            print(f"  Key ID: {result['id']}")
            print(f"  Client ID: {result['client_id']}")
            print(f"  Name: {result['name']}")
            print(f"  Active: {result['active']}")
            print(f"  Created: {result['created_at']}")
            print(f"  Last Used: {result['last_used_at'] or 'Never'}")
            return True
        else:
            print("\n❌ API Key is INVALID or INACTIVE!")
            return False

async def main():
    parser = argparse.ArgumentParser(description='Check if an API key is valid.')
    parser.add_argument('api_key', nargs='?', help='The API key to validate')
    args = parser.parse_args()
    
    # If no API key is provided, use the one generated earlier
    api_key = args.api_key or "tmk_40af9844458144dc9ba5f5859c8b0f02"
    
    try:
        is_valid = await validate_api_key(api_key)
        if not is_valid:
            print("\nPossible reasons for API key rejection:")
            print("1. The key doesn't exist in the database")
            print("2. The key exists but is marked as inactive")
            print("3. Database connection issues")
            print("\nTry generating a new API key with:")
            print("  python scripts/generate_api_key.py")
    except Exception as e:
        print(f"\n⚠️ Error validating API key: {str(e)}")
        print("\nThis could indicate database connection issues.")

if __name__ == '__main__':
    asyncio.run(main()) 