#!/bin/bash

# Simple wallpaper setter for Hyprland using hyprctl
WALLPAPER_PATH="$HOME/dotfiles/wallpapers/anime_room.png"

# Check if wallpaper file exists
if [ -f "$WALLPAPER_PATH" ]; then
    # Use hyprctl to set wallpaper
    hyprctl hyprpaper wallpaper ",$WALLPAPER_PATH"
    echo "Wallpaper set to: $WALLPAPER_PATH"
else
    echo "Wallpaper file not found: $WALLPAPER_PATH"
fi
