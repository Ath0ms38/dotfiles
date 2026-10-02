#!/bin/bash
# Re-apply the last wallpaper at login — hyprpaper for images, mpvpaper for
# videos. Replaces the plain `exec-once = hyprpaper` autostart.
source "$HOME/.config/matugen/wallpaper-lib.sh"

SOURCE="$(wall_state source || true)"

# Nothing recorded yet (or the file went away): fall back to hyprpaper, which
# still has a valid path in its own conf.
if [ -z "$SOURCE" ] || [ ! -f "$SOURCE" ]; then
    exec hyprpaper
fi

wall_apply "$SOURCE" "$(wall_state still || printf '%s' "$SOURCE")"
