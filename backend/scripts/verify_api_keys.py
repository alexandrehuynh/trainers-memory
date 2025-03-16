#!/usr/bin/env python
"""
Verify API Keys Script

This script checks all API keys in the database to ensure they have proper user_id associations
and corrects any issues found. It helps to identify and fix potential authentication problems.

Usage:
    python verify_api_keys.py [--fix]
"""

import os
import sys
import asyncio
import argparse
import logging
from uuid import UUID
from sqlalchemy import text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Default admin user ID for fallback scenarios
DEFAULT_ADMIN_USER_ID = UUID('00000000-0000-0000-0000-000000000001')

# Import after path setup
from app.db.config import AsyncSessionLocal
from app.db.models import APIKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

async def verify_api_keys(fix=False):
    """Verify all API keys and optionally fix issues."""
    logger.info("Starting API key verification")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if user_id column exists
            try:
                result = await session.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'user_id')")
                )
                user_id_exists = result.scalar()
                if not user_id_exists:
                    logger.error("user_id column does not exist in api_keys table! Please run migrations first.")
                    return
            except Exception as e:
                logger.error(f"Error checking if user_id column exists: {e}")
                return
            
            # Get all API keys
            result = await session.execute(select(APIKey))
            api_keys = result.scalars().all()
            
            logger.info(f"Found {len(api_keys)} API keys in the database")
            
            # Check each API key for issues
            issues_found = 0
            for api_key in api_keys:
                issues = []
                
                # Check if user_id is None
                if not hasattr(api_key, 'user_id') or api_key.user_id is None:
                    issues.append("Missing user_id")
                
                # Check other required fields
                if not hasattr(api_key, 'client_id') or api_key.client_id is None:
                    issues.append("Missing client_id")
                
                if issues:
                    issues_found += 1
                    logger.warning(f"Issues with API key {api_key.id}: {', '.join(issues)}")
                    
                    if fix:
                        logger.info(f"Fixing issues with API key {api_key.id}")
                        try:
                            # Fix missing user_id
                            if "Missing user_id" in issues:
                                # First try to get user_id from the associated client
                                try:
                                    result = await session.execute(
                                        text("SELECT user_id FROM clients WHERE id = :client_id")
                                        .bindparams(client_id=api_key.client_id)
                                    )
                                    client_user_id = result.scalar()
                                    
                                    if client_user_id:
                                        await session.execute(
                                            update(APIKey)
                                            .where(APIKey.id == api_key.id)
                                            .values(user_id=client_user_id)
                                        )
                                        logger.info(f"Updated API key {api_key.id} with user_id from client: {client_user_id}")
                                    else:
                                        # If no client user_id found, use default admin user
                                        await session.execute(
                                            update(APIKey)
                                            .where(APIKey.id == api_key.id)
                                            .values(user_id=DEFAULT_ADMIN_USER_ID)
                                        )
                                        logger.info(f"Updated API key {api_key.id} with default admin user_id")
                                except Exception as e:
                                    logger.error(f"Error fixing user_id for API key {api_key.id}: {e}")
                            
                            # Commit the changes
                            await session.commit()
                        except Exception as e:
                            logger.error(f"Error fixing API key {api_key.id}: {e}")
                            await session.rollback()
            
            if issues_found == 0:
                logger.info("All API keys are valid!")
            else:
                logger.warning(f"Found {issues_found} API keys with issues")
                if fix:
                    logger.info("Attempted to fix all issues")
                else:
                    logger.info("Run with --fix to automatically fix these issues")
                    
        except Exception as e:
            logger.error(f"Error verifying API keys: {e}")
            await session.rollback()

async def main():
    parser = argparse.ArgumentParser(description='Verify API keys and optionally fix issues.')
    parser.add_argument('--fix', action='store_true', help='Fix any issues found with API keys')
    args = parser.parse_args()
    
    await verify_api_keys(fix=args.fix)

if __name__ == "__main__":
    asyncio.run(main()) 