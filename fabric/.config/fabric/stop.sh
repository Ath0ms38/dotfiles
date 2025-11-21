#!/bin/bash
# Fabric Bar Stop Script

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Stopping Fabric bar..."

# Method 1: Kill by exact path match
pkill -f "fabric-bar.py" 2>/dev/null && echo "Killed process matching: fabric-bar.py"

# Method 2: Kill any python process in this directory running fabric-bar.py
pgrep -f "${SCRIPT_DIR}/fabric-bar.py" | xargs -r kill 2>/dev/null && echo "Killed remaining processes"

# Wait a moment
sleep 0.3

# Check if any processes remain
if pgrep -f "${SCRIPT_DIR}/fabric-bar.py" >/dev/null; then
    echo "Force killing remaining processes..."
    pgrep -f "${SCRIPT_DIR}/fabric-bar.py" | xargs -r kill -9 2>/dev/null
fi

# Verify
if ! pgrep -f "${SCRIPT_DIR}/fabric-bar.py" >/dev/null; then
    echo "Fabric bar stopped successfully."
else
    echo "Warning: Some processes may still be running."
    echo "Try manually: kill $(pgrep -f "${SCRIPT_DIR}/fabric-bar.py")"
fi
