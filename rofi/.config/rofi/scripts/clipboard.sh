#!/bin/bash
# Clipboard manager using cliphist

if ! command -v cliphist &> /dev/null; then
    notify-send "Clipboard" "cliphist not installed" -u critical
    exit 1
fi

selected=$(cliphist list | rofi -dmenu -p "  Clipboard" \
    -theme-str 'listview { lines: 10; }')

if [[ -n "$selected" ]]; then
    echo "$selected" | cliphist decode | wl-copy
fi
