#!/bin/bash
# Settings/Quick actions menu
# Enter = select, Escape = back to main menu

SCRIPTS_DIR="$HOME/.config/rofi/scripts"

options=(
    "  Screenshot area"
    "  Screenshot full"
    "  Color picker"
    "  Clipboard"
    "  Wallpaper"
    "  Reload theme"
)

declare -A actions=(
    ["  Screenshot area"]="grimblast copy area"
    ["  Screenshot full"]="grimblast copy screen"
    ["  Color picker"]="hyprpicker -a"
    ["  Clipboard"]="$SCRIPTS_DIR/clipboard.sh"
    ["  Wallpaper"]="$HOME/.config/matugen/set-wallpaper.sh"
    ["  Reload theme"]="matugen image \$(cat $HOME/.cache/current_wallpaper 2>/dev/null)"
)

selected=$(printf '%s\n' "${options[@]}" | rofi -dmenu -p "  Settings" \
    -theme-str 'listview { lines: 6; } element { padding: 12px 16px; }')

exit_code=$?

# Left (exit 10) or Escape (exit 1) = go back to main menu
if [[ $exit_code -eq 10 || $exit_code -eq 1 ]]; then
    exec "$SCRIPTS_DIR/main-menu.sh"
fi

if [[ $exit_code -eq 0 && -n "$selected" ]]; then
    eval "${actions[$selected]}"
fi
