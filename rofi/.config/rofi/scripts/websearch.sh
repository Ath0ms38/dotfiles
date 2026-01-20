#!/bin/bash
# Web search with multiple engines
# Enter = select, Escape = back

SCRIPTS_DIR="$HOME/.config/rofi/scripts"
BROWSER="${BROWSER:-firefox}"

engines=(
    "  Google"
    "  DuckDuckGo"
    "  YouTube"
    "  GitHub"
    "  Reddit"
    "  Wikipedia"
    "  Arch Wiki"
    "󰏗  AUR"
)

declare -A urls=(
    ["  Google"]="https://www.google.com/search?q="
    ["  DuckDuckGo"]="https://duckduckgo.com/?q="
    ["  YouTube"]="https://www.youtube.com/results?search_query="
    ["  GitHub"]="https://github.com/search?q="
    ["  Reddit"]="https://www.reddit.com/search/?q="
    ["  Wikipedia"]="https://en.wikipedia.org/wiki/Special:Search?search="
    ["  Arch Wiki"]="https://wiki.archlinux.org/index.php?search="
    ["󰏗  AUR"]="https://aur.archlinux.org/packages?K="
)

# Select search engine
engine=$(printf '%s\n' "${engines[@]}" | rofi -dmenu -p "  Search" \
    -theme-str 'listview { lines: 8; } element { padding: 12px 16px; }')

exit_code=$?

[[ $exit_code -eq 10 || $exit_code -eq 1 ]] && exec "$SCRIPTS_DIR/main-menu.sh"
[[ -z "$engine" ]] && exit 0

# Enter search query
query=$(rofi -dmenu -p "$engine" \
    -theme-str 'listview { enabled: false; }')

query_code=$?

[[ $query_code -eq 10 || $query_code -eq 1 ]] && exec "$SCRIPTS_DIR/websearch.sh"
[[ -z "$query" ]] && exit 0

# URL encode the query
encoded_query=$(echo "$query" | sed 's/ /+/g')

# Open in new browser window
$BROWSER --new-window "${urls[$engine]}${encoded_query}" &
