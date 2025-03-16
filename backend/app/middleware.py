from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class DatabaseErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle database transaction errors.
    
    This middleware catches SQLAlchemy exceptions and returns appropriate error responses
    while handling transaction cleanup.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Process the request and get the response
            response = await call_next(request)
            return response
            
        except SQLAlchemyError as e:
            # Log the SQL error
            logger.error(f"Database error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a JSON response with error details
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Database error occurred",
                    "error": str(e),
                    "data": None
                }
            )
            
        except Exception as e:
            # Log any other exception
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a JSON response with error details
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "An unexpected error occurred",
                    "error": str(e),
                    "data": None
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and their processing time.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        client_ip = forwarded_for.split(",")[0] if forwarded_for else request.client.host
        
        # Log the request
        logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log the response
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Processed in {process_time:.4f}s"
        )
        
        return response 