#!/usr/bin/env bash
# Exit on error
set -e

# Print each command for debugging
set -x

# Install Python dependencies
pip install -r requirements.txt

# Make sure server.py is executable
chmod +x server.py

# Print environment for debugging
echo "Python version:"
python --version
echo "Current directory:"
pwd
echo "Directory contents:"
ls -la
echo "PORT environment variable:"
echo $PORT
echo "DATABASE_URL type: $(echo $DATABASE_URL | cut -d':' -f1)" 