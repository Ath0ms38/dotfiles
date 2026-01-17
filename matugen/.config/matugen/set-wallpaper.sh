#!/bin/bash
# Set wallpaper by updating hyprpaper.conf and restarting hyprpaper
# Usage: set-wallpaper.sh <image_path>

IMAGE="$1"
HYPRPAPER_CONF="$HOME/.config/hypr/hyprpaper.conf"

if [ -z "$IMAGE" ]; then
    echo "Usage: set-wallpaper.sh <image_path>"
    exit 1
fi

# Update hyprpaper.conf with new wallpaper path
cat > "$HYPRPAPER_CONF" << EOF
# Wallpaper for all monitors (set by matugen)
wallpaper {
    monitor =
    path = $IMAGE
    fit_mode = cover
}

# Misc options
ipc = true
splash = false
splash_offset = 20
splash_opacity = 0.8
EOF

# Restart hyprpaper to apply the new wallpaper
pkill hyprpaper
sleep 0.2
hyprpaper &

# Reload hyprland config
hyprctl reload
