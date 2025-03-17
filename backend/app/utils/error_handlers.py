"""
Error handling utilities for the FastAPI application.

This module provides centralized error handling functionality.
"""

import logging
from functools import wraps
from typing import Callable, Any, Type, Dict, Optional, List, Union
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Configure logging
logger = logging.getLogger(__name__)

# Custom exceptions
class AuthError(Exception):
    """Base exception for authentication errors."""
    def __init__(self, message: str = "Authentication error", status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ForbiddenError(Exception):
    """Exception for authorization/permission errors."""
    def __init__(self, message: str = "Permission denied"):
        self.message = message
        self.status_code = 403
        super().__init__(self.message)

class NotFoundError(Exception):
    """Exception for resource not found errors."""
    def __init__(self, resource_type: str, resource_id: str):
        self.message = f"{resource_type} with ID {resource_id} not found"
        self.status_code = 404
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(self.message)

class BadRequestError(Exception):
    """Exception for invalid request data errors."""
    def __init__(self, message: str = "Bad request"):
        self.message = message
        self.status_code = 400
        super().__init__(self.message)


def handle_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in async route handlers.
    
    This decorator wraps route handlers and catches exceptions,
    converting them to appropriate HTTP responses.
    
    Args:
        func: The async function to wrap.
        
    Returns:
        Wrapped function that handles exceptions.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise FastAPI HTTP exceptions directly
            raise
        except ValidationError as e:
            # Handle Pydantic validation errors
            logger.warning(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors()
            )
        except AuthError as e:
            # Handle authentication errors
            logger.warning(f"Authentication error: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
                headers={"WWW-Authenticate": "Bearer"}
            )
        except ForbiddenError as e:
            # Handle authorization errors
            logger.warning(f"Permission error: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=e.message
            )
        except NotFoundError as e:
            # Handle not found errors
            logger.info(f"Resource not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message
            )
        except BadRequestError as e:
            # Handle bad request errors
            logger.info(f"Bad request: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message
            )
        except IntegrityError as e:
            # Handle database integrity errors (e.g., unique constraint violations)
            logger.error(f"Database integrity error: {str(e)}")
            # Extract specific error messages for common cases
            error_message = str(e)
            if "unique constraint" in error_message.lower():
                if "email" in error_message.lower():
                    detail = "A user with this email already exists."
                else:
                    detail = "A record with these values already exists."
            else:
                detail = "Database constraint violation. The operation cannot be completed."
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail
            )
        except SQLAlchemyError as e:
            # Handle other database errors
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred. Please try again later."
            )
        except Exception as e:
            # Handle all other exceptions
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred. Please try again later."
            )
    
    return wrapper 