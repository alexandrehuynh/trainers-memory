#!/usr/bin/env bash
# Exit on error
set -e

# Print each command for debugging
set -x

# Install Python dependencies
pip install -r requirements.txt

# Make sure server.py is executable
chmod +x server.py

# Create SQLite database if needed
python init_db.py

# Print environment for debugging
echo "Python version:"
python --version
echo "Current directory:"
pwd
echo "Directory contents:"
ls -la
echo "PORT environment variable:"
echo $PORT
echo "Database file exists check:"
if [ -f "./trainers_memory.db" ]; then
  echo "Database file exists"
  ls -la ./trainers_memory.db
else
  echo "Database file does not exist"
fi 