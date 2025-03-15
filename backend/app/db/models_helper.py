"""
Models helper module

This module provides helpers for configuring SQLAlchemy models
to work with PostgreSQL.
"""

from typing import Any, Dict, List, Tuple, Union

def get_table_args(indexes: List[Any] = None) -> Union[Tuple, Dict[str, Any]]:
    """
    Get the table arguments for PostgreSQL, including the schema.
    
    Args:
        indexes: List of SQLAlchemy Index objects
        
    Returns:
        Either a tuple of indexes + schema dict or just the schema dict
    """
    # Default to empty list if None
    indexes = indexes or []
    
    # Always include schema for PostgreSQL
    if indexes:
        return (*indexes, {"schema": "public"})
    return {"schema": "public"}

def get_foreign_key_target(table_name: str) -> str:
    """
    Get the foreign key target with the schema name included.
    
    Args:
        table_name: The target table name
        
    Returns:
        The full table reference with schema for PostgreSQL
    """
    # Always include schema for PostgreSQL
    return f"public.{table_name}" 