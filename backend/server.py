import os
# Force SQLite mode for Render deployment
os.environ["USE_SQLITE"] = "True"

import uvicorn
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Try to initialize the database if necessary
try:
    from init_db import init_sqlite_db
    logger.info("Initializing SQLite database...")
    init_sqlite_db()
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    # Continue anyway, the app might handle connection issues gracefully

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 10000))
    
    logger.info(f"Starting server on port {port}...")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')}")
    logger.info(f"USE_SQLITE: {os.getenv('USE_SQLITE', 'Not set')}")
    
    # Start the API server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 