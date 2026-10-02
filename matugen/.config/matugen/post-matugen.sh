#!/bin/bash
# Post-matugen hook script - applies the wallpaper and reloads all apps
# Usage: post-matugen.sh <image_path>
#
# <image_path> is always an image (matugen cannot read video). When it matches
# the still recorded by set-wallpaper.sh, the wallpaper to display is the
# source from that state — possibly an .mp4 handled by mpvpaper.

source "$HOME/.config/matugen/wallpaper-lib.sh"

IMAGE="$(realpath "${1:-}" 2>/dev/null || printf '%s' "${1:-}")"

echo "Post-matugen: Updating wallpaper and reloading apps..."

# 1. Apply the wallpaper (hyprpaper for images, mpvpaper for videos)
if [ -n "$IMAGE" ]; then
    SOURCE="$(wall_state source || true)"
    STILL="$(wall_state still || true)"

    # Direct `matugen image foo.png` run (rofi "Reload theme", scripts, ...):
    # no pending state, the image is the wallpaper.
    if [ -z "$SOURCE" ] || [ "$STILL" != "$IMAGE" ]; then
        SOURCE="$IMAGE"
        STILL="$IMAGE"
    fi

    wall_apply "$SOURCE" "$STILL"
    echo "Wallpaper updated: $SOURCE"
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
