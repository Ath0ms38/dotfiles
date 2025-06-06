#!/bin/bash

# Handle waybar workspace clicks - activate workspace and update special buttons
# Usage: workspace-click-handler.sh <workspace_id>

WORKSPACE_ID="$1"

if [ -z "$WORKSPACE_ID" ]; then
    echo "Usage: workspace-click-handler.sh <workspace_id>"
    exit 1
fi

# Activate the workspace
hyprctl dispatch workspace "$WORKSPACE_ID"

# Update special workspace buttons
pkill -RTMIN+8 waybar   # Discord
pkill -RTMIN+9 waybar   # VSCode  
pkill -RTMIN+10 waybar  # Minecraft
