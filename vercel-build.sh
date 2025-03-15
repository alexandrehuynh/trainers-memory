#!/bin/bash

# Print node and npm versions
echo "Node version: $(node -v)"
echo "NPM version: $(npm -v)"

# Install dependencies
npm install

# Build the application
npm run build

echo "Build completed successfully!" 