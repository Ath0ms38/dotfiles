#!/bin/bash
# Power menu
# Enter/Right = select, Escape = back to main menu

SCRIPTS_DIR="$HOME/.config/rofi/scripts"

options=(
    "  Lock"
    "  Suspend"
    "  Logout"
    "  Reboot"
    "  Shutdown"
)

declare -A actions=(
    ["  Lock"]="hyprlock"
    ["  Suspend"]="systemctl suspend"
    ["  Logout"]="hyprctl dispatch exit"
    ["  Reboot"]="systemctl reboot"
    ["  Shutdown"]="systemctl poweroff"
)

selected=$(printf '%s\n' "${options[@]}" | rofi -dmenu -p "  Power" \
    -theme-str 'listview { lines: 5; } element { padding: 12px 16px; }')

exit_code=$?

# Left (exit 10) or Escape (exit 1) = go back to main menu
[[ $exit_code -eq 10 || $exit_code -eq 1 ]] && exec "$SCRIPTS_DIR/main-menu.sh"

# Only process selection if exit code is 0 (Enter/Right pressed)
if [[ $exit_code -eq 0 && -n "$selected" ]]; then
    # Confirm for dangerous actions
    if [[ "$selected" == *"Reboot"* || "$selected" == *"Shutdown"* || "$selected" == *"Logout"* ]]; then
        confirm=$(echo -e "  Yes\n  No" | rofi -dmenu -p "Confirm?" \
            -theme-str 'listview { lines: 2; } element { padding: 12px 16px; }')

        confirm_code=$?
        [[ $confirm_code -eq 1 ]] && exec "$SCRIPTS_DIR/power-menu.sh"
        [[ "$confirm" != *"Yes"* ]] && exit 0
    fi
    eval "${actions[$selected]}"
fi
