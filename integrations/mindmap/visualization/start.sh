#!/bin/bash

# Start the visualization dev server
# Requires: Flask backend running on port 5002

cd "$(dirname "$0")"

echo "🧠 Starting HAL's Consciousness Visualization..."
echo ""
echo "Make sure the Flask backend is running:"
echo "  cd /home/hal/consciousness-framework/integrations/mindmap"
echo "  ./start_server.sh"
echo ""
echo "Starting dev server on http://localhost:3000"
echo ""

npm run dev
