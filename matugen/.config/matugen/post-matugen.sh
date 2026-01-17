#!/bin/bash
# Post-matugen hook script - handles all app reloads
# Usage: post-matugen.sh <image_path>

IMAGE="$1"
HYPRPAPER_CONF="$HOME/.config/hypr/hyprpaper.conf"

echo "Post-matugen: Updating wallpaper and reloading apps..."

# 1. Update hyprpaper.conf and restart hyprpaper
if [ -n "$IMAGE" ]; then
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

    pkill hyprpaper
    sleep 0.2
    hyprpaper &
    echo "Wallpaper updated: $IMAGE"
fi

# 2. Reload Hyprland
hyprctl reload
echo "Hyprland reloaded"

# 3. Reload Kitty colors (broadcast to all instances via their sockets)
# Find all kitty sockets (both abstract @kitty-* and /tmp/kitty-*)
for socket in $(ss -xl 2>/dev/null | grep -oE '(@kitty-[0-9]+|/tmp/kitty-[0-9]+)'); do
    kitten @ --to "unix:$socket" set-colors -a -c "$HOME/.config/kitty/colors.conf" 2>/dev/null
done
echo "Kitty colors reloaded"

# 4. Reload Swaync
swaync-client -rs 2>/dev/null && echo "Swaync reloaded"

# 5. Reload Fabric CSS (if fabric-cli is available, otherwise file watcher handles it)
if command -v fabric-cli &> /dev/null; then
    fabric-cli exec fabric-bar 'app.set_css()' && echo "Fabric CSS reloaded"
else
    echo "Fabric will auto-reload (file watcher)"
fi

echo "Post-matugen: Done!"
