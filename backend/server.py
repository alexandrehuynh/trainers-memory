import os
import uvicorn
import sys
import logging
import signal
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def handle_exit(signum, frame):
    """Handle exit signals gracefully."""
    logger.info("Shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Get port from environment variable or use default
    # Render sets the PORT environment variable
    port = int(os.getenv("PORT", 10000))
    
    logger.info(f"Starting server on port {port} at host 0.0.0.0...")
    logger.info(f"Using PostgreSQL database")
    
    try:
        # Start the API server
        # Ensure we bind to 0.0.0.0 so Render can detect the port
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
    finally:
        logger.info("Server shutdown complete.") 