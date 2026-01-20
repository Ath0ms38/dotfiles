#!/bin/bash
# Fabric Bar Restart Script

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Stopping Fabric bar..."
pkill -f "python.*fabric-bar.py" 2>/dev/null
pkill -f "python.*ax_notch_bar.py" 2>/dev/null
sleep 0.5

echo "Clearing Python cache..."
find "$SCRIPT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find "$SCRIPT_DIR" -name "*.pyc" -delete 2>/dev/null

echo "Starting Fabric bar..."
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

python "$SCRIPT_DIR/fabric-bar.py" &
python "$SCRIPT_DIR/ax_notch_bar.py" &