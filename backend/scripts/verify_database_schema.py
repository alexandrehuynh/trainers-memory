#!/usr/bin/env python
"""
Database Schema Verification Script

This script verifies the database schema by checking:
1. Required tables exist
2. Required columns exist in each table
3. Required indexes and constraints exist
4. Foreign key relationships are intact

Usage:
    python verify_database_schema.py [--verbose] [--strict]

Options:
    --verbose    Show detailed output for all checks
    --strict     Exit with error code if any issues are found
"""

import os
import sys
import logging
import argparse
from sqlalchemy import create_engine, inspect, text
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

# Get database URI from environment
DB_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/trainers_memory")

# Define required tables and their columns
REQUIRED_SCHEMA = {
    'users': {
        'columns': ['id', 'email', 'hashed_password', 'is_active', 'created_at'],
        'indexes': ['users_pkey', 'ix_users_email'],
    },
    'clients': {
        'columns': ['id', 'name', 'email', 'phone', 'notes', 'created_at', 'updated_at', 'user_id'],
        'indexes': ['clients_pkey', 'ix_clients_name', 'ix_clients_email', 'ix_clients_user_id'],
        'foreign_keys': [
            {'column': 'user_id', 'references_table': 'users', 'references_column': 'id'}
        ]
    },
    'api_keys': {
        'columns': ['id', 'key', 'client_id', 'user_id', 'name', 'description', 'active', 'created_at', 'last_used_at', 'expires_at'],
        'indexes': ['api_keys_pkey', 'ix_api_keys_key', 'ix_api_keys_client_id', 'ix_api_keys_user_id'],
        'foreign_keys': [
            {'column': 'client_id', 'references_table': 'clients', 'references_column': 'id'},
            {'column': 'user_id', 'references_table': 'users', 'references_column': 'id'}
        ]
    },
    'workouts': {
        'columns': ['id', 'client_id', 'date', 'type', 'duration', 'notes', 'created_at', 'updated_at'],
        'indexes': ['workouts_pkey', 'ix_workouts_client_id', 'ix_workouts_date'],
        'foreign_keys': [
            {'column': 'client_id', 'references_table': 'clients', 'references_column': 'id'}
        ]
    }
}

def check_database_schema(verbose=False, strict=False):
    """
    Check the database schema against the required schema
    
    Args:
        verbose: Whether to show detailed output for all checks
        strict: Whether to exit with error code if any issues are found
        
    Returns:
        bool: True if all checks passed, False otherwise
    """
    engine = create_engine(DB_URI.replace("postgres://", "postgresql://"))
    inspector = inspect(engine)
    
    all_checks_passed = True
    
    # Get all tables in the database
    db_tables = inspector.get_table_names(schema='public')
    if verbose:
        logger.info(f"Database tables: {db_tables}")
    
    # Check each required table
    for table_name, requirements in REQUIRED_SCHEMA.items():
        # Check if table exists
        if table_name not in db_tables:
            logger.error(f"Required table '{table_name}' does not exist!")
            all_checks_passed = False
            continue
        
        if verbose:
            logger.info(f"Checking table '{table_name}'...")
        
        # Get columns in the table
        columns = inspector.get_columns(table_name, schema='public')
        column_names = [col['name'] for col in columns]
        
        # Check required columns
        for required_column in requirements.get('columns', []):
            if required_column not in column_names:
                logger.error(f"Required column '{required_column}' missing from table '{table_name}'!")
                all_checks_passed = False
        
        # Get indexes in the table
        indexes = inspector.get_indexes(table_name, schema='public')
        index_names = [idx['name'] for idx in indexes]
        
        # Also get primary key constraint which is not in get_indexes
        pk_constraint = inspector.get_pk_constraint(table_name, schema='public')
        if pk_constraint and 'name' in pk_constraint:
            index_names.append(pk_constraint['name'])
        
        # Check required indexes
        for required_index in requirements.get('indexes', []):
            if required_index not in index_names:
                logger.error(f"Required index '{required_index}' missing from table '{table_name}'!")
                all_checks_passed = False
        
        # Get foreign keys in the table
        fkeys = inspector.get_foreign_keys(table_name, schema='public')
        
        # Check required foreign keys
        for required_fk in requirements.get('foreign_keys', []):
            fk_found = False
            for fk in fkeys:
                if (fk['constrained_columns'] == [required_fk['column']] and
                    fk['referred_table'] == required_fk['references_table'] and
                    fk['referred_columns'] == [required_fk['references_column']]):
                    fk_found = True
                    break
            
            if not fk_found:
                logger.error(f"Required foreign key '{required_fk['column']}' -> '{required_fk['references_table']}.{required_fk['references_column']}' missing from table '{table_name}'!")
                all_checks_passed = False
    
    # Summary
    if all_checks_passed:
        logger.info("✅ All database schema checks passed!")
    else:
        logger.error("❌ There were issues with the database schema. See above for details.")
    
    return all_checks_passed

def main():
    parser = argparse.ArgumentParser(description='Verify database schema against requirements')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output for all checks')
    parser.add_argument('--strict', action='store_true', help='Exit with error code if any issues are found')
    
    args = parser.parse_args()
    
    try:
        all_checks_passed = check_database_schema(verbose=args.verbose, strict=args.strict)
        if args.strict and not all_checks_passed:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error verifying database schema: {e}")
        if args.strict:
            sys.exit(1)

if __name__ == "__main__":
    main() 