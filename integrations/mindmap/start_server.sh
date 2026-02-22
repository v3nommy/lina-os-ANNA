#!/bin/bash
# Mindmap Server Startup Script

# Set default configuration
export MINDMAP_DB_PATH="${MINDMAP_DB_PATH:-/tmp/mindmap.db}"
export MINDMAP_PORT="${MINDMAP_PORT:-5002}"
export MINDMAP_URL="${MINDMAP_URL:-http://localhost:5002}"

echo "=================================================="
echo "Starting Mindmap Server"
echo "=================================================="
echo "Database: $MINDMAP_DB_PATH"
echo "Port: $MINDMAP_PORT"
echo "URL: $MINDMAP_URL"
echo "=================================================="
echo ""

# Start the server
python server.py
