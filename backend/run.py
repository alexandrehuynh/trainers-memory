import uvicorn
import os
import signal
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def handle_exit(signum, frame):
    """Handle exit signals gracefully."""
    print("\nShutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting server on port {port} at host 0.0.0.0...")
    print(f"To check if port is open, you can run: curl http://localhost:{port}/docs")
    print("Using PostgreSQL database")
    
    try:
        # Start the API server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully
        print("\nReceived keyboard interrupt. Shutting down...")
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        print("Server shutdown complete.") 