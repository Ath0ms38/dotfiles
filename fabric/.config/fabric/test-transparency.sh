#!/bin/bash
# Test script to verify transparency and workspace settings

cd "$(dirname "$0")"

echo "=== Fabric Bar Configuration Test ==="
echo

echo "1. Checking CSS transparency settings..."
if grep -q "rgba(141, 110, 99, 0.7)" style.css; then
    echo "   ✓ Bar background opacity set to 0.7 (70%)"
else
    echo "   ✗ Bar background NOT transparent"
fi

if grep -q "rgba(60, 45, 41, 0.75)" style.css; then
    echo "   ✓ Widget background opacity set to 0.75 (75%)"
else
    echo "   ✗ Widget background NOT transparent"
fi

echo
echo "2. Checking Python opacity setting..."
if grep -q "set_opacity" main.py; then
    echo "   ✓ Window opacity method called in main.py"
else
    echo "   ✗ Window opacity NOT set in Python code"
fi

echo
echo "3. Checking workspace configuration..."
if grep -q "all=True" main.py; then
    echo "   ✓ HyprlandWorkspaces configured to show all workspaces"
else
    echo "   ✗ Workspaces NOT configured to show all"
fi

echo
echo "4. Current running processes..."
if pgrep -f "python.*main.py" > /dev/null; then
    echo "   ⚠ Fabric bar is currently RUNNING"
    echo "   You need to restart it to see changes:"
    echo "   ./restart.sh"
else
    echo "   ℹ Fabric bar is NOT running"
    echo "   Start it with: ./launch.sh"
fi

echo
echo "=== End of Test ==="
