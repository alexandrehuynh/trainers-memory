#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting database setup...${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}.env file created. Please update with your settings.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking if PostgreSQL is running...${NC}"
pg_isready > /dev/null 2>&1
PG_RUNNING=$?

if [ $PG_RUNNING -ne 0 ]; then
    echo -e "${RED}PostgreSQL is not running.${NC}"
    echo -e "${YELLOW}Attempting to start PostgreSQL...${NC}"
    
    # Check if we're on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Try to start PostgreSQL with Homebrew
        brew services start postgresql > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}PostgreSQL started successfully with Homebrew.${NC}"
        else
            echo -e "${RED}Failed to start PostgreSQL. Please start manually.${NC}"
            exit 1
        fi
    else
        # For Linux and other systems
        if command -v systemctl > /dev/null; then
            sudo systemctl start postgresql > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}PostgreSQL started successfully with systemctl.${NC}"
            else
                echo -e "${RED}Failed to start PostgreSQL with systemctl.${NC}"
                exit 1
            fi
        else
            echo -e "${RED}Could not start PostgreSQL automatically. Please start manually.${NC}"
            exit 1
        fi
    fi
else
    echo -e "${GREEN}PostgreSQL is running.${NC}"
fi

# Create the database if it doesn't exist
echo -e "${YELLOW}Checking if database exists...${NC}"
DB_NAME="trainers_memory"
DB_EXISTS=$(psql -lqt | cut -d \| -f 1 | grep -w $DB_NAME | wc -l)

if [ $DB_EXISTS -eq 0 ]; then
    echo -e "${YELLOW}Creating database '$DB_NAME'...${NC}"
    createdb $DB_NAME
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database '$DB_NAME' created successfully.${NC}"
    else
        echo -e "${RED}Failed to create database. Try manually:${NC}"
        echo -e "createdb $DB_NAME"
        exit 1
    fi
else
    echo -e "${GREEN}Database '$DB_NAME' already exists.${NC}"
fi

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python -m alembic upgrade head
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database migrations applied successfully.${NC}"
else
    echo -e "${RED}Failed to apply migrations. Try manually:${NC}"
    echo -e "python -m alembic upgrade head"
    exit 1
fi

# Generate API key
echo -e "${YELLOW}Generating API key...${NC}"
python scripts/generate_api_key.py

echo -e "\n${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}To start the API server, run:${NC}"
echo -e "  ./scripts/start_dev.sh" 