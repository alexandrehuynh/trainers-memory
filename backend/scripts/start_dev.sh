#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting development environment setup...${NC}"

# Check if Redis is running
echo -e "Checking if Redis is running..."
redis-cli ping > /dev/null 2>&1
REDIS_RUNNING=$?

if [ $REDIS_RUNNING -ne 0 ]; then
    echo -e "${RED}Redis is not running.${NC}"
    echo -e "${YELLOW}Attempting to start Redis...${NC}"
    
    # Check if we're on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Try to start Redis with Homebrew
        brew services start redis > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Redis started successfully with Homebrew.${NC}"
        else
            # Try to start Redis directly
            redis-server --daemonize yes > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Redis started directly in daemon mode.${NC}"
            else
                echo -e "${RED}Failed to start Redis. OpenAI cache will be disabled.${NC}"
                echo -e "${YELLOW}To enable Redis caching:${NC}"
                echo -e "1. Install Redis: brew install redis (on macOS)"
                echo -e "2. Start Redis: brew services start redis (on macOS)"
            fi
        fi
    else
        # For Linux and other systems
        if command -v systemctl > /dev/null; then
            sudo systemctl start redis > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Redis started successfully with systemctl.${NC}"
            else
                echo -e "${RED}Failed to start Redis with systemctl.${NC}"
            fi
        else
            # Try to start Redis directly
            redis-server --daemonize yes > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Redis started directly in daemon mode.${NC}"
            else
                echo -e "${RED}Failed to start Redis. OpenAI cache will be disabled.${NC}"
                echo -e "${YELLOW}To enable Redis caching, install and start Redis manually.${NC}"
            fi
        fi
    fi
else
    echo -e "${GREEN}Redis is running.${NC}"
fi

# Create a .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}.env file created. Please update with your API keys.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Start the FastAPI application
echo -e "${YELLOW}Starting FastAPI application...${NC}"
uvicorn app.main:app --reload 