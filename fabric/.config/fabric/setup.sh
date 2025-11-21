#!/bin/bash
# Fabric Setup Script for EndeavourOS
# This script installs Fabric and all required dependencies

set -e

echo "=== Fabric Setup for EndeavourOS ==="
echo

# Install system dependencies
echo "Installing system dependencies..."
sudo pacman -S --needed python python-pip python-gobject python-cairo python-loguru \
    gtk3 cairo gtk-layer-shell libgirepository gobject-introspection \
    gobject-introspection-runtime pkgconf cinnamon-desktop

# Create virtual environment
echo
echo "Creating Python virtual environment..."
cd "$(dirname "$0")"
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Fabric from GitHub
echo
echo "Installing Fabric from GitHub..."
pip install --upgrade pip
pip install git+https://github.com/Fabric-Development/fabric.git

# Install additional Python dependencies
echo
echo "Installing additional dependencies..."
pip install psutil

echo
echo "=== Setup Complete! ==="
echo
echo "To activate the virtual environment, run:"
echo "  source ~/.config/fabric/venv/bin/activate"
echo
echo "To start the bar, run:"
echo "  ./launch.sh"
