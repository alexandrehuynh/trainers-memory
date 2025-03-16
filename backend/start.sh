#!/bin/bash

# Script to set up the test API key and start the API server

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set up the test API key
echo "Setting up test API key..."
python setup_test_api_key.py

# Start the API server
echo "Starting API server..."
python run.py 