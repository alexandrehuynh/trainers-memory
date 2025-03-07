from typing import Any, Dict
from datetime import datetime

# API version - should match main.py
API_VERSION = "v1"

class StandardResponse:
    """Utility class for generating standardized API responses."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Generate a standardized success response."""
        return {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "api_version": API_VERSION,
        }
    
    @staticmethod
    def error(message: str, status_code: int, details: Any = None) -> Dict[str, Any]:
        """Generate a standardized error response."""
        return {
            "status": "error",
            "message": message,
            "error_code": status_code,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "api_version": API_VERSION,
        } 