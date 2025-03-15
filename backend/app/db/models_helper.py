"""
Models helper module

This module provides helpers for configuring SQLAlchemy models
to work with both PostgreSQL and SQLite.
"""

import os
from typing import Any, Dict, List, Tuple, Union

def get_table_args(indexes: List[Any] = None) -> Union[Tuple, Dict[str, Any]]:
    """
    Get the table arguments based on the database type.
    For PostgreSQL, include the schema. For SQLite, exclude it.
    
    Args:
        indexes: List of SQLAlchemy Index objects
        
    Returns:
        Either a tuple of indexes + schema dict for PostgreSQL,
        or just a tuple of indexes for SQLite
    """
    # Default to empty list if None
    indexes = indexes or []
    
    # Check if we're using SQLite
    use_sqlite = os.getenv("USE_SQLITE", "False").lower() in ("true", "1", "t")
    
    if use_sqlite:
        # SQLite doesn't support schemas, so just return the indexes
        if indexes:
            return tuple(indexes)
        return {}
    else:
        # PostgreSQL - include schema
        if indexes:
            return (*indexes, {"schema": "public"})
        return {"schema": "public"}

def get_foreign_key_target(table_name: str) -> str:
    """
    Get the foreign key target based on the database type.
    For PostgreSQL, include the schema. For SQLite, exclude it.
    
    Args:
        table_name: The target table name
        
    Returns:
        The full table reference with schema for PostgreSQL,
        or just the table name for SQLite
    """
    # Check if we're using SQLite
    use_sqlite = os.getenv("USE_SQLITE", "False").lower() in ("true", "1", "t")
    
    if use_sqlite:
        # SQLite doesn't use schemas
        return table_name
    else:
        # PostgreSQL - include schema
        return f"public.{table_name}" 