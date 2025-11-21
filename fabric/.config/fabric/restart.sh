#!/bin/bash
# Fabric Bar Restart Script

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Restarting Fabric bar..."

# Stop the bar
"${SCRIPT_DIR}/stop.sh"

# Wait a moment
sleep 0.5

# Start the bar
"${SCRIPT_DIR}/launch.sh"
