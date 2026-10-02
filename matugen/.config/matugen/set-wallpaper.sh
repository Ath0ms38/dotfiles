#!/bin/bash
# Set the wallpaper — image or video — and regenerate the system colors.
#
# Usage:
#   set-wallpaper.sh <path> [-t <matugen-scheme>] [--no-matugen]
#   set-wallpaper.sh                 # rofi picker over the wallpapers dir
#
# For a video, colors are generated from its first frame; the video itself is
# displayed by mpvpaper. The actual applying happens in post-matugen.sh so
# that colors and wallpaper always land together.
set -uo pipefail

source "$HOME/.config/matugen/wallpaper-lib.sh"

SCHEME="scheme-tonal-spot"
USE_MATUGEN=1
TARGET=""

wallpapers_dir() {
    local dir
    dir="$(jq -r '.wallpapers_dir // empty' "$HOME/.config/fabric/config.json" 2>/dev/null)"
    printf '%s' "${dir:-$HOME/dotfiles/wallpapers}" | sed "s|^~|$HOME|"
}

usage() {
    sed -n '2,6p' "$0" | sed 's/^# \?//'
    exit "${1:-0}"
}

while [ $# -gt 0 ]; do
    case "$1" in
        -t | --scheme) SCHEME="$2"; shift 2 ;;
        --no-matugen)  USE_MATUGEN=0; shift ;;
        -h | --help)   usage 0 ;;
        *)             TARGET="$1"; shift ;;
    esac
done

# No argument: let the user pick one (this is what the rofi settings menu does)
if [ -z "$TARGET" ]; then
    dir="$(wallpapers_dir)"
    choice="$(find "$dir" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null |
        while read -r f; do wall_is_wallpaper "$f" && printf '%s\n' "$f"; done |
        sort | rofi -dmenu -i -p "  Wallpaper")" || exit 0
    [ -n "$choice" ] || exit 0
    TARGET="$dir/$choice"
fi

if [ ! -f "$TARGET" ]; then
    echo "Wallpaper not found: $TARGET" >&2
    exit 1
fi
TARGET="$(realpath "$TARGET")"

if ! wall_is_wallpaper "$TARGET"; then
    echo "Unsupported wallpaper format: $TARGET" >&2
    exit 1
fi

if wall_is_video "$TARGET" && ! command -v mpvpaper >/dev/null; then
    echo "mpvpaper is not installed — video wallpapers need it (yay -S mpvpaper)" >&2
    exit 1
fi

STILL="$(wall_still "$TARGET")" || {
    echo "Could not extract a frame from $TARGET" >&2
    exit 1
}

if [ "$USE_MATUGEN" -eq 1 ] && command -v matugen >/dev/null; then
    # Record the real target first: matugen only ever sees the still, its
    # post_hook reads this state to know a video is what should be displayed.
    wall_state_write "$TARGET" "$STILL"
    matugen image "$STILL" -t "$SCHEME"
else
    wall_apply "$TARGET" "$STILL"
    hyprctl reload >/dev/null 2>&1
    echo "Wallpaper set: $TARGET"
fi
