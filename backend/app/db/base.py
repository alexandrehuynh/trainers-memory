"""
SQLAlchemy Base configuration.

This module provides the SQLAlchemy Base class for all ORM models.
"""

from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base() 