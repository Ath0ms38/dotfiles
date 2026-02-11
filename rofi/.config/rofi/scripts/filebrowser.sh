#!/bin/bash
# Custom file browser using rofi dmenu
# Right/Enter = open folder or file
# Left = go to parent directory (or main menu if at start)

SCRIPTS_DIR="$HOME/.config/rofi/scripts"
START_DIR="$HOME"
current_dir="${1:-$START_DIR}"

# Normalize path
current_dir=$(realpath "$current_dir" 2>/dev/null || echo "$START_DIR")

while true; do
    # Build the file list
    # Show ".." for parent directory (unless at root)
    items=""
    if [[ "$current_dir" != "/" ]]; then
        items="  .."
    fi

    # List directories first, then files
    if [[ -d "$current_dir" ]]; then
        # Directories with folder icon
        dirs=$(find "$current_dir" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort | while read -r d; do
            echo "  $(basename "$d")"
        done)

        # Files with file icon
        files=$(find "$current_dir" -maxdepth 1 -mindepth 1 -type f 2>/dev/null | sort | while read -r f; do
            echo "  $(basename "$f")"
        done)

        if [[ -n "$dirs" ]]; then
            items="${items}${items:+$'\n'}${dirs}"
        fi
        if [[ -n "$files" ]]; then
            items="${items}${items:+$'\n'}${files}"
        fi
    fi

    # Show current directory in prompt (shortened)
    prompt_dir="${current_dir/#$HOME/~}"
    if [[ ${#prompt_dir} -gt 30 ]]; then
        prompt_dir="...${prompt_dir: -27}"
    fi

    selected=$(echo -e "$items" | rofi -dmenu -p "  $prompt_dir" \
        -theme-str 'listview { lines: 12; } element { padding: 8px 12px; }')

    exit_code=$?

    # Left (exit 10) = go to parent or main menu
    if [[ $exit_code -eq 10 ]]; then
        if [[ "$current_dir" == "$START_DIR" || "$current_dir" == "/" ]]; then
            exec "$SCRIPTS_DIR/main-menu.sh"
        else
            current_dir=$(dirname "$current_dir")
            continue
        fi
    fi

    # Escape (exit 1) = go back to main menu
    if [[ $exit_code -eq 1 ]]; then
        exec "$SCRIPTS_DIR/main-menu.sh"
    fi

    # Nothing selected
    [[ -z "$selected" ]] && exit 0

    # Handle selection
    # Remove the icon prefix
    name="${selected#*  }"

    if [[ "$name" == ".." ]]; then
        # Go to parent directory
        current_dir=$(dirname "$current_dir")
    elif [[ "$selected" == "  "* ]]; then
        # It's a directory
        current_dir="$current_dir/$name"
    elif [[ "$selected" == "  "* ]]; then
        # It's a file - open it
        xdg-open "$current_dir/$name" &>/dev/null &
        exit 0
    fi
done
