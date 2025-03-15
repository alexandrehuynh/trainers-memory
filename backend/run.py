import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting server on port {port} at host 0.0.0.0...")
    print(f"To check if port is open, you can run: curl http://localhost:{port}/docs")
    
    # Start the API server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 