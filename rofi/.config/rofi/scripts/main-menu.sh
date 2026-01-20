#!/bin/bash
# Main menu with categories
# Enter = select, Escape = close

SCRIPTS_DIR="$HOME/.config/rofi/scripts"

options=(
    "  Apps"
    "  Files"
    "  Search"
    "  Calc"
    "  Power"
    "  Settings"
)

declare -A actions=(
    ["  Apps"]="rofi -show drun"
    ["  Files"]="$SCRIPTS_DIR/filebrowser.sh"
    ["  Search"]="$SCRIPTS_DIR/websearch.sh"
    ["  Calc"]="$SCRIPTS_DIR/calc.sh"
    ["  Power"]="$SCRIPTS_DIR/power-menu.sh"
    ["  Settings"]="$SCRIPTS_DIR/settings-menu.sh"
)

selected=$(printf '%s\n' "${options[@]}" | rofi -dmenu -p "  Menu" \
    -theme-str 'listview { lines: 6; } element { padding: 12px 16px; }')

exit_code=$?

# Left (exit 10) or Escape (exit 1) = close menu
if [[ $exit_code -eq 10 || $exit_code -eq 1 ]]; then
    exit 0
fi

# Only process selection if exit code is 0 (Enter/Right pressed)
if [[ $exit_code -eq 0 && -n "$selected" ]]; then
    eval "${actions[$selected]}"
fi
