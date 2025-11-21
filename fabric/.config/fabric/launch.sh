#!/bin/bash
# Fabric Bar Launch Script

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run ./setup.sh first to install Fabric."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Fabric is installed
if ! python -c "import fabric" 2>/dev/null; then
    echo "Error: Fabric not installed in virtual environment!"
    echo "Please run ./setup.sh to install Fabric."
    exit 1
fi

# Kill existing Fabric bar processes
# Look for python processes running fabric-bar.py in this directory
SCRIPT_DIR="$(pwd)"
pkill -f "python.*${SCRIPT_DIR}/fabric-bar.py" 2>/dev/null || true
sleep 0.5

# Launch the bar
echo "Starting Fabric bar..."
python fabric-bar.py &

echo "Fabric bar started! PID: $!"
echo "To stop: pkill -f 'fabric-bar' or run: ./stop.sh"
