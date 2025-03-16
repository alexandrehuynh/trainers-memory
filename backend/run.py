import uvicorn
import os
import signal
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def handle_exit(signum, frame):
    """Handle exit signals gracefully."""
    logger.info("Shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on port {port} at host 0.0.0.0...")
    logger.info(f"To check if port is open, you can run: curl http://localhost:{port}/docs")
    logger.info("Using PostgreSQL database")
    
    try:
        # Start the API server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            log_level="debug"  # Changed from info to debug for more detailed logs
        )
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
    finally:
        logger.info("Server shutdown complete.") 