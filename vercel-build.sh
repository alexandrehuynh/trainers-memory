#!/bin/bash

# Print node and npm versions
echo "Node version: $(node -v)"
echo "NPM version: $(npm -v)"

# Clear npm cache
echo "Clearing npm cache..."
npm cache clean --force

# Install critical dependencies explicitly first
echo "Installing critical dependencies..."
npm install --no-save babel-plugin-module-resolver

# Install all dependencies
echo "Installing all dependencies..."
npm install

# List installed packages to verify babel plugin
echo "Verifying babel-plugin-module-resolver installation:"
npm list babel-plugin-module-resolver

# Build the application with extra debugging
echo "Starting build process..."
NODE_OPTIONS="--max-old-space-size=4096 --trace-warnings" npm run build

echo "Build completed successfully!" 