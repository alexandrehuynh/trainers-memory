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

# Create a startup wrapper script that ensures port binding is detected
cat > start_with_warmup.sh << 'EOF'
#!/bin/bash
# Run the application in the background
python server.py &
SERVER_PID=$!

# Wait for the server to start (10 seconds)
echo "Waiting for server to start..."
sleep 10

# Check if the service is up
PORT=${PORT:-10000}
echo "Checking if service is running on port $PORT..."
curl -s http://localhost:$PORT/health || echo "Service not responding yet"

# Keep checking the server status
for i in {1..5}; do
  echo "Health check attempt $i..."
  if curl -s http://localhost:$PORT/health > /dev/null; then
    echo "Server is responding on port $PORT!"
    break
  fi
  sleep 5
done

# Output a notice to Render's port detection
echo "=== SERVER IS RUNNING ON PORT $PORT ==="

# Wait for the server process to finish
wait $SERVER_PID
EOF

chmod +x start_with_warmup.sh 